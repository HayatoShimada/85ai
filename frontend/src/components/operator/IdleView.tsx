"use client";

import { motion } from "framer-motion";
import CatIcon from "@/components/icons/CatIcon";

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
      <div className="space-y-4 flex flex-col items-center">
        <div className="w-20 h-20 bg-navy rounded-3xl flex items-center justify-center shadow-lg">
          <span className="text-primary text-3xl font-extrabold">85</span>
        </div>
        <CatIcon variant="default" size={48} className="mt-4" />
        <h1 className="text-5xl font-black text-navy tracking-wider">
          85 STORE
        </h1>
        <p className="text-text-muted text-lg">
          あなたに合う一着を一緒に探しましょう
        </p>
      </div>

      <div className="space-y-4 w-full">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          className="w-full py-5 px-8 bg-primary hover:bg-primary-dark text-white rounded-2xl font-bold text-xl shadow-lg shadow-[0_0_20px_rgba(255,107,53,0.3)] transition-all flex items-center justify-center gap-3"
        >
          はじめる
        </motion.button>

        <button
          onClick={onOpenProjection}
          className="w-full py-4 text-text-muted hover:text-text-body transition-colors text-sm font-medium"
        >
          プロジェクション表示を開く →
        </button>
      </div>
    </motion.div>
  );
}
