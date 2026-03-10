# PreferenceView 2ステップ化 + ユーザー情報フロー再設計 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PreferenceViewを2ステップに分離し、メール登録→好み入力のフローを整理。emailMarketingConsent対応、プライバシーポリシーモーダル追加。

**Architecture:** PreferenceView内部に `step` state (1 or 2) を持ち、ステートマシン自体は変更しない。バックエンドは `customer_service.py` のGraphQLクエリにemailMarketingConsent を追加。スキップ時はcustomer登録なしでカメラへ直行。

**Tech Stack:** FastAPI, Shopify Admin GraphQL API (2026-01), Next.js 16, React 19, TypeScript, Tailwind CSS 4, Framer Motion

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/customer_service.py` | Modify | emailMarketingConsent GraphQL対応 (search/create/update) |
| `backend/routers/customers.py` | Modify | email_marketing_consent Form パラメータ追加 |
| `backend/mock_service.py` | Modify | モック対応 (email_marketing_consent フィールド追加) |
| `backend/tests/test_customers.py` | Modify | email_marketing_consent テスト追加 |
| `backend/tests/test_customer_service.py` | Modify | emailMarketingConsent GraphQLテスト追加 |
| `frontend/src/hooks/useBackendAPI.ts` | Modify | registerCustomer に emailMarketingConsent 追加 |
| `frontend/src/app/page.tsx` | Modify | emailMarketingConsent state, スキップ動線, 復元→step2遷移 |
| `frontend/src/components/operator/PreferenceView.tsx` | Rewrite | 2ステップ化, ポリシーモーダル, マーケティング同意チェック |

---

## Chunk 1: Backend — emailMarketingConsent 対応

### Task 1: customer_service.py に emailMarketingConsent 追加

**Files:**
- Modify: `backend/customer_service.py:38-56` (search query)
- Modify: `backend/customer_service.py:92-174` (create_customer)
- Modify: `backend/customer_service.py:177-252` (update_customer_preferences)

- [ ] **Step 1: search_customer_by_email に emailMarketingConsent 追加**

GraphQLクエリの `node` に追加し、レスポンスに含める:

```python
# backend/customer_service.py — search_customer_by_email 内の query 変数
query = """
query SearchCustomer($query: String!) {
  customers(first: 1, query: $query) {
    edges {
      node {
        id
        firstName
        lastName
        email
        emailMarketingConsent {
          marketingState
        }
        stylePreferences: metafield(namespace: "custom", key: "style_preferences") {
          value
        }
        bodyMeasurements: metafield(namespace: "custom", key: "body_measurements") {
          value
        }
      }
    }
  }
}
"""

# レスポンスのパース部分に追加:
email_consent = node.get("emailMarketingConsent") or {}
email_marketing = email_consent.get("marketingState") == "SUBSCRIBED"

return {
    "id": node["id"],
    "name": f"{node.get('firstName') or ''} {node.get('lastName') or ''}".strip(),
    "email": node["email"],
    "style_preferences": preferences,
    "body_measurements": body_measurements,
    "email_marketing_consent": email_marketing,
}
```

- [ ] **Step 2: create_customer に email_marketing_consent 引数追加**

```python
async def create_customer(name: str, email: str, preferences: list[str],
                          body_measurements: dict | None = None,
                          email_marketing_consent: bool = False) -> dict | None:
    # ... existing code ...

    # customer_input に emailMarketingConsent 追加
    customer_input = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "metafields": metafields,
        "emailMarketingConsent": {
            "marketingState": "SUBSCRIBED" if email_marketing_consent else "NOT_SUBSCRIBED",
            "marketingOptInLevel": "SINGLE_OPT_IN",
        },
    }

    # return dict に追加
    return {
        # ... existing fields ...
        "email_marketing_consent": email_marketing_consent,
    }
```

- [ ] **Step 3: update_customer_preferences に email_marketing_consent 引数追加**

```python
async def update_customer_preferences(customer_id: str, preferences: list[str],
                                      body_measurements: dict | None = None,
                                      email_marketing_consent: bool | None = None) -> dict | None:
    # ... existing code ...

    customer_input = {
        "id": customer_id,
        "metafields": metafields,
    }
    if email_marketing_consent is not None:
        customer_input["emailMarketingConsent"] = {
            "marketingState": "SUBSCRIBED" if email_marketing_consent else "NOT_SUBSCRIBED",
            "marketingOptInLevel": "SINGLE_OPT_IN",
        }

    # return dict に追加
    return {
        # ... existing fields ...
        "email_marketing_consent": email_marketing_consent if email_marketing_consent is not None else False,
    }
