"use client";

import { motion } from "framer-motion";
import { ProjectionPayload } from "@/lib/projection-types";
import CatIcon from "@/components/icons/CatIcon";

// ============================================
// IDLE SCENE
// ============================================
export function ProjectionIdleScene() {
  return (
    <motion.div
      key="idle"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
      className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none overflow-hidden"
    >
      <motion.div
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="flex flex-col items-center gap-6 z-10"
      >
        <div className="flex items-center gap-6 mb-6">
          <div className="w-24 h-24 bg-[#FF6B35] rounded-3xl flex items-center justify-center shadow-lg">
            <span className="text-[#141E2B] text-4xl font-extrabold">85</span>
          </div>
          <span className="text-6xl font-black text-[#FF8A5B] tracking-[0.15em]">STORE</span>
        </div>
        <CatIcon variant="default" size={80} theme="dark" />
        <p className="text-3xl text-[#8A9AAD] font-light tracking-wide mt-4">
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
      <div className="flex items-center gap-4 mb-8">
        <CatIcon variant="thinking" size={48} theme="dark" />
        <h2 className="text-4xl text-[#8A9AAD] font-light">
          好みを入力中...
        </h2>
      </div>

      {payload.userName && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-6xl font-bold text-[#FF6B35] mb-12 drop-shadow-lg"
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
            className="px-6 py-3 rounded-full border-2 border-[#FF6B35]/50 bg-[#FF6B35]/10 text-[#FF8A5B] text-2xl font-bold shadow-[0_0_15px_rgba(255,107,53,0.2)]"
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
            <div key={`h-${i}`} className="w-full h-[1px] bg-[#FF6B35]/30 shadow-[0_0_5px_rgba(255,107,53,0.3)]" />
          ))}
        </div>
        <div className="absolute inset-0 flex justify-evenly">
          {vLines.map((_, i) => (
            <div key={`v-${i}`} className="h-full w-[1px] bg-[#FF6B35]/30 shadow-[0_0_5px_rgba(255,107,53,0.3)]" />
          ))}
        </div>
      </div>

      <motion.div
        animate={{ top: ["-10%", "110%"] }}
        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 right-0 h-4 bg-[#FF6B35]/40 shadow-[0_0_40px_rgba(255,107,53,0.8)]"
      />

      <div className="absolute top-16 left-1/2 -translate-x-1/2 text-center z-20 mix-blend-plus-lighter">
        <h2 className="text-4xl font-mono text-[#FF6B35] tracking-[0.5em] opacity-80 drop-shadow-md">
          STANDBY
        </h2>
      </div>

      <div className="absolute bottom-16 left-1/2 -translate-x-1/2 flex flex-wrap justify-center gap-3 w-full max-w-3xl px-8 z-20">
        {payload.selectedTags.map((tag) => (
          <div key={tag} className="px-4 py-1.5 border border-[#2A3D50] bg-[#1E2D3D] text-[#8A9AAD] text-lg rounded font-mono">
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
         <div className="relative w-1/3 aspect-[3/4] rounded-3xl overflow-hidden border-2 border-[#FF6B35]/50 shadow-[0_0_30px_rgba(255,107,53,0.2)] z-10">
           <img src={payload.capturedImage} className="w-full h-full object-cover" />

           <motion.div
             animate={{ top: ['0%', '100%', '0%'] }}
             transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
             className="absolute left-0 right-0 h-2 bg-[#FF6B35] shadow-[0_0_20px_rgba(255,107,53,1)] opacity-70"
           />
         </div>
       )}

       {/* CatIcon thinking */}
       <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
         <CatIcon variant="thinking" size={96} theme="dark" />
       </div>

       {/* テキスト */}
       <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-center z-20">
         <motion.h2
           animate={{ opacity: [0.5, 1, 0.5] }}
           transition={{ duration: 2, repeat: Infinity }}
           className="text-4xl text-[#F0F2F5] font-bold tracking-widest bg-[#141E2B]/70 px-8 py-4 rounded-full"
         >
           AI CONNECTING...
         </motion.h2>
         {payload.analyzeTimedOut && (
           <p className="text-xl text-[#FF8A5B] mt-4 bg-[#141E2B]/70 px-6 py-2 rounded-full inline-block">
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
