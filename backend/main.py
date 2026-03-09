from fastapi import FastAPI, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os
import json
import asyncio
from gemini_service import analyze_image_and_get_tags
from shopify_service import search_products_on_shopify
from mirror_service import mirror, list_cameras
from customer_service import (
    search_customer_by_email,
    create_customer,
    update_customer_preferences,
)
from mock_service import (
    get_mock_analysis,
    get_mock_customer,
    create_mock_customer,
    update_mock_customer_preferences,
)

load_dotenv()

app = FastAPI(title="Vintage AI Shop Assistant API")

# フロントエンドからのAPIアクセスを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_mock_mode() -> bool:
    return os.getenv("MOCK_MODE", "false").lower() == "true"


# --- プロジェクション状態同期マネージャー ---


class ProjectionManager:
    """iPad (タッチUI) → Backend → プロジェクション画面の状態中継"""

    def __init__(self):
        self.displays: list[WebSocket] = []
        self._current_state: dict | None = None
        self._mirror_task: asyncio.Task | None = None
        self._mirror_active = False

    async def connect_display(self, ws: WebSocket):
        await ws.accept()
        self.displays.append(ws)
        if self._current_state:
            await ws.send_json(self._current_state)

    def disconnect_display(self, ws: WebSocket):
        if ws in self.displays:
            self.displays.remove(ws)
        if not self.displays and self._mirror_active:
            self._stop_mirror()

    async def handle_message(self, data: dict):
        msg_type = data.get("type")
        if msg_type == "STATE_CHANGE":
            self._current_state = data
            await self._broadcast_json(data)
            state = data.get("state", "")
            if state in ("CAMERA_ACTIVE", "ANALYZING"):
                if not self._mirror_active and self.displays:
                    self._start_mirror()
            else:
                if self._mirror_active:
                    self._stop_mirror()
        elif msg_type == "FLASH":
            await self._broadcast_json(data)

    async def _broadcast_json(self, data: dict):
        dead: list[WebSocket] = []
        for ws in self.displays:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.displays.remove(ws)

    async def _broadcast_text(self, text: str):
        dead: list[WebSocket] = []
        for ws in self.displays:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.displays.remove(ws)

    def _start_mirror(self):
        if is_mock_mode():
            return
        if not mirror.start():
            return
        self._mirror_active = True
        self._mirror_task = asyncio.create_task(self._stream_mirror_loop())

    def _stop_mirror(self):
        self._mirror_active = False
        if self._mirror_task:
            self._mirror_task.cancel()
            self._mirror_task = None
        mirror.stop()

    async def _stream_mirror_loop(self):
        try:
            async for frame_data in mirror.stream_frames():
                if not self._mirror_active:
                    break
                if self.displays:
                    await self._broadcast_text(frame_data)
        except asyncio.CancelledError:
            pass
        finally:
            self._mirror_active = False


projection_mgr = ProjectionManager()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Vintage AI Shop Assistant API"}


@app.get("/api/health")
def health_check():
    """ヘルスチェック: 各外部APIの設定状況を返す"""
    return {
        "status": "ok",
        "mock_mode": is_mock_mode(),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "shopify_storefront_configured": bool(os.getenv("SHOPIFY_STORE_URL"))
        and bool(os.getenv("SHOPIFY_STOREFRONT_ACCESS_TOKEN")),
        "shopify_admin_configured": bool(os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")),
    }


@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    preferences: str = Form(default="[]"),
    customer_id: str = Form(default=""),
):
    """
    アップロードされた画像とユーザーの好みタグを受け取り、
    Geminiを通してShopify検索タグを生成し、商品を検索する
    """
    # 好みタグをパース
    try:
        user_preferences = json.loads(preferences)
        if not isinstance(user_preferences, list):
            user_preferences = []
    except json.JSONDecodeError:
        user_preferences = []

    image_bytes = await file.read()

    # モックモード
    if is_mock_mode():
        result_dict = get_mock_analysis(user_preferences)
        return {"status": "success", "data": result_dict}

    # 実API呼び出し
    json_str_response = analyze_image_and_get_tags(image_bytes, user_preferences)

    try:
        result_dict = json.loads(json_str_response)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "AI解析結果の読み取りに失敗しました。もう一度お試しください。",
        }

    # Geminiがエラーを返した場合
    if result_dict.get("_error"):
        result_dict.pop("_error", None)
        return {"status": "error", "message": result_dict.get("analyzed_outfit", "AI解析中にエラーが発生しました")}

    # Shopifyで商品を検索（複数の提案パターンごとに実行）
    # 部分成功: Shopify検索が失敗しても解析結果は返す
    shopify_errors = []
    recommendations = result_dict.get("recommendations", [])
    for rec in recommendations:
        keywords = rec.get("search_keywords", [])
        if keywords:
            try:
                shopify_res = search_products_on_shopify(keywords)
                rec["shopify_products"] = shopify_res.get("products", [])
                if shopify_res.get("status") == "error":
                    shopify_errors.append(rec.get("title", "不明"))
            except Exception as e:
                print(f"Shopify search error for {keywords}: {e}")
                rec["shopify_products"] = []
                shopify_errors.append(rec.get("title", "不明"))
        else:
            rec["shopify_products"] = []

    response = {"status": "success", "data": result_dict}
    if shopify_errors:
        response["warning"] = f"一部の商品検索に失敗しました: {', '.join(shopify_errors)}"
    return response


