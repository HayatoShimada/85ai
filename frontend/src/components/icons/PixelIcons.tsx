"use client";

import React from "react";

interface IconProps {
  size?: number;
  theme?: "light" | "dark";
  className?: string;
}

function Px({ x, y, c }: { x: number; y: number; c: string }) {
  return <rect x={x} y={y} width={1} height={1} fill={c} />;
}

function Rect({ x, y, w, h, c }: { x: number; y: number; w: number; h: number; c: string }) {
  return <rect x={x} y={y} width={w} height={h} fill={c} />;
}

function SvgBase({ size, className, children }: { size: number; className: string; children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" shapeRendering="crispEdges" className={className}>
      {children}
    </svg>
  );
}

export function CameraIcon({ size = 24, theme = "light", className = "" }: IconProps) {
  const o = theme === "light" ? "#1E3A5F" : "#F0F2F5";
  const f = theme === "light" ? "#FFFFFF" : "#141E2B";
  return (
    <SvgBase size={size} className={className}>
      <Rect x={1} y={4} w={14} h={9} c={o} />
      <Rect x={2} y={5} w={12} h={7} c={f} />
      <Rect x={5} y={2} w={4} h={2} c={o} />
      <Rect x={6} y={3} w={2} h={1} c={f} />
      <Rect x={11} y={3} w={2} h={1} c="#FF6B35" />
      <Rect x={6} y={6} w={4} h={4} c={o} />
      <Rect x={7} y={7} w={2} h={2} c="#FF6B35" />
      <Px x={7} y={7} c="#FF8A5B" />
    </SvgBase>
  );
}

export function FishIcon({ size = 24, theme = "light", className = "" }: IconProps) {
  const o = theme === "light" ? "#1E3A5F" : "#F0F2F5";
  const f = theme === "light" ? "#FFFFFF" : "#141E2B";
  return (
    <SvgBase size={size} className={className}>
      <Rect x={4} y={4} w={8} h={1} c={o} />
      <Rect x={3} y={5} w={9} h={6} c="#FF6B35" />
      <Rect x={2} y={6} w={1} h={4} c={o} />
      <Rect x={12} y={5} w={1} h={6} c={o} />
      <Px x={3} y={5} c={o} />
      <Px x={3} y={10} c={o} />
      <Rect x={4} y={11} w={8} h={1} c={o} />
      <Rect x={5} y={6} w={2} h={2} c={f} />
      <Px x={5} y={6} c={o} />
      <Px x={13} y={5} c={o} />
      <Px x={13} y={10} c={o} />
      <Rect x={14} y={4} w={1} h={2} c={o} />
      <Rect x={14} y={10} w={1} h={2} c={o} />
      <Px x={14} y={5} c="#FF8A5B" />
      <Px x={14} y={10} c="#FF8A5B" />
      <Rect x={15} y={3} w={1} h={2} c={o} />
      <Rect x={15} y={11} w={1} h={2} c={o} />
      <Rect x={7} y={3} w={2} h={1} c={o} />
      <Px x={7} y={3} c="#FF8A5B" />
    </SvgBase>
  );
}

export function PawIcon({ size = 24, theme = "light", className = "" }: IconProps) {
  const o = theme === "light" ? "#1E3A5F" : "#F0F2F5";
  const f = theme === "light" ? "#FFFFFF" : "#141E2B";
  return (
    <SvgBase size={size} className={className}>
      <Rect x={5} y={7} w={6} h={4} c={o} />
      <Rect x={6} y={11} w={4} h={2} c={o} />
      <Rect x={6} y={8} w={4} h={2} c={f} />
      <Rect x={3} y={4} w={2} h={3} c={o} />
      <Px x={3} y={5} c="#FF6B35" />
      <Rect x={6} y={3} w={2} h={3} c={o} />
      <Px x={6} y={4} c="#FF6B35" />
      <Rect x={9} y={3} w={2} h={3} c={o} />
      <Px x={9} y={4} c="#FF6B35" />
      <Rect x={12} y={4} w={2} h={3} c={o} />
      <Px x={12} y={5} c="#FF6B35" />
    </SvgBase>
  );
}

export function HangerIcon({ size = 24, theme = "light", className = "" }: IconProps) {
  const o = theme === "light" ? "#1E3A5F" : "#F0F2F5";
  return (
    <SvgBase size={size} className={className}>
      <Rect x={7} y={1} w={2} h={1} c={o} />
      <Rect x={9} y={2} w={1} h={2} c={o} />
      <Rect x={7} y={3} w={2} h={1} c={o} />
      <Rect x={7} y={4} w={2} h={2} c={o} />
      <Px x={6} y={7} c={o} />
      <Px x={5} y={8} c={o} />
      <Px x={4} y={9} c={o} />
      <Px x={8} y={6} c={o} />
      <Px x={9} y={7} c={o} />
      <Px x={10} y={8} c={o} />
      <Px x={11} y={9} c={o} />
      <Rect x={1} y={10} w={14} h={1} c={o} />
      <Rect x={1} y={11} w={14} h={1} c={o} />
    </SvgBase>
  );
}
