# UI Redesign: Warm Kare-Style Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current dark/futuristic UI with a warm, Susan Kare-inspired design using 85-store brand colors (Orange × Navy) and pixel art cat icons.

**Architecture:** Systematic color system replacement via Tailwind CSS v4 custom properties. New `CatIcon` and `PixelIcons` React components provide Kare-style SVG icons. iPad uses light theme, Projection uses dark theme with same brand palette. No logic/backend changes — purely visual.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS v4 (`@theme inline`), Framer Motion, inline SVG pixel art

**Spec:** `docs/superpowers/specs/2026-03-10-ui-redesign-warm-kare-style.md`

---

## Color Mapping Reference

Use this table when transforming any component. Every emerald/cyan/slate class maps to the new system:

| Old (Dark Futuristic) | New (iPad Light) | New (Projection Dark) |
|----------------------|-----------------|---------------------|
| `bg-slate-950` | `bg-bg` | `bg-[#141E2B]` |
| `bg-slate-900` | `bg-card` or `bg-[#F5F6F7]` | `bg-[#1E2D3D]` |
| `bg-slate-800` | `bg-card` | `bg-[#1E2D3D]` |
| `bg-slate-800/60` | `bg-card/60` | `bg-[#1E2D3D]/60` |
| `bg-black` | `bg-card` | `bg-[#141E2B]` |
| `bg-black/40` | `bg-card/40` | `bg-[#141E2B]/40` |
| `bg-black/50` | — | `bg-[#141E2B]/70` |
| `bg-black/60` | `bg-navy/60` | `bg-[#141E2B]/60` |
| `bg-black/70` | `bg-navy/70` | — |
| `border-slate-700` | `border-border` | `border-[#2A3D50]` |
| `border-slate-700/50` | `border-border` | `border-[#2A3D50]` |
| `border-slate-800` | `border-border` | `border-[#2A3D50]` |
| `border-slate-600/50` | `border-border` | `border-[#2A3D50]` |
| `text-slate-100` | `text-text` | `text-[#F0F2F5]` |
| `text-slate-200` | `text-text` | `text-[#F0F2F5]` |
| `text-slate-300` | `text-text-body` | `text-[#8A9AAD]` |
| `text-slate-400` | `text-text-muted` | `text-[#6B7B8D]` |
| `text-slate-500` | `text-text-muted` | `text-[#6B7B8D]` |
| `text-white` | `text-white` (on CTAs) | `text-[#F0F2F5]` |
| `bg-emerald-500` | `bg-primary` | `bg-primary` |
| `bg-emerald-500/20` | `bg-primary/20` | `bg-primary/20` |
| `bg-emerald-500/10` | `bg-primary/10` | `bg-primary/10` |
| `bg-emerald-400` | `bg-primary` | `bg-primary` |
| `text-emerald-400` | `text-primary` | `text-primary` |
| `text-emerald-300` | `text-primary-light` | `text-primary-light` |
| `text-emerald-500` | `text-primary` | `text-primary` |
| `border-emerald-500` | `border-primary` | `border-primary` |
| `border-emerald-500/50` | `border-primary/50` | `border-primary/50` |
| `border-emerald-400` | `border-primary` | `border-primary` |
| `ring-emerald-500` | `ring-primary` | `ring-primary` |
| `focus:ring-emerald-500` | `focus:ring-primary` | `focus:ring-primary` |
| `selection:bg-emerald-500/30` | `selection:bg-primary/30` | — |
| `shadow-[*rgba(16,185,129,*)]` | `shadow-[*rgba(255,107,53,*)]` | `shadow-[*rgba(255,107,53,*)]` |
| `text-cyan-400` | `text-navy-light` | `text-[#8A9AAD]` |
| `text-cyan-300` | `text-navy-light` | `text-[#8A9AAD]` |
| `bg-cyan-500/20` | `bg-navy-light/20` | `bg-[#2C4A6F]/20` |
| `bg-cyan-500/10` | `bg-navy-light/10` | `bg-[#2C4A6F]/10` |
| `border-cyan-500/50` | `border-navy-light/50` | `border-[#2C4A6F]/50` |
| `border-cyan-400/50` | `border-navy-light/50` | `border-[#2C4A6F]/50` |
| `bg-violet-500/10` | `bg-navy/10` | — |
| `bg-violet-500` | `bg-navy` | — |
| `border-violet-500/40` | `border-navy/40` | — |
| `text-red-400` | `text-primary-dark` | `text-primary-dark` |
| `bg-red-500/10` | `bg-[#FFF5F0]` | `bg-primary-dark/10` |
| `border-red-500/20` | `border-primary-dark/20` | `border-primary-dark/20` |
| `text-amber-400` | `text-primary-light` | `text-primary-light` |

---

## Chunk 1: Foundation

### Task 1: CSS Color System

**Files:**
- Modify: `frontend/src/app/globals.css`

- [ ] **Step 1: Replace globals.css with new color system**

