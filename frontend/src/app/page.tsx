"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Camera, Check, RefreshCcw, Sparkles, Volume2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// アプリのメイン状態管理
type AppState = "IDLE" | "CAMERA_ACTIVE" | "ANALYZING" | "RESULT";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("IDLE");
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  // APIレスポンス用のステート
  const [recommendation, setRecommendation] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 音声合成用の関数
  const speakText = useCallback((text: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // 既存の音声をキャンセル
      const msg = new SpeechSynthesisUtterance(text);
      msg.lang = "ja-JP";
      msg.rate = 1.1; // 少し早め
      msg.pitch = 1.2; // 少し高め（明るく）
      window.speechSynthesis.speak(msg);
    }
  }, []);

  // カメラの起動処理
  const startCamera = async () => {
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false // 今回は映像のみで音声(マイク)入力は簡易化のため省略。または後で追加
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setAppState("CAMERA_ACTIVE");
    } catch (err) {
      console.error("Camera error:", err);
      setErrorMsg("カメラへのアクセスが拒否されたか、デバイスが見つかりません。");
      setAppState("IDLE");
    }
  };

  // カメラの停止処理
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // 撮影とAPI送信処理
  const captureAndAnalyze = async () => {
    if (!videoRef.current) return;

    // Canvasにビデオの現在のフレームを描画
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // 画像をBlobに変換
    const imageBlob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.8);
    });

    if (!imageBlob) {
      setErrorMsg("画像の生成に失敗しました。");
      return;
    }

    // 画像のプレビュー用URLを作成してセット
    const imageUrl = URL.createObjectURL(imageBlob);
    setCapturedImage(imageUrl);

    // カメラを止めて解析中ステータスへ
    stopCamera();
    setAppState("ANALYZING");

    // バックエンドへ送信
    const formData = new FormData();
    formData.append("file", imageBlob, "capture.jpg");

    try {
      // ローカルのFastAPIに送信（ポート8000前提）
      const res = await fetch("http://localhost:8000/api/analyze", {
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
        // AIのコメントを読み上げ
        if (resData.data.reason) {
          speakText(resData.data.reason);
        }
      } else {
        throw new Error(resData.message || "Unknown error occurred");
      }
    } catch (err: any) {
      console.error("Analysis Error:", err);
      setErrorMsg(`解析中にエラーが発生しました: ${err.message}`);
      setAppState("IDLE");
    }
  };

  // 最初に戻る処理
  const resetApp = () => {
    stopCamera();
    setCapturedImage(null);
    setRecommendation(null);
    setErrorMsg(null);
    setAppState("IDLE");
    window.speechSynthesis.cancel();
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
                いま着ている服をスキャンして、<br />
                お店の中から相性ピッタリの古着を提案します。
              </p>
            </div>

            {errorMsg && (
              <div className="bg-red-500/20 text-red-300 px-4 py-3 rounded-lg border border-red-500/30 text-sm">
                {errorMsg}
              </div>
            )}

            <button
              onClick={startCamera}
              className="group relative px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-full text-xl font-bold transition-all transform hover:scale-105 hover:shadow-[0_0_40px_rgba(16,185,129,0.4)] flex items-center space-x-3 overflow-hidden"
            >
              <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              <Camera className="w-6 h-6 relative z-10" />
              <span className="relative z-10">AIスタイリストを呼ぶ</span>
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
            </div>

            <div className="relative w-full aspect-[4/3] sm:aspect-video rounded-3xl overflow-hidden bg-slate-800 border-4 border-slate-700 shadow-2xl">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover -scale-x-100" // 鏡面表示
              />

              {/* ガイド枠 */}
              <div className="absolute inset-0 border-2 border-emerald-500/50 m-8 sm:m-16 rounded-2xl pointer-events-none border-dashed" />
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={resetApp}
                className="p-4 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                キャンセル
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
            className="w-full max-w-6xl grid md:grid-cols-2 gap-8 lg:gap-12 items-start"
          >
            {/* 左側: AIコメントとスキャン画像 */}
            <div className="space-y-6">
              <div className="bg-slate-800/50 rounded-3xl p-6 sm:p-8 border border-slate-700 backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-emerald-400 to-cyan-400" />

                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <Volume2 className="w-6 h-6" />
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-xl font-bold text-slate-200">AI店員からの提案</h3>
                    <p className="text-lg leading-relaxed text-slate-300">
                      {recommendation.reason}
                    </p>
                  </div>
                </div>

                <div className="mt-8 flex flex-wrap gap-2">
                  {recommendation.search_keywords?.map((kw: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-slate-700 text-cyan-300 rounded-full text-sm font-medium border border-slate-600">
                      #{kw}
                    </span>
                  ))}
                </div>
              </div>

              {capturedImage && (
                <div className="flex items-center space-x-4 bg-slate-800/30 p-4 rounded-2xl border border-slate-800">
                  <div className="w-16 h-20 rounded-lg overflow-hidden flex-shrink-0">
                    <img src={capturedImage} className="w-full h-full object-cover" alt="Captured" />
                  </div>
                  <div className="text-sm text-slate-400">
                    <Check className="w-4 h-4 inline mr-1 text-emerald-500" />
                    あなたのコーディネートを分析済み
                  </div>
                </div>
              )}
            </div>

            {/* 右側: Shopify商品リスト */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold flex items-center">
                  <span className="bg-emerald-500 w-3 h-8 rounded-full mr-3 inline-block" />
                  おすすめのアイテム
                </h3>
                <span className="text-slate-400 text-sm">
                  {recommendation.shopify_products?.length || 0}件見つかりました
                </span>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {recommendation.shopify_products?.length > 0 ? (
                  recommendation.shopify_products.map((product: any) => (
                    <div key={product.id} className="bg-slate-800 rounded-2xl overflow-hidden border border-slate-700 hover:border-emerald-500/50 transition-colors group">
                      <div className="aspect-square relative bg-slate-900">
                        {product.image_url ? (
                          <img src={product.image_url} alt={product.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center text-slate-600">No Image</div>
                        )}
                        <div className="absolute top-3 left-3 px-3 py-1 bg-black/70 backdrop-blur-md rounded-full text-sm font-bold text-emerald-400">
                          在庫あり
                        </div>
                      </div>

                      <div className="p-5 space-y-3">
                        <h4 className="font-bold text-lg line-clamp-1 truncate" title={product.title}>{product.title}</h4>
                        <p className="text-emerald-400 font-bold text-xl">{product.price}</p>

                        <a
                          href={product.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-4 block w-full py-3 text-center bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
                        >
                          詳細を見る
                        </a>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 bg-slate-800/50 border border-slate-700 border-dashed rounded-3xl p-12 text-center text-slate-400">
                    <p className="text-lg">現在、条件に合うアイテムが店舗にありません。</p>
                    <p className="text-sm mt-2">条件を変えてもう一度お試しください。</p>
                  </div>
                )}
              </div>

              <div className="pt-8">
                <button
                  onClick={resetApp}
                  className="w-full py-4 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-2xl font-bold flex items-center justify-center space-x-2 transition-colors border border-slate-700 hover:border-slate-600"
                >
                  <RefreshCcw className="w-5 h-5" />
                  <span>最初からやり直す</span>
                </button>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
