"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import Image from "next/image";
import { ProjectionPayload } from "@/lib/projection-types";

// ============================================
// IDLE SCENE
// ============================================
export function ProjectionIdleScene() {
  // パーティクルの初期座標（固定）
  const particles = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    x: ((i * 37 + 13) % 97) + "%",
    y: ((i * 53 + 29) % 97) + "%",
    scale: (i % 3) * 0.5 + 0.5,
    duration: (i % 3) * 2 + 4,
  }));

  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
      className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none overflow-hidden"
    >
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute w-2 h-2 rounded-full bg-emerald-400"
          style={{ left: p.x, top: p.y }}
          animate={{ y: [0, -30, 0], opacity: [0.2, 0.8, 0.2] }}
          transition={{ duration: p.duration, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}

      <motion.div
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="flex flex-col items-center gap-6 z-10"
      >
        <div className="w-24 h-24 rounded-3xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-[0_0_50px_rgba(16,185,129,0.3)]">
          <Sparkles className="w-12 h-12" />
        </div>
        <h1 className="text-8xl font-black tracking-tighter bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          VINTAGE.AI
        </h1>
        <p className="text-3xl text-slate-300 font-light tracking-wide mt-4">
          AIがあなたにぴったりの一点モノを見つけます
        </p>
      </motion.div>
    </motion.div>
  );
}

// ============================================
// PREFERENCE SCENE
// ============================================
export function ProjectionPreferenceScene({ payload }: { payload: ProjectionPayload }) {
  return (
    <motion.div
      key="pref"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center"
    >
      <h2 className="text-4xl text-slate-300 mb-8 font-light">
        好みを入力中...
      </h2>
      
      {payload.userName && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-6xl font-bold text-emerald-400 mb-12 shadow-emerald-500/20 drop-shadow-lg"
        >
          ようこそ、{payload.userName} さん
        </motion.div>
      )}

      <div className="flex flex-wrap justify-center gap-4 max-w-4xl">
        {payload.selectedTags.map((tag, i) => (
          <motion.div
            key={tag}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className="px-6 py-3 rounded-full border-2 border-emerald-500/50 bg-emerald-500/10 text-emerald-300 text-2xl font-bold shadow-[0_0_20px_rgba(16,185,129,0.2)]"
          >
            {tag}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

// ============================================
// CAMERA SCENE
// ============================================
export function ProjectionCameraScene({ payload }: { payload: ProjectionPayload }) {
  // グリッド線
  const hLines = Array.from({ length: 10 });
  const vLines = Array.from({ length: 10 });

  return (
    <motion.div
      key="camera"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
    >
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 flex flex-col justify-evenly">
          {hLines.map((_, i) => (
            <div key={`h-${i}`} className="w-full h-[1px] bg-emerald-500/30 shadow-[0_0_5px_rgba(16,185,129,0.5)]" />
          ))}
        </div>
        <div className="absolute inset-0 flex justify-evenly">
          {vLines.map((_, i) => (
            <div key={`v-${i}`} className="h-full w-[1px] bg-emerald-500/30 shadow-[0_0_5px_rgba(16,185,129,0.5)]" />
          ))}
        </div>
      </div>

      <motion.div
        animate={{ top: ["-10%", "110%"] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 right-0 h-4 bg-emerald-500/40 shadow-[0_0_40px_rgba(16,185,129,1)]"
      />

      <div className="absolute top-16 left-1/2 -translate-x-1/2 text-center z-20 mix-blend-plus-lighter">
        <h2 className="text-4xl font-mono text-emerald-400 tracking-[0.5em] opacity-80 shadow-emerald-500/50 drop-shadow-md">
          STANDBY
        </h2>
      </div>

      <div className="absolute bottom-16 left-1/2 -translate-x-1/2 flex flex-wrap justify-center gap-3 w-full max-w-3xl px-8 z-20">
        {payload.selectedTags.map((tag) => (
          <div key={tag} className="px-4 py-1.5 border border-cyan-500/50 bg-cyan-500/10 text-cyan-300 text-lg rounded font-mono shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            {tag}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ============================================
// ANALYZING SCENE
// ============================================
export function ProjectionAnalyzingScene({ payload }: { payload: ProjectionPayload }) {
  return (
    <motion.div
       key="analyze"
       initial={{ opacity: 0, scale: 0.9 }}
       animate={{ opacity: 1, scale: 1 }}
       exit={{ opacity: 0, scale: 1.1 }}
       transition={{ duration: 0.8 }}
       className="absolute inset-0 flex items-center justify-center"
     >
       {/* 撮影画像 */}
       {payload.capturedImage && (
         <div className="relative w-1/3 aspect-[3/4] rounded-3xl overflow-hidden border-2 border-emerald-500/50 shadow-[0_0_50px_rgba(16,185,129,0.2)] z-10">
           <img src={payload.capturedImage} className="w-full h-full object-cover" />
           <div className="absolute inset-0 bg-emerald-500/10 mix-blend-overlay" />
           
           <motion.div 
             animate={{ top: ['0%', '100%', '0%'] }}
             transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
             className="absolute left-0 right-0 h-2 bg-emerald-400 shadow-[0_0_20px_rgba(16,185,129,1)] opacity-70"
           />
         </div>
       )}

       {/* 装飾リング */}
       <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
         <motion.div animate={{ rotate: 360 }} transition={{ duration: 10, repeat: Infinity, ease: "linear" }} className="absolute w-[45vw] h-[45vw] rounded-full border border-dashed border-emerald-500/30" />
         <motion.div animate={{ rotate: -360 }} transition={{ duration: 15, repeat: Infinity, ease: "linear" }} className="absolute w-[55vw] h-[55vw] rounded-full border-2 border-dotted border-cyan-500/20" />
       </div>

       {/* テキスト */}
       <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-center z-20">
         <motion.h2 
           animate={{ opacity: [0.5, 1, 0.5] }}
           transition={{ duration: 2, repeat: Infinity }}
           className="text-4xl text-emerald-400 font-bold tracking-widest bg-black/50 px-8 py-4 rounded-full backdrop-blur-md"
         >
           AI CONNECTING...
         </motion.h2>
         {payload.analyzeTimedOut && (
           <p className="text-xl text-amber-400 mt-4 bg-black/50 px-6 py-2 rounded-full inline-block backdrop-blur-md shadow-[0_0_15px_rgba(245,158,11,0.3)]">
             膨大なデーターベースから探索中です。少々お待ちください…
           </p>
         )}
       </div>
    </motion.div>
  );
}

// ============================================
// MIRROR OVERLAY
// ============================================
export function MirrorOverlay({ frame }: { frame: string | null }) {
  if (!frame) return null;
  return (
    <div className="absolute inset-0 z-30 pointer-events-none flex items-center justify-center opacity-80 mix-blend-screen">
      <img
        src={`data:image/webp;base64,${frame}`}
        className="w-full h-full object-cover scale-x-[-1]"
        alt="mirror stream"
      />
    </div>
  );
}