```css
@import "tailwindcss";

:root {
  /* Brand */
  --color-primary: #FF6B35;
  --color-primary-light: #FF8A5B;
  --color-primary-dark: #E55A2B;
  --color-navy: #1E3A5F;
  --color-navy-light: #2C4A6F;
  --color-charcoal: #36454F;
  --color-icon-green: #6B8B3E;

  /* iPad (Light) */
  --color-bg: #FAFBFC;
  --color-card: #FFFFFF;
  --color-border: #E8EAED;
  --color-text: #1E3A5F;
  --color-text-body: #4A5A66;
  --color-text-muted: #8A949E;
}

@theme inline {
  --color-primary: var(--color-primary);
  --color-primary-light: var(--color-primary-light);
  --color-primary-dark: var(--color-primary-dark);
  --color-navy: var(--color-navy);
  --color-navy-light: var(--color-navy-light);
  --color-charcoal: var(--color-charcoal);
  --color-icon-green: var(--color-icon-green);
  --color-bg: var(--color-bg);
  --color-card: var(--color-card);
  --color-border: var(--color-border);
  --color-text: var(--color-text);
  --color-text-body: var(--color-text-body);
  --color-text-muted: var(--color-text-muted);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

body {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans), Arial, Helvetica, sans-serif;
}
```

- [ ] **Step 2: Verify build succeeds**

Run: `cd frontend && npm run build`
Expected: Build succeeds. New CSS variables are registered in Tailwind theme.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/globals.css
git commit -m "feat(ui): replace CSS color system with 85-store brand palette"
```

---

### Task 2: CatIcon Component

**Files:**
- Create: `frontend/src/components/icons/CatIcon.tsx`

- [ ] **Step 1: Create icons directory and CatIcon component**

The directory `frontend/src/components/icons/` does not exist yet. Create it, then create the component:

```tsx
"use client";

import React from "react";

type CatVariant = "default" | "thinking" | "happy" | "error";

interface CatIconProps {
  variant?: CatVariant;
  size?: number;
  theme?: "light" | "dark";
  className?: string;
}

// Shared pixel: helper to place a 1x1 rect in the 16x16 grid
function Px({ x, y, c }: { x: number; y: number; c: string }) {
  return <rect x={x} y={y} width={1} height={1} fill={c} />;
}

// Multi-pixel horizontal run
function Run({ x, y, w, c }: { x: number; y: number; w: number; c: string }) {
  return <rect x={x} y={y} width={w} height={1} fill={c} />;
}

