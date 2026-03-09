"use client";

import { motion } from "framer-motion";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface AnalyzingViewProps {
  analyzedImage: string | null;
  analyzeTimedOut: boolean;
  analyzeError: string | null;
  onRetry: () => void;
  onReset: () => void;
}

export function AnalyzingView({
  analyzedImage,
  analyzeTimedOut,
  analyzeError,
  onRetry,
  onReset,
}: AnalyzingViewProps) {
  return (
    <motion.div
      key="analyzing"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center p-8 space-y-12"
    >
      <div className="relative w-64 h-64 rounded-3xl overflow-hidden shadow-2xl bg-black border border-slate-700/50">
        {analyzedImage && (
          <img
            src={analyzedImage}
            alt="Captured"
            className="w-full h-full object-cover"
          />
        )}
        <div className="absolute inset-0 bg-emerald-500/20 mix-blend-overlay" />
        <motion.div
          animate={{ top: ["0%", "100%", "0%"] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          className="absolute left-0 right-0 h-1 bg-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.8)]"
        />
        
        {/* スキャンリングエフェクト */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="w-[140%] h-[140%] rounded-full border border-dashed border-emerald-500/40"
          />
        </div>
      </div>

      <div className="text-center space-y-4 max-w-md">
        <h2 className="text-2xl font-bold text-emerald-400">
          AIが解析中...
        </h2>
        
        {analyzeError ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex flex-col items-center gap-4">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <p className="font-medium text-sm">{analyzeError}</p>
            </div>
            <div className="flex gap-2 w-full">
              <button
                onClick={onRetry}
                className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                リトライ
              </button>
              <button
                onClick={onReset}
                className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors"
              >
                戻る
              </button>
            </div>
          </div>
        ) : analyzeTimedOut ? (
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700 space-y-3">
            <p className="text-slate-300 text-sm">
              検索に時間がかかっています。もうしばらくお待ちください。
            </p>
            <button
              onClick={onReset}
              className="px-4 py-2 border border-slate-600 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-colors"
            >
              キャンセルしてやり直す
            </button>
          </div>
        ) : (
          <p className="text-slate-400 text-sm">
            あなたの服装やスタイルに合わせて<br />
            数万点の在庫から最適なアイテムを探索しています
          </p>
        )}
      </div>
    </motion.div>
  );
}
