"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { QRCodeSVG } from "qrcode.react";
import { Sparkles } from "lucide-react";
import Image from "next/image";
import {
  type AppState,
  type ProjectionPayload,
  type RecommendationPattern,
  type ShopifyProduct,
} from "@/lib/projection-types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

// SSR/クライアント間でハイドレーション不一致を防ぐための固定パーティクル座標
const PARTICLES = Array.from({ length: 12 }, (_, i) => ({
  x1: ((i * 37 + 13) % 97),
  y1: ((i * 53 + 29) % 97),
  x2: ((i * 41 + 61) % 97),
  y2: ((i * 67 + 43) % 97),
  scale: (i % 5) * 0.4 + 0.5,
  duration: (i % 4) * 2.5 + 8,
}));

const defaultPayload: ProjectionPayload = {
  selectedTags: [],
  userName: "",
  capturedImage: null,
  recommendation: null,
  analyzeTimedOut: false,
};

// ========== IDLE: ウェルカム画面 ==========
function IdleScene() {
  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full h-full flex flex-col items-center justify-center relative"
    >
      {/* 動くグラデーション背景 */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-emerald-950/30 to-cyan-950/20 animate-gradient-shift" />

      {/* 浮遊パーティクル */}
      {PARTICLES.map((p, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-emerald-400/40"
          initial={{
            x: `${p.x1}vw`,
            y: `${p.y1}vh`,
            scale: p.scale,
          }}
          animate={{
            y: [null, `${p.y2}vh`],
            x: [null, `${p.x2}vw`],
            opacity: [0.2, 0.6, 0.2],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut",
          }}
        />
      ))}

      <div className="relative z-10 text-center space-y-8">
        <motion.div
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="flex items-center justify-center gap-4"
        >
          <Sparkles className="w-16 h-16 text-emerald-400" />
          <h1 className="text-8xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
            VINTAGE.AI
          </h1>
        </motion.div>

        <motion.p
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="text-3xl text-slate-400 font-light"
        >
          AIがあなたにぴったりの一点モノを見つけます
        </motion.p>

        <div className="flex items-center justify-center gap-3 pt-8">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <p className="text-xl text-slate-500">タッチスクリーンからスタートしてください</p>
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </div>
    </motion.div>
  );
}

// ========== PREFERENCE: 好み入力中 ==========
function PreferenceScene({ payload }: { payload: ProjectionPayload }) {
  return (
    <motion.div
      key="preference"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full h-full flex flex-col items-center justify-center relative"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-indigo-950/20 to-slate-950" />

      <div className="relative z-10 text-center space-y-10 max-w-4xl px-8">
        {payload.userName && (
          <motion.p
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl text-emerald-400 font-bold"
          >
            ようこそ、{payload.userName}さん
          </motion.p>
        )}

        <h2 className="text-5xl font-bold text-white">
          好みを入力中...
        </h2>

        {payload.selectedTags.length > 0 && (
          <motion.div
            className="flex flex-wrap justify-center gap-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {payload.selectedTags.map((tag, i) => (
              <motion.span
                key={tag}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="px-6 py-3 bg-emerald-500/20 text-emerald-300 rounded-full text-2xl border border-emerald-500/40 font-medium"
              >
                {tag}
              </motion.span>
            ))}
          </motion.div>
        )}

        {payload.selectedTags.length === 0 && (
          <p className="text-2xl text-slate-500">
            タッチスクリーンで好みのスタイルを選択してください
          </p>
        )}
      </div>
    </motion.div>
  );
}