// Multi-pixel vertical run
function Col({ x, y, h, c }: { x: number; y: number; h: number; c: string }) {
  return <rect x={x} y={y} width={1} height={h} fill={c} />;
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
          {/* Left ear */}
          <Px x={2} y={1} c={outline} />
          <Px x={3} y={0} c={outline} />
          <Px x={3} y={1} c={fill} />
          <Px x={4} y={1} c={outline} />
          {/* Right ear */}
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
      <Col x={2} y={3} h={8} c={outline} />
      <Col x={13} y={3} h={8} c={outline} />
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
          {/* Spiral left eye */}
          <Run x={5} y={5} w={2} c={orange} />
          <Px x={5} y={6} c={orange} />
          {/* Spiral right eye */}
          <Px x={10} y={5} c={orange} />
          <Run x={9} y={6} w={2} c={orange} />
        </>
      )}
      {variant === "happy" && (
        <>
          {/* ^_^ left */}
          <Px x={5} y={5} c={outline} />
          <Px x={6} y={6} c={outline} />
          {/* ^_^ right */}
          <Px x={10} y={5} c={outline} />
          <Px x={9} y={6} c={outline} />
          {/* Blush */}
          <Run x={4} y={7} w={2} c={orangeLight} />
          <Run x={10} y={7} w={2} c={orangeLight} />
        </>
      )}
      {variant === "error" && (
        <>
          {/* X left */}
          <Px x={5} y={5} c={orangeDark} />
          <Px x={6} y={6} c={orangeDark} />
          <Px x={6} y={5} c={orangeDark} />
          <Px x={5} y={6} c={orangeDark} />
          {/* X right */}
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
```

- [ ] **Step 2: Verify build succeeds**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/icons/CatIcon.tsx
git commit -m "feat(ui): add CatIcon component with Kare-style pixel art variants"
```

---

### Task 3: Pixel Functional Icons

**Files:**
- Create: `frontend/src/components/icons/PixelIcons.tsx`

- [ ] **Step 1: Create PixelIcons component**

```tsx
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

function Rect({
  x, y, w, h, c,
}: {
  x: number; y: number; w: number; h: number; c: string;
}) {
  return <rect x={x} y={y} width={w} height={h} fill={c} />;
}

function SvgBase({
  size, className, children,
}: {
  size: number; className: string; children: React.ReactNode;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      shapeRendering="crispEdges"
      className={className}
    >
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
      {/* Body outline + fill */}
      <Rect x={4} y={4} w={8} h={1} c={o} />
      <Rect x={3} y={5} w={9} h={6} c="#FF6B35" />
      <Px x={2} y={6} c={o} />
      <Rect x={2} y={6} w={1} h={4} c={o} />
      <Rect x={12} y={5} w={1} h={6} c={o} />
      <Px x={3} y={5} c={o} />
      <Px x={3} y={10} c={o} />
      <Rect x={4} y={11} w={8} h={1} c={o} />
      {/* Eye */}
      <Rect x={5} y={6} w={2} h={2} c={f} />
      <Px x={5} y={6} c={o} />
      {/* Tail */}
      <Px x={13} y={5} c={o} />
      <Px x={13} y={10} c={o} />
      <Rect x={14} y={4} w={1} h={2} c={o} />
      <Rect x={14} y={10} w={1} h={2} c={o} />
      <Px x={14} y={5} c="#FF8A5B" />
      <Px x={14} y={10} c="#FF8A5B" />
      <Rect x={15} y={3} w={1} h={2} c={o} />
      <Rect x={15} y={11} w={1} h={2} c={o} />
      {/* Fin */}
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
      {/* Main pad */}
      <Rect x={5} y={7} w={6} h={4} c={o} />
      <Rect x={6} y={11} w={4} h={2} c={o} />
      <Rect x={6} y={8} w={4} h={2} c={f} />
      {/* Toe beans */}
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
      {/* Hook */}
      <Rect x={7} y={1} w={2} h={1} c={o} />
      <Rect x={9} y={2} w={1} h={2} c={o} />
      <Rect x={7} y={3} w={2} h={1} c={o} />
      <Rect x={7} y={4} w={2} h={2} c={o} />
      {/* Arms */}
      <Px x={6} y={7} c={o} />
      <Px x={5} y={8} c={o} />
      <Px x={4} y={9} c={o} />
      <Px x={8} y={6} c={o} />
      <Px x={9} y={7} c={o} />
      <Px x={10} y={8} c={o} />
      <Px x={11} y={9} c={o} />
      {/* Bar */}
      <Rect x={1} y={10} w={14} h={1} c={o} />
      <Rect x={1} y={11} w={14} h={1} c={o} />
    </SvgBase>
  );
}
```

- [ ] **Step 2: Verify build succeeds**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/icons/PixelIcons.tsx
git commit -m "feat(ui): add pixel art functional icons (Camera, Fish, Paw, Hanger)"
```

---

### Task 4: Page Container Updates

**Files:**
- Modify: `frontend/src/app/page.tsx:241`
- Modify: `frontend/src/app/projection/page.tsx:93`

- [ ] **Step 1: Update iPad page container**

In `frontend/src/app/page.tsx`, change the `<main>` className:

```
Before: className="min-h-screen bg-slate-950 font-sans selection:bg-emerald-500/30 text-slate-200"
After:  className="min-h-screen bg-bg font-sans selection:bg-primary/30 text-text"
```

- [ ] **Step 2: Update Projection page container**

In `frontend/src/app/projection/page.tsx`, change the `<main>` className:

```
Before: className="w-screen h-screen overflow-hidden bg-black text-slate-100 font-sans cursor-none relative"
After:  className="w-screen h-screen overflow-hidden bg-[#141E2B] text-[#F0F2F5] font-sans cursor-none relative"
```

- [ ] **Step 3: Verify build succeeds**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/page.tsx frontend/src/app/projection/page.tsx
git commit -m "feat(ui): update page containers with new color system"
```

---

## Chunk 2: Operator Components (iPad Light Theme)

### Task 5: IdleView — Rebrand + Retheme

**Files:**
- Modify: `frontend/src/components/operator/IdleView.tsx`

- [ ] **Step 1: Rewrite IdleView**

Replace the entire component. Remove the emerald icon badge, gradient title "VINTAGE.AI", and cyan accents. Replace with:

- **85 Logo**: 80×80 navy rounded box with orange "85" text
- **CatIcon**: Default variant below logo
- **Title**: "85 STORE" in navy, `text-5xl font-black tracking-wider`
- **Subtitle**: "あなたに合う一着を一緒に探しましょう" in `text-text-body`
- **CTA**: Orange primary button "はじめる"
- **Secondary**: "プロジェクション表示を開く →" in `text-text-muted`

Key class changes:
- Remove: `bg-emerald-500/20`, `shadow-[0_0_30px_rgba(16,185,129,0.3)]`, `from-emerald-400 to-cyan-400`
- Add: `bg-navy`, `text-primary` for "85", CatIcon default

Imports to add:
```tsx
import CatIcon from "@/components/icons/CatIcon";
```

Icon badge replacement:
```tsx
// Before: emerald rounded-3xl with sparkles icon
// After:
<div className="w-20 h-20 bg-navy rounded-3xl flex items-center justify-center shadow-lg">
  <span className="text-primary text-3xl font-extrabold">85</span>
</div>
<CatIcon variant="default" size={48} className="mt-4" />
```

Title replacement:
```tsx
// Before: <h1 className="text-5xl font-black bg-gradient-to-r from-emerald-400 to-cyan-400 text-transparent bg-clip-text">VINTAGE.AI</h1>
// After:
<h1 className="text-5xl font-black text-navy tracking-wider">85 STORE</h1>
```

Button replacement:
```tsx
// Before: bg-emerald-500 hover:bg-emerald-600 shadow-[0_0_20px_rgba(16,185,129,0.3)]
// After:
className="bg-primary hover:bg-primary-dark text-white px-12 py-4 rounded-2xl text-xl font-bold shadow-[0_0_20px_rgba(255,107,53,0.3)] transition-colors"
```

Secondary link:
```tsx
// Before: text-slate-400 hover:text-slate-300
// After: text-text-muted hover:text-text-body
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Visual verification**

Run: `cd frontend && npm run dev`
Open http://localhost:3000 — verify light background, navy title, orange CTA, cat icon visible.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/operator/IdleView.tsx
git commit -m "feat(ui): retheme IdleView with 85-store branding and CatIcon"
```

---

### Task 6: PreferenceView — Retheme

**Files:**
- Modify: `frontend/src/components/operator/PreferenceView.tsx`

This is the largest operator component (~490 lines). Apply the color mapping systematically:

- [ ] **Step 1: Update imports**

Add at top:
```tsx
import CatIcon from "@/components/icons/CatIcon";
```

- [ ] **Step 2: Replace all color classes**

Apply the Color Mapping Reference table. Key replacements throughout the file:

**Input fields** (appears ~8 times):
```
Before: bg-slate-900 border-slate-700 text-slate-100 focus:ring-emerald-500 placeholder:text-slate-500
After:  bg-white border-border text-text focus:ring-primary focus:ring-2 placeholder:text-text-muted
```

**Checkboxes**:
```
Before: accent-emerald-500
After:  accent-primary
```

**Style tags (selected)**:
```
Before: bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]
After:  bg-primary/15 text-primary border-primary/50 shadow-[0_0_10px_rgba(255,107,53,0.15)]
```

**Style tags (unselected)**:
```
Before: bg-slate-800 text-slate-300 border-slate-600
After:  bg-[#F5F6F7] text-text-body border-border
```

**Section headers** (text-slate-300 → text-text, text-slate-400 → text-text-muted):
Apply throughout.

**Body measurement inputs**:
```
Before: bg-slate-900 border-slate-700 text-slate-100 focus:ring-emerald-500
After:  bg-white border-border text-text focus:ring-primary focus:ring-2
```

**Proceed button (primary CTA)**:
```
Before: bg-emerald-500 hover:bg-emerald-600 text-white disabled:opacity-40
After:  bg-primary hover:bg-primary-dark text-white disabled:opacity-40 shadow-[0_0_12px_rgba(255,107,53,0.3)]
```

**Secondary buttons**:
```
Before: bg-slate-800 text-slate-300 hover:bg-slate-700
After:  bg-white text-text border border-border hover:bg-[#F5F6F7]
```

**Privacy modal**:
```
Before: bg-black/60 backdrop-blur-sm → bg-slate-800 border-slate-700 text-slate-100
After:  bg-navy/60 backdrop-blur-sm → bg-white border-border text-text
```

**Skip links**:
```
Before: text-slate-500 hover:text-slate-400
After:  text-text-muted hover:text-text-body
```

**Card backgrounds**:
```
Before: bg-slate-900 border-slate-700
After:  bg-card border-border shadow-[0_0_3px_rgba(30,58,95,0.06)]
```

**Step indicator icons** (emerald → primary):
```
Before: bg-emerald-500, text-emerald-400
After:  bg-primary, text-primary
```

- [ ] **Step 3: Add CatIcon to Step 1 header**

Before the greeting text, add a small CatIcon:

```tsx
<div className="flex items-center gap-3 mb-4">
  <CatIcon variant="default" size={32} />
  <h2 className="text-lg font-bold text-text">こんにちは！</h2>
</div>
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/operator/PreferenceView.tsx
git commit -m "feat(ui): retheme PreferenceView with light theme and orange/navy palette"
```

---

### Task 7: CameraView — Retheme

**Files:**
- Modify: `frontend/src/components/operator/CameraView.tsx`

- [ ] **Step 1: Replace color classes**

**Video container**:
```
Before: bg-black border-4 border-slate-800
After:  bg-[#F0F4F8] border-4 border-border
```

**Corner brackets**:
```
Before: border-emerald-500/50
After:  border-primary/50
```

**Center guide**:
```
Before: border-emerald-500/30
After:  border-primary/30
```

**"FIT PERSON IN FRAME" text**:
```
Before: text-emerald-400 bg-slate-900/80
After:  text-primary bg-white/80
```

**Scanning ring**:
```
Before: border-emerald-500/40
After:  border-primary/40
```

**Capture button**:
```
Before: bg-emerald-500 ring-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.4)]
After:  bg-primary ring-primary/30 shadow-[0_0_30px_rgba(255,107,53,0.4)]
```

**Status text**:
```
Before: bg-slate-900/80 text-emerald-400
After:  bg-white/80 text-primary
```

**Outer container** (line 27):
```
Before: bg-slate-900
After:  bg-bg
```

**Countdown overlay** (line 57):
```
Before: bg-slate-900/40 backdrop-blur-md
After:  bg-white/40 backdrop-blur-md
```

**Cancel button**:
```
Before: bg-slate-800 text-slate-300
After:  bg-white text-text border border-border
```

**Countdown number**:
```
Before: text-emerald-400
After:  text-primary
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/operator/CameraView.tsx
git commit -m "feat(ui): retheme CameraView with light theme and orange accents"
```

---

### Task 8: AnalyzingView — Retheme + Replace Animations

**Files:**
- Modify: `frontend/src/components/operator/AnalyzingView.tsx`

This view needs the most structural change: remove scanning line + rotating ring, add CatIcon.

- [ ] **Step 1: Update imports**

```tsx
import CatIcon from "@/components/icons/CatIcon";
```

Remove `motion` usage for the scan line and rotating ring (but keep the container's entry/exit animation).

- [ ] **Step 2: Replace the image + animation section**

Before (scanning line + rotating ring around image):
```tsx
// Remove: motion.div for scanning line (animate top 0% → 100%)
// Remove: motion.div for rotating dashed ring (animate rotate 360)
// Remove: bg-emerald-500/20 mix-blend-overlay on image
```

After — replace with CatIcon + simple text:
```tsx
{analyzedImage ? (
  <div className="relative w-64 h-64 rounded-3xl overflow-hidden shadow-lg bg-card border border-border">
    <img src={analyzedImage} alt="Captured" className="w-full h-full object-cover" />
  </div>
) : null}

<div className="flex flex-col items-center gap-4 mt-6">
  <CatIcon variant="thinking" size={64} />
  <p className="text-xl font-bold text-text">スタイルを解析中</p>
  <motion.p
    className="text-text-muted text-sm"
    animate={{ opacity: [0.4, 1, 0.4] }}
    transition={{ duration: 2, repeat: Infinity }}
  >
    もうちょっと待ってね...
  </motion.p>
</div>
```

- [ ] **Step 3: Replace error state**

Error container:
```
Before: bg-red-500/10 border border-red-500/20
After:  bg-[#FFF5F0] border-l-[3px] border-l-primary border border-primary-dark/20
```

Error text:
```
Before: text-red-400
After:  text-primary-dark
```

Add CatIcon error before the alert icon:
```tsx
<CatIcon variant="error" size={48} className="mb-3" />
<p className="text-primary-dark font-bold">うまくいかなかったみたい...</p>
```

Error buttons (BOTH are `bg-slate-800` in current code):
```
Before: bg-slate-800 hover:bg-slate-700 text-slate-200 (retry button)
After:  bg-primary hover:bg-primary-dark text-white (retry button)

Before: bg-slate-800 hover:bg-slate-700 text-slate-200 (back button)
After:  bg-white hover:bg-[#F5F6F7] text-text border border-border (back button)
```

- [ ] **Step 4: Replace timeout state**

```
Before: bg-slate-800/80 border-slate-700 text-slate-300
After:  bg-card border-border text-text-body
```

Timeout buttons: same pattern as error buttons.

- [ ] **Step 5: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/operator/AnalyzingView.tsx
git commit -m "feat(ui): retheme AnalyzingView with CatIcon thinking state, remove futuristic animations"
```

---

### Task 9: ResultView — Retheme

**Files:**
- Modify: `frontend/src/components/operator/ResultView.tsx`

This is the most complex operator component. Key changes:

- [ ] **Step 1: Update imports**

```tsx
import CatIcon from "@/components/icons/CatIcon";
import { FishIcon } from "@/components/icons/PixelIcons";
```

- [ ] **Step 2: Replace card color rotation**

The variable is named `colors` (not `cardThemes`), with properties `accent`, `bg`, `border`, `badge`, `text`:

Before (line 27-31 of ResultView.tsx):
```tsx
const colors = [
  { accent: "emerald", bg: "bg-emerald-500/10", border: "border-emerald-500/40", badge: "bg-emerald-500", text: "text-emerald-400" },
  { accent: "cyan",    bg: "bg-cyan-500/10",    border: "border-cyan-500/40",    badge: "bg-cyan-500",    text: "text-cyan-400" },
  { accent: "violet",  bg: "bg-violet-500/10",  border: "border-violet-500/40",  badge: "bg-violet-500",  text: "text-violet-400" },
][index] || { accent: "emerald", bg: "bg-emerald-500/10", border: "border-emerald-500/40", badge: "bg-emerald-500", text: "text-emerald-400" };
```

After (orange/navy rotation):
```tsx
const colors = [
  { accent: "primary",    bg: "bg-primary/10",    border: "border-primary/40",    badge: "bg-primary",    text: "text-primary" },
  { accent: "navy",       bg: "bg-navy/10",       border: "border-navy/40",       badge: "bg-navy",       text: "text-navy" },
  { accent: "navy-light", bg: "bg-navy-light/10", border: "border-navy-light/40", badge: "bg-navy-light", text: "text-navy-light" },
][index] || { accent: "primary", bg: "bg-primary/10", border: "border-primary/40", badge: "bg-primary", text: "text-primary" };
```

- [ ] **Step 3: Replace heading gradient**

```
Before: bg-gradient-to-r from-emerald-400 to-cyan-400 text-transparent bg-clip-text
After:  text-navy (plain, no gradient)
```

- [ ] **Step 4: Add FishIcon to recommendation headers**

In the recommendation card header, before the title:
```tsx
<FishIcon size={18} className="flex-shrink-0" />
```

- [ ] **Step 5: Replace tag styling**

Detected tags:
```
Before: bg-cyan-500/10 text-cyan-400
After:  bg-navy-light/10 text-navy-light
```

Selected tags:
```
Before: bg-emerald-500/10 text-emerald-400
After:  bg-primary/10 text-primary
```

- [ ] **Step 6: Replace remaining slate classes**

Apply Color Mapping Reference throughout:
- `bg-slate-900/40` → `bg-[#F5F6F7]`
- `border-slate-700/50` → `border-border`
- `bg-slate-800/60 backdrop-blur` → `bg-card/80`
- `text-slate-100` → `text-text`
- `text-slate-300` → `text-text-body`
- `bg-slate-800` → `bg-[#F5F6F7]`

Product card image container:
```
Before: bg-black
After:  bg-[#F0F4F8]
```

Price text:
```
Before: text-emerald-400
After:  text-primary
```

- [ ] **Step 7: Replace warning message and no-recommendation fallback**

Warning message (AI Hint Box pattern with left border):
```
Before: (any amber/yellow warning styling)
After:  bg-[#FFF5F0] border-l-[3px] border-l-primary rounded-xl p-3 text-primary-dark text-sm
```

No-recommendation fallback (around lines 125-134):
```
Before: text-red-400 + bg-slate-800 styling
After:  Use CatIcon error + text-primary-dark + bg-[#FFF5F0] border-l-[3px] border-l-primary
```

- [ ] **Step 8: Add CatIcon happy to header**

```tsx
<div className="flex items-center gap-3">
  <CatIcon variant="happy" size={36} />
  <h2 className="text-2xl font-bold text-navy">おすすめコーデ</h2>
</div>
```

- [ ] **Step 9: Reset button**

```
Before: bg-slate-800 text-slate-300
After:  bg-white text-text border border-border
```

- [ ] **Step 10: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add frontend/src/components/operator/ResultView.tsx
git commit -m "feat(ui): retheme ResultView with orange/navy cards, FishIcon, CatIcon"
```

---

## Chunk 3: Projection Components (Dark Theme)

### Task 10: ProjectionBackground — Retheme Gradients

**Files:**
- Modify: `frontend/src/components/projection/ProjectionBackground.tsx`

- [ ] **Step 1: Replace all gradient color arrays**

The code uses **3-element** arrays (`colors[0]`, `colors[1]`, `colors[2]`) at lines 22-53 of ProjectionBackground.tsx. The animation template at lines 63-66 constructs 3 gradient steps from these 3 elements. Keep 3-element arrays:

**IDLE** (line 27):
```
Before: ["#020617", "#065f46", "#0e7490"]
After:  ["#141E2B", "#1E2D3D", "#1E3A5F"]
```

**PREFERENCE** (line 31):
```
Before: ["#1e1b4b", "#312e81", "#4c1d95"]
After:  ["#141E2B", "#2C4A6F", "#1E3A5F"]
```

**CAMERA_ACTIVE** (line 35):
```
Before: ["#0a0a0a", "#022c22", "#064e3b"]
After:  ["#141E2B", "#1E2D3D", "#2C4A6F"]
```

**ANALYZING** (line 39):
```
Before: ["#0f172a", "#059669", "#7c3aed"]
After:  ["#141E2B", "#FF6B35", "#1E3A5F"]
```
(Keep shorter duration — 5s — for analyzing state visual feedback)

**Default** (line 22):
```
Before: ["#0f172a", "#10b981", "#06b6d4"]
After:  ["#141E2B", "#1E3A5F", "#2C4A6F"]
```

**RESULT** (lines 43-50): Simplify to a single navy-themed gradient. Remove the tag-dependent if/else:
```
Before: 3 different tag-dependent color arrays
After:  colors = ["#141E2B", "#1E3A5F", "#2C4A6F"]
```

- [ ] **Step 2: Keep SVG noise overlay**

The `feTurbulence` noise filter stays unchanged — it adds good texture.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/projection/ProjectionBackground.tsx
git commit -m "feat(ui): retheme ProjectionBackground with navy gradient palette"
```

---

### Task 11: ProjectionScenes — Retheme 4 Scenes

**Files:**
- Modify: `frontend/src/components/projection/ProjectionScenes.tsx`

This file contains: ProjectionIdleScene, ProjectionPreferenceScene, ProjectionCameraScene, ProjectionAnalyzingScene, MirrorOverlay.

- [ ] **Step 1: Update imports**

```tsx
import CatIcon from "@/components/icons/CatIcon";
```

- [ ] **Step 2: Retheme ProjectionIdleScene**

Title:
```
Before: text-8xl font-black bg-gradient-to-r from-emerald-400 to-cyan-400 text-transparent bg-clip-text
        "VINTAGE.AI"
After:  Use 85 logo + text:
```

Replace the title section with:
```tsx
<div className="flex items-center gap-6 mb-6">
  <div className="w-24 h-24 bg-primary rounded-3xl flex items-center justify-center shadow-lg">
    <span className="text-[#141E2B] text-4xl font-extrabold">85</span>
  </div>
  <span className="text-6xl font-black text-primary-light tracking-[0.15em]">STORE</span>
</div>
<CatIcon variant="default" size={80} theme="dark" />
```

Icon badge:
```
Before: bg-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.3)] with Sparkles icon
After:  Remove entirely (replaced by 85 logo above)
```

Subtitle:
```
Before: text-3xl text-slate-300
After:  text-3xl text-[#8A9AAD] font-light
```

Particles: **Remove** the 12-particle system entirely. Replace with a simple gentle pulse on the CatIcon.

- [ ] **Step 3: Retheme ProjectionPreferenceScene**

Header text:
```
Before: text-slate-300
After:  text-[#8A9AAD]
```

User name:
```
Before: text-emerald-400 drop-shadow-lg
After:  text-primary drop-shadow-lg
```

Tags:
```
Before: border-emerald-500/50 bg-emerald-500/10 text-emerald-300 shadow-[0_0_20px_rgba(16,185,129,0.2)]
After:  border-primary/50 bg-primary/10 text-primary-light shadow-[0_0_15px_rgba(255,107,53,0.2)]
```

Add CatIcon thinking (small) next to header.

- [ ] **Step 4: Retheme ProjectionCameraScene**

Grid lines:
```
Before: bg-emerald-500/30 shadow-[0_0_5px_rgba(16,185,129,0.5)]
After:  bg-primary/30 shadow-[0_0_5px_rgba(255,107,53,0.3)]
```

STANDBY text:
```
Before: text-emerald-400
After:  text-primary
```

Scan line:
```
Before: bg-emerald-500/40 shadow-[0_0_40px_rgba(16,185,129,1)]
After:  bg-primary/40 shadow-[0_0_40px_rgba(255,107,53,0.8)]
```

Tag badges:
```
Before: border-cyan-500/50 bg-cyan-500/10 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.3)]
After:  border-[#2A3D50] bg-[#1E2D3D] text-[#8A9AAD] shadow-none
```

- [ ] **Step 5: Retheme ProjectionAnalyzingScene**

Image border:
```
Before: border-emerald-500/50 shadow-[0_0_50px_rgba(16,185,129,0.2)]
After:  border-primary/50 shadow-[0_0_30px_rgba(255,107,53,0.2)]
```

Overlay on image:
```
Before: bg-emerald-500/10
After:  Remove overlay entirely (keep image clean)
```

Text:
```
Before: text-emerald-400 bg-black/50 backdrop-blur-md
After:  text-[#F0F2F5] bg-[#141E2B]/70
```

Timeout text:
```
Before: text-amber-400
After:  text-primary-light
```

**Remove** the two decorative rotating rings entirely. Replace with CatIcon thinking (large):
```tsx
<CatIcon variant="thinking" size={96} theme="dark" className="mb-6" />
```

Scan line on image: **Keep** (only iPad AnalyzingView scan line is removed per spec; projection keeps a subtle re-colored version for visual feedback on the captured image):
```
Before: emerald-400 shadow with emerald glow
After:  primary shadow with orange glow
```

- [ ] **Step 6: MirrorOverlay — No changes**

`mix-blend-screen` + `opacity-80` works correctly on `#141E2B` backgrounds. Leave unchanged.

- [ ] **Step 7: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/projection/ProjectionScenes.tsx
git commit -m "feat(ui): retheme ProjectionScenes with 85-store branding and CatIcon"
```

---

### Task 12: ProjectionResultScene — Retheme

**Files:**
- Modify: `frontend/src/components/projection/ProjectionResultScene.tsx`

- [ ] **Step 1: Update imports**

```tsx
import CatIcon from "@/components/icons/CatIcon";
import { FishIcon } from "@/components/icons/PixelIcons";
```

- [ ] **Step 2: Top section (analysis summary)**

Container:
```
Before: bg-black/40 backdrop-blur-md border border-slate-700/50
After:  bg-[#1E2D3D]/60 backdrop-blur-md border border-[#2A3D50]
```

Image container:
```
Before: bg-black border border-slate-700
After:  bg-[#141E2B] border border-[#2A3D50]
```

Bounding box:
```
Before: border-emerald-400 bg-emerald-400/20
After:  border-primary bg-primary/20
```

Bounding box label:
```
Before: bg-emerald-500 text-white
After:  bg-primary text-white
```

Title:
```
Before: bg-gradient-to-r from-emerald-400 to-cyan-400 text-transparent bg-clip-text
After:  text-[#F0F2F5] (plain)
```

Description:
```
Before: text-slate-200
After:  text-[#8A9AAD]
```

Tags:
```
Before (detected): bg-cyan-500/20 border-cyan-400/50 text-cyan-300
After:  bg-[#2C4A6F]/20 border-[#2C4A6F]/50 text-[#8A9AAD]

Before (selected): bg-emerald-500/20 border-emerald-400/50 text-emerald-300
After:  bg-primary/20 border-primary/50 text-primary-light
```

Add CatIcon happy:
```tsx
<CatIcon variant="happy" size={48} theme="dark" className="flex-shrink-0" />
```

- [ ] **Step 3: Recommendation cards**

Container:
```
Before: bg-black/60 border border-slate-700/50 backdrop-blur-xl
After:  bg-[#1E2D3D] border border-[#2A3D50]
```

Add FishIcon before "RECOMMENDATION" label.

Title:
```
Before: text-slate-100
After:  text-[#F0F2F5]
```

Category badge:
```
Before: bg-emerald-500 (assumed, or color rotation)
After:  bg-primary text-white
```

Description:
```
Before: text-slate-300
After:  text-[#8A9AAD]
```

Product items:
```
Before: bg-slate-800 border-slate-600/50
After:  bg-[#141E2B] border-[#2A3D50]
```

Product gradient overlay:
```
Before: from-black/90 via-black/40
After:  from-[#141E2B]/90 via-[#141E2B]/40
```

Price:
```
Before: text-emerald-400
After:  text-primary
```

QR code container: Keep `bg-white` (QR codes need white background).

"NO ITEM" fallback (around line 136):
```
Before: text-slate-500 bg-slate-900/50 border-dashed border-slate-700
After:  text-[#6B7B8D] bg-[#1E2D3D]/50 border-dashed border-[#2A3D50]
```

Category badge on recommendation cards (around line 97):
```
Before: bg-emerald-500/20 text-emerald-400 border-emerald-500/30
After:  bg-primary/20 text-primary border-primary/30
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/projection/ProjectionResultScene.tsx
git commit -m "feat(ui): retheme ProjectionResultScene with navy dark palette and pixel icons"
```

---

## Chunk 4: Polish & Verification

### Task 13: QRCode + Final Cleanup

**Files:**
- Modify: `frontend/src/components/QRCode.tsx`

- [ ] **Step 1: Update QRCode button**

```
Before: bg-slate-700 hover:bg-slate-600 text-white
After:  bg-navy hover:bg-navy-light text-white
```

- [ ] **Step 2: Update QRCode modal backdrop and internal text**

```
Before: bg-black/70 backdrop-blur-sm
After:  bg-navy/70 backdrop-blur-sm
```

Modal internal text colors:
```
Before: text-slate-800 (title)
After:  text-navy (title)

Before: text-slate-400, text-slate-500 (description, close)
After:  text-text-muted (description, close)
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/QRCode.tsx
git commit -m "feat(ui): retheme QRCode component"
```

---

### Task 14: Full Build + Visual Verification

- [ ] **Step 1: Clean build**

Run: `cd frontend && rm -rf .next && npm run build`
Expected: Build succeeds with no errors or warnings about unknown Tailwind classes.

- [ ] **Step 2: Run lint**

Run: `cd frontend && npm run lint`
Expected: No errors.

- [ ] **Step 3: Run backend tests (regression)**

Run: `cd backend && pytest tests/ -v`
Expected: All tests pass (no backend changes, but verify nothing broke).

- [ ] **Step 4: Visual verification checklist**

Start the app:
```bash
docker compose up --build
```

Verify each state in browser:

**iPad (http://localhost:3000):**
- [ ] IDLE: Light bg (#FAFBFC), 85 logo, "85 STORE", cat icon, orange CTA
- [ ] PREFERENCE Step 1: White card, navy text, orange accents, cat greeting
- [ ] PREFERENCE Step 2: Orange selected tags, white inputs, orange CTA
- [ ] CAMERA: Light overlay, orange corner brackets, orange capture button
- [ ] ANALYZING: Thinking cat icon, "スタイルを解析中", no rotating ring
- [ ] RESULT: Orange/navy cards, fish icons, happy cat, navy heading

**Projection (http://localhost:3000/projection):**
- [ ] IDLE: Dark navy bg (#141E2B), 85 logo with orange, cat icon (dark theme)
- [ ] PREFERENCE: Orange tags, white text on dark
- [ ] CAMERA: Orange scan line, orange grid
- [ ] ANALYZING: Thinking cat (dark), no rotating rings
- [ ] RESULT: Navy cards, orange prices, fish icons

- [ ] **Step 5: Final commit (if any fixups needed)**

```bash
git add -A
git commit -m "fix(ui): polish visual details from verification"
```
