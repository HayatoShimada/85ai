"""
Shopify Admin API トークン管理
Client Credentials Grant でトークンを自動取得・更新する
(トークンは24時間で失効するため、期限前に自動更新)
"""

import os
import time
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)


class ShopifyTokenManager:
    """Admin APIトークンの自動更新を管理するシングルトン"""

    def __init__(self):
        self._token: str | None = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str | None:
        """有効なAdmin APIトークンを返す。期限切れなら自動更新する。"""
        # 期限の5分前に更新（余裕を持たせる）
        if self._token and time.time() < self._expires_at - 300:
            return self._token

        async with self._lock:
            # ダブルチェック（別タスクが既に更新した場合）
            if self._token and time.time() < self._expires_at - 300:
                return self._token
            return await self._refresh()

    async def _refresh(self) -> str | None:
        """Client Credentials Grantでトークンを再取得する"""
        store_url = os.getenv("SHOPIFY_STORE_URL")
        client_id = os.getenv("SHOPIFY_CLIENT_ID")
        client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")

        if not all([store_url, client_id, client_secret]):
            # フォールバック: 静的トークン（.envに直接指定されている場合）
            static_token = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
            if static_token and static_token.startswith("shpat_"):
                self._token = static_token
                self._expires_at = time.time() + 86000
                return self._token
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://{store_url}/admin/oauth/access_token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "client_credentials",
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

            self._token = data["access_token"]
            self._expires_at = time.time() + data.get("expires_in", 86399)
            logger.info(f"Shopify Admin API token refreshed (expires in {data.get('expires_in', '?')}s)")
            return self._token

        except Exception as e:
            logger.error(f"Failed to refresh Shopify Admin API token: {e}")
            # 期限切れトークンはクリア（期限内なら保持）
            if self._token and time.time() >= self._expires_at:
                self._token = None
                self._expires_at = 0
            return self._token


# シングルトンインスタンス
token_manager = ShopifyTokenManager()
