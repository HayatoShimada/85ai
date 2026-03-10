"use client";

import { motion } from "framer-motion";
import { AlertTriangle, RotateCcw } from "lucide-react";
import CatIcon from "@/components/icons/CatIcon";

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
      <div className="relative w-64 h-64 rounded-3xl overflow-hidden shadow-lg bg-card border border-border">
        {analyzedImage && (
          <img
            src={analyzedImage}
            alt="Captured"
            className="w-full h-full object-cover"
          />
        )}
      </div>

      <div className="text-center space-y-4 max-w-md">
        <CatIcon variant="thinking" size={64} />
        <h2 className="text-2xl font-bold text-text">
          スタイルを解析中
        </h2>
        <motion.p
          className="text-text-muted text-sm"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          もうちょっと待ってね...
        </motion.p>

        {analyzeError ? (
          <div className="bg-[#FFF5F0] border-l-[3px] border-l-primary border border-primary-dark/20 rounded-xl p-4 flex flex-col items-center gap-4">
            <CatIcon variant="error" size={32} className="mb-2" />
            <div className="flex items-center gap-2 text-primary-dark">
              <AlertTriangle className="w-5 h-5" />
              <p className="font-medium text-sm">{analyzeError}</p>
            </div>
            <div className="flex gap-2 w-full">
              <button
                onClick={onRetry}
                className="flex-1 px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                リトライ
              </button>
              <button
                onClick={onReset}
                className="flex-1 px-4 py-2 bg-white hover:bg-[#F5F6F7] text-text border border-border rounded-lg text-sm font-medium transition-colors"
              >
                戻る
              </button>
            </div>
          </div>
        ) : analyzeTimedOut ? (
          <div className="bg-card p-4 rounded-xl border border-border space-y-3">
            <p className="text-text-body text-sm">
              検索に時間がかかっています。もうしばらくお待ちください。
            </p>
            <button
              onClick={onReset}
              className="px-4 py-2 border border-border hover:bg-[#F5F6F7] text-text rounded-lg text-sm font-medium transition-colors"
            >
              キャンセルしてやり直す
            </button>
          </div>
        ) : (
          <p className="text-text-muted text-sm">
            あなたの服装やスタイルに合わせて<br />
            数万点の在庫から最適なアイテムを探索しています
          </p>
        )}
      </div>
    </motion.div>
  );
}
