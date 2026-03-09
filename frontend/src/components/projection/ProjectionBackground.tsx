"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { AppState } from "@/lib/projection-types";

interface ProjectionBackgroundProps {
  appState: AppState;
  selectedTags: string[];
}

export function ProjectionBackground({ appState, selectedTags }: ProjectionBackgroundProps) {
  // ステートとタグに応じて背景グラデーションの色と動きを決定する
  // (例)
  // IDLE: slate -> emerald -> cyan
  // PREFERENCE: インディゴ系
  // CAMERA_ACTIVE: ダーク + エメラルドグリッド
  // ANALYSIS: 濃紺ベースに強い赤/紫/エメラルドなどのパルス
  // RESULT: 選ばれたタグに影響されたグラデーション

  const bgConfig = useMemo(() => {
    let colors = ["#0f172a", "#10b981", "#06b6d4"]; // デフォルト
    let duration = 15;

    switch (appState) {
      case "IDLE":
        colors = ["#020617", "#065f46", "#0e7490"];
        duration = 20;
        break;
      case "PREFERENCE":
        colors = ["#1e1b4b", "#312e81", "#4c1d95"];
        duration = 10;
        break;
      case "CAMERA_ACTIVE":
        colors = ["#0a0a0a", "#022c22", "#064e3b"];
        duration = 15;
        break;
      case "ANALYZING":
        colors = ["#0f172a", "#059669", "#7c3aed"];
        duration = 5; // 激しい動き
        break;
      case "RESULT":
        // ユーザーの好みタグに応じてグラデーションのアクセントを変える（簡易ロジック）
        if (selectedTags.includes("ストリート") || selectedTags.includes("かっこいい")) {
          colors = ["#09090b", "#9f1239", "#be123c"];
        } else if (selectedTags.includes("ナチュラル") || selectedTags.includes("きれいめ")) {
          colors = ["#1c1917", "#78716c", "#a8a29e"];
        } else {
          colors = ["#1e293b", "#0ea5e9", "#14b8a6"];
        }
        duration = 20;
        break;
    }

    return { colors, duration };
  }, [appState, selectedTags]);

  return (
    <>
      <motion.div
        className="absolute inset-0 z-0 bg-gradient-to-br"
        animate={{
          background: [
            `linear-gradient(135deg, ${bgConfig.colors[0]}, ${bgConfig.colors[1]})`,
            `linear-gradient(135deg, ${bgConfig.colors[1]}, ${bgConfig.colors[2]})`,
            `linear-gradient(135deg, ${bgConfig.colors[2]}, ${bgConfig.colors[0]})`,
          ],
        }}
        transition={{
          duration: bgConfig.duration,
          repeat: Infinity,
          ease: "linear",
        }}
      />
      {/* SVGノイズオーバーレイ (画像不要) */}
      <svg className="absolute inset-0 z-0 w-full h-full opacity-20 pointer-events-none mix-blend-overlay">
        <filter id="noise">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter="url(#noise)" />
      </svg>
    </>
  );
}
