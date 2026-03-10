"use client";

import { motion } from "framer-motion";
import { Camera } from "lucide-react";
import React from "react";

interface CameraViewProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  countdown: number | null;
  onCapture: () => void;
  onCancelCountdown: () => void;
}

export function CameraView({
  videoRef,
  countdown,
  onCapture,
  onCancelCountdown,
}: CameraViewProps) {
  return (
    <motion.div
      key="camera"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="absolute inset-x-0 bottom-0 top-[80px] flex flex-col items-center justify-center p-6 bg-bg overflow-hidden"
    >
      <div className="relative w-full max-w-4xl aspect-[4/3] rounded-3xl overflow-hidden bg-[#F0F4F8] shadow-lg border-4 border-border">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />

        {/* ターゲット用オーバーレイUI */}
        <div className="absolute inset-0 pointer-events-none">
          {/* 四隅のブラケット */}
          <div className="absolute top-8 left-8 w-16 h-16 border-t-4 border-l-4 border-primary/50 rounded-tl-xl" />
          <div className="absolute top-8 right-8 w-16 h-16 border-t-4 border-r-4 border-primary/50 rounded-tr-xl" />
          <div className="absolute bottom-8 left-8 w-16 h-16 border-b-4 border-l-4 border-primary/50 rounded-bl-xl" />
          <div className="absolute bottom-8 right-8 w-16 h-16 border-b-4 border-r-4 border-primary/50 rounded-br-xl" />

          {/* 中央のガイド */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-[80%] h-[80%] border-2 border-primary/30 rounded-2xl relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white/80 px-4 py-1 rounded-full text-primary text-sm tracking-wider font-mono backdrop-blur-sm border border-primary/30">
                FIT PERSON IN FRAME
              </div>
            </div>
          </div>
        </div>

        {/* カウントダウン */}
        {countdown !== null && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/40 backdrop-blur-md">
            <motion.div
              key={countdown}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.5 }}
              className="text-white text-9xl font-bold font-mono"
            >
              {countdown}
            </motion.div>
          </div>
        )}
      </div>

      {/* アクション領域 */}
      <div className="absolute bottom-12 flex flex-col items-center gap-6">
        {countdown === null ? (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onCapture}
            className="group relative flex items-center justify-center w-24 h-24 rounded-full bg-primary text-white shadow-lg shadow-primary/30 ring-4 ring-primary/30 hover:bg-primary-dark transition-colors"
          >
            <div className="absolute inset-2 rounded-full border-4 border-white/20" />
            <Camera className="w-10 h-10 relative z-10" />
          </motion.button>
        ) : (
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={onCancelCountdown}
            className="px-8 py-4 rounded-xl bg-primary-dark hover:bg-primary text-white font-medium shadow-lg backdrop-blur-sm transition-colors text-lg"
          >
            キャンセル
          </motion.button>
        )}

        {countdown === null && (
           <div className="text-primary font-mono tracking-widest text-sm bg-white/80 px-4 py-2 rounded-full backdrop-blur-sm">
             READY TO CAPTURE
           </div>
        )}
      </div>
    </motion.div>
  );
}