```

- [ ] **Step 4: 構文チェック**

Run: `cd backend && python3 -c "import ast; ast.parse(open('customer_service.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/customer_service.py
git commit -m "feat: add emailMarketingConsent to customer service GraphQL"
```

### Task 2: routers/customers.py に email_marketing_consent パラメータ追加

**Files:**
- Modify: `backend/routers/customers.py:40-85`

- [ ] **Step 1: POST /api/customers に email_marketing_consent パラメータ追加**

```python
@router.post("/api/customers")
async def register_customer(
    name: str = Form(...),
    email: str = Form(...),
    style_preferences: str = Form(default="[]"),
    body_measurements: str = Form(default=""),
    email_marketing_consent: str = Form(default="false"),
):
    # ... existing preferences/measurements parse ...

    # email_marketing_consent をパース
    marketing_consent = email_marketing_consent.lower() in ("true", "1", "yes")

    # mock mode の呼び出しに反映
    if is_mock_mode():
        existing = get_mock_customer(email)
        if existing:
            updated = update_mock_customer_preferences(email, preferences, measurements, marketing_consent)
            return {"status": "success", "customer": updated}
        customer = create_mock_customer(name, email, preferences, measurements, marketing_consent)
        return {"status": "success", "customer": customer}

    # 実API の呼び出しに反映
    existing = await search_customer_by_email(email)
    if existing:
        updated = await update_customer_preferences(existing["id"], preferences, measurements, marketing_consent)
        if updated:
            return {"status": "success", "customer": updated}
        return {"status": "error", "message": "Failed to update customer preferences"}

    customer = await create_customer(name, email, preferences, measurements, marketing_consent)
    if customer:
        return {"status": "success", "customer": customer}
    return {"status": "error", "message": "Failed to create customer"}
```

- [ ] **Step 2: 構文チェック**

Run: `cd backend && python3 -c "import ast; ast.parse(open('routers/customers.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/routers/customers.py
git commit -m "feat: add email_marketing_consent parameter to customers router"
```

### Task 3: mock_service.py にモック対応追加

**Files:**
- Modify: `backend/mock_service.py:101-125`

- [ ] **Step 1: モック関数の引数に body_measurements と email_marketing_consent 追加**

```python
def create_mock_customer(name: str, email: str, preferences: list[str],
                         body_measurements: dict | None = None,
                         email_marketing_consent: bool = False) -> dict:
    """モック顧客作成"""
    customer = {
        "id": f"mock-customer-{len(MOCK_CUSTOMER_DB) + 1}",
        "name": name,
        "email": email,
        "style_preferences": preferences,
        "body_measurements": body_measurements,
        "email_marketing_consent": email_marketing_consent,
        "is_new": True,
    }
    MOCK_CUSTOMER_DB[email] = customer
    return customer


def update_mock_customer_preferences(email: str, preferences: list[str],
                                     body_measurements: dict | None = None,
                                     email_marketing_consent: bool | None = None) -> dict | None:
    """モック顧客の好み更新"""
    customer = MOCK_CUSTOMER_DB.get(email)
    if customer:
        customer["style_preferences"] = preferences
        if body_measurements is not None:
            customer["body_measurements"] = body_measurements
        if email_marketing_consent is not None:
            customer["email_marketing_consent"] = email_marketing_consent
        customer["is_new"] = False
    return customer