// ========== CAMERA_ACTIVE: 撮影準備中 ==========
function CameraScene({ payload }: { payload: ProjectionPayload }) {
  return (
    <motion.div
      key="camera"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full h-full flex flex-col items-center justify-center relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-slate-950" />

      {/* スキャングリッド */}
      <div className="absolute inset-0 opacity-10">
        <div
          className="w-full h-full"
          style={{
            backgroundImage:
              "linear-gradient(rgba(16,185,129,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.3) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* 横スキャンライン */}
      <motion.div
        initial={{ top: "-5%" }}
        animate={{ top: "105%" }}
        transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
        className="absolute left-0 right-0 h-0.5 bg-emerald-400 shadow-[0_0_30px_10px_rgba(16,185,129,0.4)] z-20"
      />

      {/* カメラビューファインダー枠 */}
      <div className="relative z-10 w-[60vh] h-[80vh] max-w-[80vw] max-h-[80vh]">
        {/* 四隅のブラケット */}
        <div className="absolute top-0 left-0 w-16 h-16 border-t-4 border-l-4 border-emerald-400" />
        <div className="absolute top-0 right-0 w-16 h-16 border-t-4 border-r-4 border-emerald-400" />
        <div className="absolute bottom-0 left-0 w-16 h-16 border-b-4 border-l-4 border-emerald-400" />
        <div className="absolute bottom-0 right-0 w-16 h-16 border-b-4 border-r-4 border-emerald-400" />

        <div className="absolute inset-0 flex flex-col items-center justify-center gap-6">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-6 h-6 rounded-full border-4 border-emerald-400"
          />
          <h2 className="text-5xl font-bold text-white">撮影スタンバイ</h2>
          <p className="text-2xl text-slate-400">カメラの前に立ってください</p>
        </div>
      </div>

      {/* 好みタグ表示 */}
      {payload.selectedTags.length > 0 && (
        <div className="absolute bottom-12 flex flex-wrap justify-center gap-3 px-8">
          {payload.selectedTags.map((tag) => (
            <span key={tag} className="px-4 py-2 bg-emerald-500/20 text-emerald-300 rounded-full text-lg border border-emerald-500/30">
              {tag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// マトリックス風カタカナ列の固定データ
const MATRIX_COLS = Array.from({ length: 8 }, (_, i) => ({
  duration: (i % 4) * 1.0 + 3,
  delay: (i * 0.4) % 3,
  chars: Array.from({ length: 30 }, (_, j) =>
    String.fromCharCode(0x30A0 + ((i * 31 + j * 17 + 7) % 96))
  ),
}));

// ========== ANALYZING: 解析中 ==========
function AnalyzingScene({ payload }: { payload: ProjectionPayload }) {
  return (
    <motion.div
      key="analyzing"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full h-full flex items-center justify-center relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-slate-950" />

      {/* データストリーム左右 */}
      {[0, 1].map((side) => (
        <div
          key={side}
          className="absolute top-0 bottom-0 w-32 overflow-hidden opacity-20"
          style={{ [side === 0 ? "left" : "right"]: "5%" }}
        >
          {MATRIX_COLS.map((col, i) => (
            <motion.div
              key={i}
              className="absolute text-emerald-400 font-mono text-xs leading-none whitespace-nowrap"
              style={{ left: `${i * 16}px` }}
              initial={{ y: -200 }}
              animate={{ y: "100vh" }}
              transition={{
                duration: col.duration,
                repeat: Infinity,
                delay: col.delay,
                ease: "linear",
              }}
            >
              {col.chars.map((ch, j) => (
                <div key={j}>{ch}</div>
              ))}
            </motion.div>
          ))}
        </div>
      ))}

      <div className="relative z-10 flex flex-col items-center gap-12">
        {/* 回転リング + 画像 */}
        <div className="relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="absolute -inset-8 border-2 border-dashed border-cyan-400/40 rounded-full"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
            className="absolute -inset-16 border border-emerald-400/20 rounded-full"
          />

          {payload.capturedImage ? (
            <div className="relative w-[35vh] h-[45vh] rounded-2xl overflow-hidden shadow-[0_0_60px_rgba(16,185,129,0.3)]">
              <img
                src={payload.capturedImage}
                alt="Scanning"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent" />
              {/* スキャンライン */}
              <motion.div
                initial={{ top: "-10%" }}
                animate={{ top: "110%" }}
                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                className="absolute left-0 right-0 h-1 bg-emerald-400 shadow-[0_0_30px_10px_rgba(16,185,129,0.8)] z-10"
              />
            </div>
          ) : (
            <div className="w-[35vh] h-[45vh] rounded-2xl bg-slate-800 flex items-center justify-center">
              <Sparkles className="w-20 h-20 text-emerald-400 animate-pulse" />
            </div>
          )}
        </div>

        {/* テキスト */}
        <div className="text-center space-y-4">
          <motion.h2
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400"
          >
            AIがコーディネートを考案中...
          </motion.h2>
          <p className="text-2xl text-slate-400">
            服の特徴を分析し、最適なアイテムを探しています
          </p>
          {payload.analyzeTimedOut && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xl text-amber-400"
            >
              少々お待ちください...
            </motion.p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ========== RESULT: 結果表示 ==========
function ResultScene({ payload }: { payload: ProjectionPayload }) {
  const rec = payload.recommendation;
  if (!rec) return null;

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full h-full flex flex-col overflow-auto relative"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 to-slate-900" />

      <div className="relative z-10 flex flex-col gap-8 p-10 min-h-full">
        {/* 上部: 解析結果 */}
        <div className="flex gap-10 items-start">
          {/* 撮影画像 */}
          {payload.capturedImage && (
            <div className="flex-shrink-0">
              <div className="relative w-56 rounded-2xl overflow-hidden border-4 border-slate-700 shadow-2xl">
                <img src={payload.capturedImage} alt="Captured" className="w-full object-contain" />
                {rec.box_ymin !== undefined && rec.box_ymax !== 1000 && (
                  <div
                    className="absolute border-[3px] border-emerald-400 bg-emerald-400/20 pointer-events-none"
                    style={{
                      top: `${(rec.box_ymin / 1000) * 100}%`,
                      left: `${(rec.box_xmin / 1000) * 100}%`,
                      height: `${((rec.box_ymax - rec.box_ymin) / 1000) * 100}%`,
                      width: `${((rec.box_xmax - rec.box_xmin) / 1000) * 100}%`,
                    }}
                  />
                )}
              </div>
            </div>
          )}

          {/* 分析テキスト */}
          <div className="flex-1 space-y-5">
            <div className="flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-cyan-400" />
              <h2 className="text-4xl font-bold text-white">スタイリング分析結果</h2>
            </div>
            <p className="text-2xl text-slate-300 leading-relaxed">{rec.analyzed_outfit}</p>

            {/* タグ表示 */}
            <div className="flex flex-wrap gap-3">
              {rec.detected_style?.map((s, i) => (
                <span key={i} className="px-4 py-2 bg-cyan-500/20 text-cyan-300 rounded-full text-lg border border-cyan-500/30">
                  {s}
                </span>
              ))}
              {payload.selectedTags.map((tag, i) => (
                <span key={`p-${i}`} className="px-4 py-2 bg-emerald-500/20 text-emerald-300 rounded-full text-lg border border-emerald-500/30">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 下部: 提案パターン */}
        <div className="flex-1">
          <h3 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
            <span className="bg-emerald-500 w-3 h-10 rounded-full inline-block" />
            おすすめコーディネート
          </h3>

          <div className="grid grid-cols-3 gap-6">
            {rec.recommendations?.map((pattern: RecommendationPattern, idx: number) => (
              <div key={idx} className="bg-slate-800/80 rounded-2xl border border-slate-700 p-6 flex flex-col">
                <h4 className="text-2xl font-bold text-emerald-400 pb-3 border-b border-emerald-500/30 mb-4">
                  {pattern.title}
                </h4>
                <p className="text-slate-300 text-base leading-relaxed mb-4">{pattern.reason}</p>

                {/* 検索キーワード */}
                <div className="flex flex-wrap gap-2 mb-5">
                  {pattern.search_keywords?.map((kw: string, i: number) => (
                    <span key={i} className="px-3 py-1 bg-slate-900 border border-emerald-500/30 text-emerald-300 rounded text-sm">
                      #{kw}
                    </span>
                  ))}
                </div>

                {/* 商品リスト + QRコード */}
                <div className="flex-1 flex flex-col gap-4">
                  {pattern.shopify_products?.length > 0 ? (
                    pattern.shopify_products.slice(0, 2).map((product: ShopifyProduct) => (
                      <div key={product.id} className="bg-slate-900 rounded-xl border border-slate-700 p-4 flex gap-4">
                        <div className="w-20 h-20 flex-shrink-0 relative rounded-lg overflow-hidden bg-slate-800">
                          {product.image_url ? (
                            <Image
                              src={product.image_url}
                              alt={product.title}
                              fill
                              sizes="80px"
                              className="object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-600 text-xs">No Image</div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h5 className="font-bold text-base text-slate-200 line-clamp-2">{product.title}</h5>
                          <p className="text-emerald-400 font-bold text-lg mt-1">{product.price}</p>
                        </div>
                        {product.url && product.url !== "#" && (
                          <div className="flex-shrink-0 bg-white rounded-lg p-1.5">
                            <QRCodeSVG value={product.url} size={64} level="M" />
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="bg-slate-900/50 border border-slate-700 border-dashed rounded-xl p-6 text-center text-slate-500">
                      該当商品なし
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ========== ミラーオーバーレイ ==========
function MirrorOverlay({ frame }: { frame: string | null }) {
  if (!frame) return null;
  return (
    <img
      src={`data:image/webp;base64,${frame}`}
      alt=""
      className="absolute inset-0 w-full h-full object-contain z-30 pointer-events-none"
    />
  );
}

// ========== メインコンポーネント ==========
export default function ProjectionPage() {
  const [appState, setAppState] = useState<AppState>("IDLE");
  const [payload, setPayload] = useState<ProjectionPayload>(defaultPayload);
  const [flashing, setFlashing] = useState(false);
  const [mirrorFrame, setMirrorFrame] = useState<string | null>(null);

  // バックエンドWebSocket接続（状態同期 + ミラーフレーム受信）
  // iPad → Backend → この画面 の経路で、別デバイス間でも動作する
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const connect = () => {
      ws = new WebSocket(`${WS_URL}/ws/projection/display`);
      ws.onopen = () => {
        ws?.send(JSON.stringify({ type: "REQUEST_STATE" }));
      };
      ws.onmessage = (e) => {
        if (typeof e.data !== "string") return;
        // Raw base64ミラーフレーム（'{'で始まらないテキスト）
        if (!e.data.startsWith("{")) {
          setMirrorFrame(e.data);
          return;
        }
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "STATE_CHANGE") {
            setAppState(msg.state);
            setPayload(msg.payload);
            // ミラー非活性状態ではフレームをクリア
            if (!["CAMERA_ACTIVE", "ANALYZING"].includes(msg.state)) {
              setMirrorFrame(null);
            }
          } else if (msg.type === "FLASH") {
            setFlashing(true);
            setTimeout(() => setFlashing(false), 1200);
          }
        } catch {
          // パースエラーは無視
        }
      };
      ws.onclose = () => {
        ws = null;
        reconnectTimeout = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws?.close();
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, []);

  return (
    <main className="w-screen h-screen overflow-hidden bg-slate-950 text-white cursor-none select-none">
      <style jsx global>{`
        @keyframes gradient-shift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .animate-gradient-shift {
          background-size: 200% 200%;
          animation: gradient-shift 8s ease infinite;
        }
      `}</style>

      {/* フラッシュ（白画面オーバーレイ） */}
      <AnimatePresence>
        {flashing && (
          <motion.div
            key="flash"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ exit: { duration: 0.6 } }}
            className="fixed inset-0 z-50 bg-white"
          />
        )}
      </AnimatePresence>

      {/* ミラー: 人物切り抜き映像を前面にオーバーレイ */}
      <MirrorOverlay frame={mirrorFrame} />

      <AnimatePresence mode="wait">
        {appState === "IDLE" && <IdleScene />}
        {appState === "PREFERENCE" && <PreferenceScene payload={payload} />}
        {appState === "CAMERA_ACTIVE" && <CameraScene payload={payload} />}
        {appState === "ANALYZING" && <AnalyzingScene payload={payload} />}
        {appState === "RESULT" && <ResultScene payload={payload} />}
      </AnimatePresence>
    </main>
  );
}
