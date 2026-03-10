"use client";

import React from "react";

type CatVariant = "default" | "thinking" | "happy" | "error";

interface CatIconProps {
  variant?: CatVariant;
  size?: number;
  theme?: "light" | "dark";
  className?: string;
}

function Px({ x, y, c }: { x: number; y: number; c: string }) {
  return <rect x={x} y={y} width={1} height={1} fill={c} />;
}

function Run({ x, y, w, c }: { x: number; y: number; w: number; c: string }) {
  return <rect x={x} y={y} width={w} height={1} fill={c} />;
}

export default function CatIcon({
  variant = "default",
  size = 36,
  theme = "light",
  className = "",
}: CatIconProps) {
  const outline = theme === "light" ? "#1E3A5F" : "#F0F2F5";
  const fill = theme === "light" ? "#FFFFFF" : "#141E2B";
  const green = "#6B8B3E";
  const orange = "#FF6B35";
  const orangeLight = "#FF8A5B";
  const orangeDark = "#E55A2B";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      shapeRendering="crispEdges"
      className={className}
    >
      {/* === Ears === */}
      {variant === "error" ? (
        <>
          {/* Left ear drooped */}
          <Px x={2} y={2} c={outline} />
          <Px x={1} y={3} c={outline} />
          <Px x={1} y={4} c={outline} />
          {/* Right ear normal */}
          <Px x={11} y={1} c={outline} />
          <Px x={12} y={0} c={outline} />
          <Px x={12} y={1} c={fill} />
          <Px x={13} y={1} c={outline} />
        </>
      ) : (
        <>
          <Px x={2} y={1} c={outline} />
          <Px x={3} y={0} c={outline} />
          <Px x={3} y={1} c={fill} />
          <Px x={4} y={1} c={outline} />
          <Px x={11} y={1} c={outline} />
          <Px x={12} y={0} c={outline} />
          <Px x={12} y={1} c={fill} />
          <Px x={13} y={1} c={outline} />
        </>
      )}

      {/* === Head outline === */}
      <Px x={2} y={2} c={outline} />
      <Run x={3} y={2} w={10} c={outline} />
      <Px x={13} y={2} c={outline} />
      <rect x={2} y={3} width={1} height={8} fill={outline} />
      <rect x={13} y={3} width={1} height={8} fill={outline} />
      <Run x={3} y={11} w={10} c={outline} />

      {/* === Head fill === */}
      <rect x={3} y={3} width={10} height={8} fill={fill} />

      {/* === Eyes === */}
      {variant === "default" && (
        <>
          <rect x={5} y={5} width={2} height={2} fill={green} />
          <rect x={9} y={5} width={2} height={2} fill={green} />
        </>
      )}
      {variant === "thinking" && (
        <>
          <Run x={5} y={5} w={2} c={orange} />
          <Px x={5} y={6} c={orange} />
          <Px x={10} y={5} c={orange} />
          <Run x={9} y={6} w={2} c={orange} />
        </>
      )}
      {variant === "happy" && (
        <>
          <Px x={5} y={5} c={outline} />
          <Px x={6} y={6} c={outline} />
          <Px x={10} y={5} c={outline} />
          <Px x={9} y={6} c={outline} />
          <Run x={4} y={7} w={2} c={orangeLight} />
          <Run x={10} y={7} w={2} c={orangeLight} />
        </>
      )}
      {variant === "error" && (
        <>
          <Px x={5} y={5} c={orangeDark} />
          <Px x={6} y={6} c={orangeDark} />
          <Px x={6} y={5} c={orangeDark} />
          <Px x={5} y={6} c={orangeDark} />
          <Px x={9} y={5} c={orangeDark} />
          <Px x={10} y={6} c={orangeDark} />
          <Px x={10} y={5} c={orangeDark} />
          <Px x={9} y={6} c={orangeDark} />
        </>
      )}

      {/* === Nose === */}
      <Run x={7} y={7} w={2} c={outline} />
      <Run x={7} y={8} w={2} c={outline} />

      {/* === Mouth === */}
      {variant === "happy" ? (
        <Run x={6} y={9} w={4} c={outline} />
      ) : variant === "error" ? (
        <>
          <Px x={6} y={9} c={outline} />
          <Px x={7} y={10} c={outline} />
          <Px x={8} y={9} c={outline} />
          <Px x={9} y={10} c={outline} />
        </>
      ) : variant === "thinking" ? (
        <>
          <Px x={6} y={9} c={outline} />
          <Run x={7} y={10} w={2} c={outline} />
          <Px x={9} y={9} c={outline} />
        </>
      ) : (
        <>
          <Px x={6} y={9} c={outline} />
          <Px x={9} y={9} c={outline} />
        </>
      )}

      {/* === Whiskers === */}
      {variant === "error" ? (
        <>
          <Run x={0} y={7} w={2} c={outline} />
          <Run x={0} y={9} w={2} c={outline} />
          <Run x={14} y={7} w={2} c={outline} />
          <Run x={14} y={9} w={2} c={outline} />
        </>
      ) : (
        <>
          <Run x={0} y={6} w={2} c={outline} />
          <Run x={0} y={8} w={2} c={outline} />
          <Run x={14} y={6} w={2} c={outline} />
          <Run x={14} y={8} w={2} c={outline} />
        </>
      )}
    </svg>
  );
}