@app.get("/api/customers")
async def lookup_customer(email: str = Query(...)):
    """
    メールアドレスで既存顧客を検索し、保存済みの好みタグを返す
    """
    if is_mock_mode():
        customer = get_mock_customer(email)
        if customer:
            return {"status": "success", "customer": customer}
        return {"status": "not_found", "customer": None}

    customer = search_customer_by_email(email)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "not_found", "customer": None}


@app.post("/api/customers")
async def register_customer(
    name: str = Form(...),
    email: str = Form(...),
    style_preferences: str = Form(default="[]"),
):
    """
    顧客を登録（または既存顧客の好みを更新）し、好みタグをShopifyに保存する
    """
    try:
        preferences = json.loads(style_preferences)
        if not isinstance(preferences, list):
            preferences = []
    except json.JSONDecodeError:
        preferences = []

    if is_mock_mode():
        existing = get_mock_customer(email)
        if existing:
            updated = update_mock_customer_preferences(email, preferences)
            return {"status": "success", "customer": updated}
        customer = create_mock_customer(name, email, preferences)
        return {"status": "success", "customer": customer}

    # 既存顧客を検索
    existing = search_customer_by_email(email)
    if existing:
        # 好みを更新
        updated = update_customer_preferences(existing["id"], preferences)
        if updated:
            return {"status": "success", "customer": updated}
        return {"status": "error", "message": "Failed to update customer preferences"}

    # 新規作成
    customer = create_customer(name, email, preferences)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "error", "message": "Failed to create customer"}


# --- ミラーカメラ（リアルタイム人物切り抜き） ---


@app.get("/api/mirror/cameras")
async def get_mirror_cameras():
    """利用可能なミラーカメラの一覧と現在の選択を返す"""
    if is_mock_mode():
        return {"status": "ok", "cameras": [], "current": 0}
    cameras = list_cameras()
    return {"status": "ok", "cameras": cameras, "current": mirror.camera_index}


@app.post("/api/mirror/cameras/{index}")
async def set_mirror_camera(index: int):
    """ミラーカメラを切り替える"""
    if is_mock_mode():
        return {"status": "ok", "message": "Mock mode: mirror not available"}
    ok = mirror.set_camera(index)
    if ok:
        return {"status": "ok", "current": mirror.camera_index}
    return {"status": "error", "message": f"Camera {index} could not be opened"}


@app.post("/api/mirror/start")
async def start_mirror():
    """ミラーカメラを起動"""
    if is_mock_mode():
        return {"status": "ok", "message": "Mock mode: mirror not available"}
    ok = mirror.start()
    if ok:
        return {"status": "ok"}
    return {"status": "error", "message": "Camera could not be opened"}


@app.post("/api/mirror/stop")
async def stop_mirror():
    """ミラーカメラを停止"""
    mirror.stop()
    return {"status": "ok"}


@app.websocket("/ws/mirror")
async def mirror_ws(websocket: WebSocket):
    """
    ミラーカメラのリアルタイム切り抜きフレームを配信するWebSocket。
    接続時に自動でカメラを起動し、切断時に停止する。
    クライアントにはbase64エンコードされたPNG(透過)を送信。
    """
    await websocket.accept()

    if is_mock_mode():
        await websocket.send_json({"type": "error", "message": "Mock mode: mirror not available"})
        await websocket.close()
        return

    if not mirror.start():
        await websocket.send_json({"type": "error", "message": "Camera could not be opened"})
        await websocket.close()
        return

    try:
        async for frame_data in mirror.stream_frames():
            await websocket.send_text(frame_data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Mirror WebSocket error: {e}")
    finally:
        mirror.stop()


# --- プロジェクション状態同期 WebSocket ---


@app.websocket("/ws/projection/control")
async def projection_control_ws(websocket: WebSocket):
    """iPad (タッチUI) から状態変更・フラッシュ指示を受信"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await projection_mgr.handle_message(data)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/projection/display")
async def projection_display_ws(websocket: WebSocket):
    """プロジェクション表示画面にイベント(状態・フラッシュ・ミラーフレーム)を配信"""
    await projection_mgr.connect_display(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "REQUEST_STATE" and projection_mgr._current_state:
                await websocket.send_json(projection_mgr._current_state)
    except WebSocketDisconnect:
        pass
    finally:
        projection_mgr.disconnect_display(websocket)
