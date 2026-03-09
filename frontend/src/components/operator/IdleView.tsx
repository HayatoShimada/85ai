"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

interface IdleViewProps {
  onStart: () => void;
  onOpenProjection: () => void;
}

export function IdleView({ onStart, onOpenProjection }: IdleViewProps) {
  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      className="max-w-md mx-auto p-8 flex flex-col items-center justify-center min-h-[60vh] text-center space-y-12"
    >
      <div className="space-y-4">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-emerald-500/20 text-emerald-400 mb-4 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
          <Sparkles className="w-10 h-10" />
        </div>
        <h1 className="text-5xl font-black tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          VINTAGE.AI
        </h1>
        <p className="text-slate-400 text-lg">
          AIがあなたのアウトフィットを解析し、<br />
          最適な一点モノの古着をご提案します。
        </p>
      </div>

      <div className="space-y-4 w-full">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          className="w-full py-5 px-8 bg-emerald-500 hover:bg-emerald-400 text-white rounded-2xl font-bold text-xl shadow-lg shadow-emerald-500/25 transition-all flex items-center justify-center gap-3"
        >
          <Sparkles className="w-6 h-6" />
          接客をはじめる
        </motion.button>
        
        <button
          onClick={onOpenProjection}
          className="w-full py-4 text-slate-400 hover:text-slate-200 transition-colors text-sm font-medium"
        >
          別画面でプロジェクションを起動
        </button>
      </div>
    </motion.div>
  );
}
