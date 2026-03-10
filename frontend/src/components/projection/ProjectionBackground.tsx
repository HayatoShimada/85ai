"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { AppState } from "@/lib/projection-types";

interface ProjectionBackgroundProps {
  appState: AppState;
  selectedTags: string[];
}

export function ProjectionBackground({ appState, selectedTags }: ProjectionBackgroundProps) {
  const bgConfig = useMemo(() => {
    let colors = ["#141E2B", "#1E3A5F", "#2C4A6F"]; // デフォルト
    let duration = 15;

    switch (appState) {
      case "IDLE":
        colors = ["#141E2B", "#1E2D3D", "#1E3A5F"];
        duration = 20;
        break;
      case "PREFERENCE":
        colors = ["#141E2B", "#2C4A6F", "#1E3A5F"];
        duration = 10;
        break;
      case "CAMERA_ACTIVE":
        colors = ["#141E2B", "#1E2D3D", "#2C4A6F"];
        duration = 15;
        break;
      case "ANALYZING":
        colors = ["#141E2B", "#FF6B35", "#1E3A5F"];
        duration = 5;
        break;
      case "RESULT":
        colors = ["#141E2B", "#1E3A5F", "#2C4A6F"];
        duration = 20;
        break;
    }

    return { colors, duration };
  }, [appState]);

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