```

- [ ] **Step 2: 構文チェック**

Run: `cd backend && python3 -c "import ast; ast.parse(open('mock_service.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/mock_service.py
git commit -m "feat: add email_marketing_consent to mock service"
```

### Task 4: バックエンドテスト追加

**Files:**
- Modify: `backend/tests/test_customers.py`
- Modify: `backend/tests/test_customer_service.py`

- [ ] **Step 1: test_customers.py に email_marketing_consent テスト追加**

```python
@pytest.mark.asyncio
async def test_create_customer_with_marketing_consent(client):
    """email_marketing_consent が保存されること"""
    res = await client.post(
        "/api/customers",
        data={
            "name": "マーケテスト",
            "email": "marketing@example.com",
            "style_preferences": json.dumps(["カジュアル"]),
            "email_marketing_consent": "true",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["email_marketing_consent"] is True


@pytest.mark.asyncio
async def test_create_customer_without_marketing_consent(client):
    """email_marketing_consent デフォルトは false"""
    res = await client.post(
        "/api/customers",
        data={
            "name": "デフォルトテスト",
            "email": "default@example.com",
            "style_preferences": "[]",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["customer"]["email_marketing_consent"] is False
```

- [ ] **Step 2: テスト実行**

Run: `docker compose exec backend pytest tests/test_customers.py -v`
Expected: All tests PASS

- [ ] **Step 3: test_customer_service.py に emailMarketingConsent GraphQL テスト追加**

```python
@pytest.mark.asyncio
async def test_search_customer_returns_marketing_consent():
    """検索結果に email_marketing_consent が含まれる"""
    mock_graphql_response = {
        "data": {
            "customers": {
                "edges": [{
                    "node": {
                        "id": "gid://shopify/Customer/999",
                        "firstName": "テスト",
                        "lastName": None,
                        "email": "consent@example.com",
                        "emailMarketingConsent": {
                            "marketingState": "SUBSCRIBED",
                        },
                        "stylePreferences": {"value": "[]"},
                        "bodyMeasurements": None,
                    }
                }]
            }
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_graphql_response
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("customer_service.token_manager") as mock_tm:
        mock_tm.get_token = AsyncMock(return_value="shpat_test")
        with patch.dict("os.environ", {"SHOPIFY_STORE_URL": "test.myshopify.com"}):
            with patch("customer_service.httpx.AsyncClient", return_value=mock_client):
                from customer_service import search_customer_by_email
                result = await search_customer_by_email("consent@example.com")

    assert result["email_marketing_consent"] is True
```

- [ ] **Step 4: テスト実行**

Run: `docker compose exec backend pytest tests/test_customer_service.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_customers.py backend/tests/test_customer_service.py
git commit -m "test: add email_marketing_consent tests"
```

---

## Chunk 2: Frontend — 2ステップ化 + ポリシーモーダル

### Task 5: useBackendAPI.ts に emailMarketingConsent 追加

**Files:**
- Modify: `frontend/src/hooks/useBackendAPI.ts:68-101`

- [ ] **Step 1: registerCustomer に emailMarketingConsent パラメータ追加**

```typescript
const registerCustomer = useCallback(async (
  userName: string,
  userEmail: string,
  selectedTags: string[],
  bodyMeasurements?: Record<string, number>,
  emailMarketingConsent?: boolean
): Promise<string | null> => {
  if (!userName.trim() || !userEmail.trim()) return null;
  const formData = new FormData();
  formData.append("name", userName);
  formData.append("email", userEmail);
  formData.append("style_preferences", JSON.stringify(selectedTags));
  if (bodyMeasurements && Object.keys(bodyMeasurements).length > 0) {
    formData.append("body_measurements", JSON.stringify(bodyMeasurements));
  }
  if (emailMarketingConsent !== undefined) {
    formData.append("email_marketing_consent", String(emailMarketingConsent));
  }
  // ... rest unchanged ...
}, []);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useBackendAPI.ts
git commit -m "feat: add emailMarketingConsent to registerCustomer API"
```

### Task 6: page.tsx にスキップ動線 + 復元→step2 + emailMarketingConsent state 追加

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: state 追加 + リセット対応**

```typescript
// 既存の bodyMeasurements の下に追加
const [emailMarketingConsent, setEmailMarketingConsent] = useState(false);
const [privacyAgreed, setPrivacyAgreed] = useState(false);

// resetApp 内に追加
setEmailMarketingConsent(false);
setPrivacyAgreed(false);
```

- [ ] **Step 2: handleLookupCustomer に emailMarketingConsent 復元追加**

`handleLookupCustomer` 内、既存の `if (cust.body_measurements)` の後に追加:

```typescript
if (cust.email_marketing_consent !== undefined) {
  setEmailMarketingConsent(cust.email_marketing_consent);
}
```

また、復元成功時にステップ2へ遷移するための返り値が必要。`handleLookupCustomer` は現在 void を返すが、復元成功時に `true` を返すように変更:

```typescript
const handleLookupCustomer = async (): Promise<boolean> => {
  if (!userEmail) return false;
  const cust = await api.lookupCustomer(userEmail);
  if (cust) {
    setCustomerId(cust.id);
    if (cust.name) setUserName(cust.name);
    if (cust.style_preferences?.length > 0) setSelectedTags(cust.style_preferences);
    if (cust.body_measurements) setBodyMeasurements(cust.body_measurements);
    if (cust.email_marketing_consent !== undefined) {
      setEmailMarketingConsent(cust.email_marketing_consent);
    }
    return true;
  }
  return false;
};
```

- [ ] **Step 3: handleProceedToCamera, handleFileUpload に emailMarketingConsent 追加**

```typescript
const handleProceedToCamera = async () => {
  const cid = await api.registerCustomer(userName, userEmail, selectedTags, bodyMeasurements, emailMarketingConsent);
  // ... rest unchanged ...
};

const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    const cid = await api.registerCustomer(userName, userEmail, selectedTags, bodyMeasurements, emailMarketingConsent);
    // ... rest unchanged ...
  }
};
```

- [ ] **Step 4: スキップハンドラー追加**

```typescript
const handleSkipToCamera = () => {
  // customer登録なし、スタイル・体型入力なしでカメラへ直行
  camera.startCamera(camera.selectedCameraId);
  changeState("CAMERA_ACTIVE");
};

const handleSkipFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (file) {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (reader.result) {
        processImageRequest(file, reader.result as string);
      }
    };
    reader.readAsDataURL(file);
  }
};
```

- [ ] **Step 5: PreferenceView の props を更新**

```tsx
<PreferenceView
  userName={userName}
  setUserName={setUserName}
  userEmail={userEmail}
  setUserEmail={setUserEmail}
  selectedTags={selectedTags}
  toggleTag={toggleTag}
  onLookupCustomer={handleLookupCustomer}
  onProceed={handleProceedToCamera}
  onSkipToCamera={handleSkipToCamera}
  onSkipFileUpload={handleSkipFileUpload}
  cameras={camera.cameras}
  selectedCameraId={camera.selectedCameraId}
  onSelectCamera={(id) => {
    camera.setSelectedCameraId(id);
    camera.startCamera(id);
  }}
  mirrorCameras={mirrorCameras}
  onSelectMirrorCamera={api.switchMirrorCamera}
  onFileUpload={handleFileUpload}
  bodyMeasurements={bodyMeasurements}
  setBodyMeasurements={setBodyMeasurements}
  emailMarketingConsent={emailMarketingConsent}
  setEmailMarketingConsent={setEmailMarketingConsent}
  privacyAgreed={privacyAgreed}
  setPrivacyAgreed={setPrivacyAgreed}
/>
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: add skip flow, email marketing consent state, lookup return value"
```

### Task 7: PreferenceView.tsx を2ステップ化 + ポリシーモーダル

**Files:**
- Rewrite: `frontend/src/components/operator/PreferenceView.tsx`

- [ ] **Step 1: PreferenceView を2ステップ構造に書き換え**

Props interface を更新:

```typescript
interface PreferenceViewProps {
  userName: string;
  setUserName: (val: string) => void;
  userEmail: string;
  setUserEmail: (val: string) => void;
  selectedTags: string[];
  toggleTag: (tag: string) => void;
  onLookupCustomer: () => Promise<boolean>;
  onProceed: () => void;
  onSkipToCamera: () => void;
  onSkipFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  // カメラ設定
  cameras: MediaDeviceInfo[];
  selectedCameraId: string;
  onSelectCamera: (deviceId: string) => void;
  mirrorCameras: any[];
  onSelectMirrorCamera: (index: number) => void;
  // ファイルアップロード
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  // 体型情報
  bodyMeasurements: Record<string, number>;
  setBodyMeasurements: (val: Record<string, number>) => void;
  // 同意・マーケティング
  emailMarketingConsent: boolean;
  setEmailMarketingConsent: (val: boolean) => void;
  privacyAgreed: boolean;
  setPrivacyAgreed: (val: boolean) => void;
}
```

コンポーネント内部に `step` state と `showPolicyModal` state を追加:

```typescript
const [step, setStep] = useState(1);
const [showPolicyModal, setShowPolicyModal] = useState(false);

const canProceedToStep2 = userName.trim() !== "" && userEmail.trim() !== "" && privacyAgreed;

const handleLookup = async () => {
  const found = await onLookupCustomer();
  if (found) setStep(2);
};
```

- [ ] **Step 2: ステップ1のUI実装**

ステップ1: 名前、メール、復元ボタン、マーケティング同意チェック、ポリシー同意チェック、「次へ」ボタン、「スキップして撮影」ボタン。

ステップ1には `{step === 1 && ( ... )}` で囲む。

```tsx
{step === 1 && (
  <>
    {/* お客様情報 */}
    <div className="space-y-4">
      <h3>...</h3>
      {/* 名前 + メール + 復元ボタン（既存UIを再利用） */}
    </div>

    {/* 同意チェックボックス */}
    <div className="space-y-3">
      <label className="flex items-start gap-3 cursor-pointer">
        <input type="checkbox" checked={emailMarketingConsent}
          onChange={(e) => setEmailMarketingConsent(e.target.checked)}
          className="mt-1 w-4 h-4 ..." />
        <span className="text-sm text-slate-300">新着・セール情報をメールで受け取る</span>
      </label>
      <label className="flex items-start gap-3 cursor-pointer">
        <input type="checkbox" checked={privacyAgreed}
          onChange={(e) => setPrivacyAgreed(e.target.checked)}
          className="mt-1 w-4 h-4 ..." />
        <span className="text-sm text-slate-300">
          <button type="button" onClick={() => setShowPolicyModal(true)}
            className="text-emerald-400 underline">個人情報の取り扱いについて</button>
          に同意する
        </span>
      </label>
    </div>

    {/* ボタン */}
    <div className="flex flex-col sm:flex-row gap-4 pt-4">
      <button onClick={() => setStep(2)} disabled={!canProceedToStep2}
        className="flex-1 ... disabled:opacity-40 disabled:cursor-not-allowed">
        次へ
      </button>
      <button onClick={onSkipToCamera}
        className="flex-1 ... border-2 border-slate-700">
        スキップして撮影へ
      </button>
    </div>
  </>
)}
```

- [ ] **Step 3: ステップ2のUI実装**

ステップ2: スタイルタグ、体型入力、カメラ設定、「カメラで撮影に進む」「画像をアップロード」ボタン。既存UIをそのまま `{step === 2 && ( ... )}` で囲む。

- [ ] **Step 4: プライバシーポリシーモーダル実装**

```tsx
{showPolicyModal && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    onClick={() => setShowPolicyModal(false)}>
    <div className="bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 sm:p-8 border border-slate-700"
      onClick={(e) => e.stopPropagation()}>
      <h2 className="text-xl font-bold text-slate-100 mb-4">プライバシーポリシー</h2>
      <div className="text-sm text-slate-300 space-y-4 leading-relaxed">
        {/* ポリシー全文をハードコード — shop.85-store.com/policies/privacy-policy の内容 */}
        <p>最終更新日：2025年12月5日</p>
        <p>85-store は、この店舗およびウェブサイト...</p>
        {/* ... 全文 ... */}
      </div>
      <button onClick={() => setShowPolicyModal(false)}
        className="mt-6 w-full px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-bold">
        閉じる
      </button>
    </div>
  </div>
)}
```

ポリシー全文は長いので、コンポーネント外に `PRIVACY_POLICY_SECTIONS` 定数として定義し、`.map()` でレンダリングする。各セクションは `{title, content}` のオブジェクト配列。

- [ ] **Step 5: TypeScript 型チェック**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/operator/PreferenceView.tsx
git commit -m "feat: redesign PreferenceView with 2-step flow, privacy modal, marketing consent"
```

### Task 8: ビルド検証 + 全テスト

- [ ] **Step 1: Docker ビルド**

Run: `docker compose build`
Expected: Both images build successfully

- [ ] **Step 2: バックエンドテスト**

Run: `docker compose up -d && sleep 10 && docker compose exec backend pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: TypeScript 型チェック**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit (全体統合)**

全ファイルがコミット済みであることを確認。未コミットがあれば追加コミット。
