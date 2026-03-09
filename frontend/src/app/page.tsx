"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Camera, Check, RefreshCcw, Sparkles, Upload, User, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// スタイルタグの定義
const STYLE_TAGS = {
  テイスト: ["かっこいい", "かわいい", "きれいめ", "ナチュラル", "個性的"],
  スタイル: ["ストリート", "アメカジ", "モード", "ヴィンテージ", "カジュアル", "スポーティ"],
  年代感: ["70s", "80s", "90s", "Y2K", "ミリタリー"],
};

// アプリのメイン状態管理
type AppState = "IDLE" | "PREFERENCE" | "CAMERA_ACTIVE" | "ANALYZING" | "RESULT";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("IDLE");
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  // APIレスポンス用のステート
  const [recommendation, setRecommendation] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 顧客・好み用のステート
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customerId, setCustomerId] = useState<string>("");
  const [customerLoading, setCustomerLoading] = useState(false);
  const [customerMessage, setCustomerMessage] = useState<string | null>(null);

  // 音声合成用の関数
  const speakText = useCallback((text: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const msg = new SpeechSynthesisUtterance(text);
      msg.lang = "ja-JP";
      msg.rate = 1.1;
      msg.pitch = 1.2;
      window.speechSynthesis.speak(msg);
    }
  }, []);

  // タグのトグル
  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  // 既存顧客の好みを復元
  const lookupCustomer = async () => {
    if (!userEmail.trim()) return;
    setCustomerLoading(true);
    setCustomerMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/customers?email=${encodeURIComponent(userEmail)}`);
      const data = await res.json();
      if (data.status === "success" && data.customer) {
        setCustomerId(data.customer.id);
        setUserName(data.customer.name || userName);
        if (data.customer.style_preferences?.length > 0) {
          setSelectedTags(data.customer.style_preferences);
        }
        setCustomerMessage("前回の好みを復元しました！");
      } else {
        setCustomerMessage("初めてのご来店ですね。好みを選んでください。");
      }
    } catch {
      setCustomerMessage("検索に失敗しました。そのまま好みを選んでください。");
    } finally {
      setCustomerLoading(false);
    }
  };

  // 顧客登録してカメラへ遷移
  const registerAndProceed = async () => {
    // 顧客情報をバックエンドに保存
    if (userName.trim() && userEmail.trim()) {
      try {
        const formData = new FormData();
        formData.append("name", userName);
        formData.append("email", userEmail);
        formData.append("style_preferences", JSON.stringify(selectedTags));
        const res = await fetch(`${API_URL}/api/customers`, {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.status === "success" && data.customer) {
          setCustomerId(data.customer.id);
        }
      } catch (err) {
        console.error("Customer registration error:", err);
      }
    }
    startCamera();
  };

  // カメラの起動処理
  const startCamera = async () => {
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setAppState("CAMERA_ACTIVE");
    } catch (err) {
      console.error("Camera error:", err);
      setErrorMsg("カメラへのアクセスが拒否されたか、デバイスが見つかりません。画像アップロードをお試しください。");
      setAppState("PREFERENCE");
    }
  };

  // カメラの停止処理
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // 画像をAPIに送信する共通処理
  const sendImageToAPI = async (imageBlob: Blob, previewUrl: string) => {
    setCapturedImage(previewUrl);
    stopCamera();
    setAppState("ANALYZING");

    const formData = new FormData();
    formData.append("file", imageBlob, "capture.jpg");
    formData.append("preferences", JSON.stringify(selectedTags));
    if (customerId) {
      formData.append("customer_id", customerId);
    }

    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }

      const resData = await res.json();

      if (resData.status === "success") {
        setRecommendation(resData.data);
        setAppState("RESULT");
        if (resData.data.analyzed_outfit) {
          speakText(resData.data.analyzed_outfit);
        }
      } else {
        throw new Error(resData.message || "Unknown error occurred");
      }
    } catch (err: any) {
      console.error("Analysis Error:", err);
      setErrorMsg(`解析中にエラーが発生しました: ${err.message}`);
      setAppState("PREFERENCE");
    }
  };

  // カメラ撮影→API送信
  const captureAndAnalyze = async () => {
    if (!videoRef.current) return;

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    const imageBlob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.8);
    });

    if (!imageBlob) {
      setErrorMsg("画像の生成に失敗しました。");
      return;
    }

    const imageUrl = URL.createObjectURL(imageBlob);
    await sendImageToAPI(imageBlob, imageUrl);
  };

  // ファイルアップロード→API送信
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    await sendImageToAPI(file, imageUrl);
  };

  // 最初に戻る処理
  const resetApp = () => {
    stopCamera();
    setCapturedImage(null);
    setRecommendation(null);
    setErrorMsg(null);
    setCustomerMessage(null);
    setAppState("IDLE");
    if (typeof window !== "undefined") {
      window.speechSynthesis.cancel();
    }
  };

  // クリーンアップ
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <main className="min-h-screen bg-slate-900 text-slate-50 flex flex-col items-center justify-center p-4 sm:p-8 font-sans overflow-hidden">
      {/* 共通のヘッダーロゴ */}
      <div className="absolute top-8 left-8 flex items-center space-x-2 text-2xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
        <Sparkles className="w-8 h-8 text-emerald-400" />
        <span>VINTAGE.AI</span>
      </div>

      <AnimatePresence mode="wait">
        {/* --- 待機・スタート画面 --- */}
        {appState === "IDLE" && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center max-w-lg text-center space-y-8"
          >
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
                あなたに最適な一点モノを
                <span className="block text-emerald-400">AIが見つけます</span>
              </h1>
              <p className="text-lg text-slate-400">
                いま着ている服をスキャンして、
                <br />
                お店の中から相性ピッタリの古着を提案します。
              </p>
            </div>

            {errorMsg && (
              <div className="bg-red-500/20 text-red-300 px-4 py-3 rounded-lg border border-red-500/30 text-sm">
                {errorMsg}
              </div>
            )}

            <button
              onClick={() => setAppState("PREFERENCE")}
              className="group relative px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-full text-xl font-bold transition-all transform hover:scale-105 hover:shadow-[0_0_40px_rgba(16,185,129,0.4)] flex items-center space-x-3 overflow-hidden"
            >
              <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              <Sparkles className="w-6 h-6 relative z-10" />
              <span className="relative z-10">AIスタイリストを呼ぶ</span>
            </button>
          </motion.div>
        )}

        {/* --- 好み入力画面 --- */}
        {appState === "PREFERENCE" && (
          <motion.div
            key="preference"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center w-full max-w-2xl space-y-6"
          >
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-bold">あなたの好みを教えてください</h2>
              <p className="text-slate-400">好みに合わせてAIが提案をカスタマイズします</p>
            </div>

            {/* 顧客情報入力 */}
            <div className="w-full bg-slate-800/60 rounded-2xl p-6 border border-slate-700 space-y-4">
              <div className="flex items-center space-x-2 text-slate-300 mb-2">
                <User className="w-5 h-5" />
                <span className="font-medium">お客様情報</span>
                <span className="text-xs text-slate-500">（任意）</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="お名前"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                />
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="メールアドレス"
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    className="flex-1 px-4 py-3 bg-slate-900 border border-slate-600 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                  <button
                    onClick={lookupCustomer}
                    disabled={customerLoading || !userEmail.trim()}
                    className="px-4 py-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 rounded-xl text-sm font-medium transition-colors flex items-center gap-1 whitespace-nowrap"
                  >
                    <Search className="w-4 h-4" />
                    復元
                  </button>
                </div>
              </div>
              {customerMessage && (
                <p className="text-sm text-emerald-400">{customerMessage}</p>
              )}
            </div>

            {/* スタイルタグ選択 */}
            <div className="w-full bg-slate-800/60 rounded-2xl p-6 border border-slate-700 space-y-5">
              {Object.entries(STYLE_TAGS).map(([category, tags]) => (
                <div key={category}>
                  <p className="text-sm text-slate-400 mb-2 font-medium">{category}</p>
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <button
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                          selectedTags.includes(tag)
                            ? "bg-emerald-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)]"
                            : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                        }`}
                      >
                        {selectedTags.includes(tag) && <Check className="w-3 h-3 inline mr-1" />}
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {errorMsg && (
              <div className="bg-red-500/20 text-red-300 px-4 py-3 rounded-lg border border-red-500/30 text-sm w-full">
                {errorMsg}
              </div>
            )}

            {/* アクションボタン */}
            <div className="flex flex-col sm:flex-row gap-4 w-full">
              <button
                onClick={registerAndProceed}
                className="flex-1 group relative px-6 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-full text-lg font-bold transition-all transform hover:scale-105 flex items-center justify-center space-x-3 overflow-hidden"
              >
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                <Camera className="w-5 h-5 relative z-10" />
                <span className="relative z-10">カメラで撮影する</span>
              </button>

              <button
                onClick={() => {
                  // 顧客登録してからファイル選択
                  if (userName.trim() && userEmail.trim()) {
                    const formData = new FormData();
                    formData.append("name", userName);
                    formData.append("email", userEmail);
                    formData.append("style_preferences", JSON.stringify(selectedTags));
                    fetch(`${API_URL}/api/customers`, { method: "POST", body: formData }).catch(() => {});
                  }
                  fileInputRef.current?.click();
                }}
                className="flex-1 px-6 py-4 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-full text-lg font-bold transition-all flex items-center justify-center space-x-3"
              >
                <Upload className="w-5 h-5" />
                <span>画像をアップロード</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>

            <button
              onClick={resetApp}
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
            >
              戻る
            </button>
          </motion.div>
        )}

        {/* --- カメラ撮影画面 --- */}
        {appState === "CAMERA_ACTIVE" && (
          <motion.div
            key="camera"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            className="flex flex-col items-center w-full max-w-3xl space-y-6"
          >
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">全身・またはトップスが映るように立ってください</h2>
              <p className="text-slate-400">準備ができたら撮影ボタンを押します</p>
              {selectedTags.length > 0 && (
                <div className="flex flex-wrap justify-center gap-1.5 pt-2">
                  {selectedTags.map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full text-xs border border-emerald-500/30">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="relative w-full aspect-[4/3] sm:aspect-video rounded-3xl overflow-hidden bg-slate-800 border-4 border-slate-700 shadow-2xl">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover -scale-x-100"
              />
              {/* ガイド枠 */}
              <div className="absolute inset-0 border-2 border-emerald-500/50 m-8 sm:m-16 rounded-2xl pointer-events-none border-dashed" />
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => { stopCamera(); setAppState("PREFERENCE"); }}
                className="p-4 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                戻る
              </button>

              <button
                onClick={captureAndAnalyze}
                className="w-20 h-20 bg-emerald-500 rounded-full flex items-center justify-center border-4 border-emerald-900 hover:bg-emerald-400 hover:scale-105 transition-all shadow-[0_0_20px_rgba(16,185,129,0.5)]"
              >
                <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 rounded-full bg-red-500 animate-pulse" />
                </div>
              </button>
            </div>
          </motion.div>
        )}

        {/* --- 解析中（ローディング）画面 --- */}
        {appState === "ANALYZING" && (
          <motion.div
            key="analyzing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center space-y-12 py-20"
          >
            {capturedImage && (
              <div className="relative w-48 h-64 sm:w-64 sm:h-80 rounded-2xl overflow-hidden opacity-50 shadow-2xl">
                <img src={capturedImage} alt="Captured" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent" />
                {/* スキャン演出 */}
                <motion.div
                  initial={{ top: "-10%" }}
                  animate={{ top: "110%" }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="absolute left-0 right-0 h-1 bg-emerald-400 shadow-[0_0_20px_rgba(16,185,129,1)] z-10"
                />
              </div>
            )}

            <div className="text-center space-y-4">
              <div className="flex items-center justify-center space-x-3">
                <Sparkles className="w-8 h-8 text-cyan-400 animate-spin-slow" />
                <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
                  AIがコーディネートを考案中...
                </h2>
              </div>
              <p className="text-slate-400">
                あなたの服の特徴を分析し、お店の在庫から最適なアイテムを探しています
              </p>
              {selectedTags.length > 0 && (
                <p className="text-emerald-400/70 text-sm">
                  好み: {selectedTags.join("・")}
                </p>
              )}
            </div>
          </motion.div>
        )}

        {/* --- 結果提案画面 --- */}
        {appState === "RESULT" && recommendation && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="w-full max-w-7xl flex flex-col items-center gap-8 lg:gap-12"
          >
            {/* 上部: AIの分析結果とスキャン画像 */}
            <div className="w-full bg-slate-800/80 rounded-3xl p-6 sm:p-8 border border-slate-700 backdrop-blur-md relative overflow-hidden flex flex-col md:flex-row gap-8 items-start flex-wrap">
              <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-cyan-400 to-emerald-400" />

              {/* マスク付き画像表示領域 */}
              {capturedImage && (
                <div className="relative flex-shrink-0 w-auto">
                  <div className="relative rounded-xl overflow-hidden shadow-2xl border-4 border-slate-700 bg-slate-900 mx-auto" style={{ maxWidth: "240px" }}>
                    <img src={capturedImage} className="w-full object-contain block opacity-90" alt="Captured" />
                    {/* AIが認識した服のバウンディングボックス */}
                    {recommendation.box_ymin !== undefined && recommendation.box_ymax !== 1000 && (
                      <div
                        className="absolute border-[3px] border-emerald-400 bg-emerald-400/20 shadow-[0_0_15px_rgba(16,185,129,0.5)] flex items-center justify-center pointer-events-none"
                        style={{
                          top: `${(recommendation.box_ymin / 1000) * 100}%`,
                          left: `${(recommendation.box_xmin / 1000) * 100}%`,
                          height: `${((recommendation.box_ymax - recommendation.box_ymin) / 1000) * 100}%`,
                          width: `${((recommendation.box_xmax - recommendation.box_xmin) / 1000) * 100}%`,
                        }}
                      >
                        <div className="bg-emerald-500 text-white text-[10px] sm:text-xs font-bold px-1.5 py-0.5 rounded-br-lg absolute top-0 left-0">
                          Target
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 解析結果 */}
              <div className="flex-1 space-y-4">
                <div className="flex items-center space-x-3 text-cyan-400">
                  <Sparkles className="w-6 h-6" />
                  <h3 className="text-xl font-bold">スタイリング分析結果</h3>
                </div>
                <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-700 text-slate-300">
                  <p className="text-lg leading-relaxed">{recommendation.analyzed_outfit}</p>
                </div>
                {/* 推測されたスタイルタグ */}
                {recommendation.detected_style?.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs text-slate-500">検出スタイル:</span>
                    {recommendation.detected_style.map((s: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded-full text-xs border border-cyan-500/30">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
                {/* 選択した好みタグ */}
                {selectedTags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs text-slate-500">あなたの好み:</span>
                    {selectedTags.map((tag, i) => (
                      <span key={i} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full text-xs border border-emerald-500/30">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 下部: 各パターンの提案と商品リスト */}
            <div className="w-full space-y-8">
              <h3 className="text-2xl font-bold flex items-center">
                <span className="bg-emerald-500 w-3 h-8 rounded-full mr-3 inline-block" />
                おすすめのコーディネート ({recommendation.recommendations?.length || 0}パターン)
              </h3>

              <div className="grid gap-8 lg:grid-cols-3">
                {recommendation.recommendations?.map((rec: any, idx: number) => (
                  <div key={idx} className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6 flex flex-col items-center">
                    <div className="w-full space-y-3 mb-6">
                      <h4 className="text-xl font-bold text-emerald-400 border-b border-emerald-500/30 pb-2">{rec.title}</h4>
                      <p className="text-slate-300 text-sm leading-relaxed">{rec.reason}</p>
                      <div className="flex flex-wrap gap-2 pt-2">
                        {rec.search_keywords?.map((kw: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-slate-900 border border-emerald-500/30 text-emerald-300 rounded-md text-xs font-medium">
                            #{kw}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="w-full flex-1 flex flex-col gap-4">
                      {rec.shopify_products?.length > 0 ? (
                        rec.shopify_products.slice(0, 2).map((product: any) => (
                          <div key={product.id} className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700 hover:border-emerald-500/50 transition-colors group flex items-start gap-4 p-3">
                            <div className="w-20 h-20 flex-shrink-0 relative rounded-lg overflow-hidden bg-slate-800">
                              {product.image_url ? (
                                <img src={product.image_url} alt={product.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                              ) : (
                                <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-xs">No Image</div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h5 className="font-bold text-sm text-slate-200 line-clamp-2" title={product.title}>{product.title}</h5>
                              <p className="text-emerald-400 font-bold mt-1 text-sm">{product.price}</p>
                              <a
                                href={product.url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-2 inline-block px-3 py-1 bg-slate-700 hover:bg-slate-600 text-xs text-white rounded font-medium transition-colors"
                              >
                                詳細
                              </a>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="bg-slate-900/50 border border-slate-700 border-dashed rounded-xl p-6 flex items-center justify-center h-full text-center text-slate-500 text-sm">
                          <div>
                            このパターンの該当商品が
                            <br />
                            店舗にありません
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 pb-12 w-full text-center">
              <button
                onClick={resetApp}
                className="inline-flex py-4 px-12 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full text-lg sm:text-xl font-bold items-center justify-center space-x-2 transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(16,185,129,0.4)]"
              >
                <RefreshCcw className="w-6 h-6" />
                <span>最初からやり直す</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
