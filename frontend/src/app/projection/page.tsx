"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { AppState, ProjectionPayload } from "@/lib/projection-types";

import { ProjectionBackground } from "@/components/projection/ProjectionBackground";
import { MirrorOverlay, ProjectionIdleScene, ProjectionPreferenceScene, ProjectionCameraScene, ProjectionAnalyzingScene } from "@/components/projection/ProjectionScenes";
import { ProjectionResultScene } from "@/components/projection/ProjectionResultScene";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws") + "/ws/projection/display";

const defaultPayload: ProjectionPayload = {
  selectedTags: [],
  userName: "",
  capturedImage: null,
  recommendation: null,
  analyzeTimedOut: false,
};

export default function ProjectionPage() {
  const [appState, setAppState] = useState<AppState>("IDLE");
  const [payload, setPayload] = useState<ProjectionPayload>(defaultPayload);
  
  // フラッシュエフェクト用 (iPadでの撮影実行時に光る)
  const [flash, setFlash] = useState(false);
  
  // ミラーカメラ（人物セグメンテーション）のフレーム
  const [mirrorFrame, setMirrorFrame] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // ==========================================
  // Display WebSocket (状態同期 + ミラーフレーム統合)
  // projection_manager が JSON制御メッセージとbase64ミラーフレームの両方を配信
  // ==========================================
  const connectDisplay = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Projection WS] Connected (Display)");
      ws.send(JSON.stringify({ type: "REQUEST_STATE" }));
    };

    ws.onmessage = (e) => {
      if (typeof e.data !== "string") return;

      // JSON制御メッセージ
      if (e.data.startsWith("{")) {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "STATE_CHANGE" && data.state) {
            setAppState(data.state as AppState);
            if (data.payload) {
              setPayload((prev) => ({ ...prev, ...data.payload }));
            }
          } else if (data.type === "FLASH") {
            setFlash(true);
            setTimeout(() => setFlash(false), 1200);
          }
        } catch (err) {
          console.error("Failed to parse projection WS message", err);
        }
      } else {
        // base64ミラーフレーム (projection_manager から配信)
        setMirrorFrame(e.data);
      }
    };

    ws.onclose = () => {
      console.log("[Projection WS] Disconnected. Reconnect in 3s...");
      setMirrorFrame(null);
      setTimeout(connectDisplay, 3000);
    };

    ws.onerror = (err) => {
      console.error("[Projection WS] Error:", err);
    };
  }, []);

  useEffect(() => {
    connectDisplay();
    return () => { wsRef.current?.close(); };
  }, [connectDisplay]);

  const showMirror = appState === "IDLE" || appState === "PREFERENCE" || appState === "CAMERA_ACTIVE" || appState === "ANALYZING";

  return (
    <main className="w-screen h-screen overflow-hidden bg-black text-slate-100 font-sans cursor-none relative">
      
      {/* 動的背景グラデーション */}
      <ProjectionBackground appState={appState} selectedTags={payload.selectedTags} />

      {/* フラッシュエフェクトレイヤー (最前面) */}
      <AnimatePresence>
        {flash && (
          <div className="absolute inset-0 bg-white z-[9999] pointer-events-none transition-opacity duration-[1200ms] ease-out opacity-0 starting:opacity-100" />
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {appState === "IDLE" && <ProjectionIdleScene key="idle" />}
        {appState === "PREFERENCE" && <ProjectionPreferenceScene key="pref" payload={payload} />}
        {appState === "CAMERA_ACTIVE" && <ProjectionCameraScene key="camera" payload={payload} />}
        {appState === "ANALYZING" && <ProjectionAnalyzingScene key="analyzing" payload={payload} />}
        {appState === "RESULT" && <ProjectionResultScene key="result" payload={payload} />}
      </AnimatePresence>

      {/* ミラー映像オーバーレイ */}
      <AnimatePresence>
        {showMirror && <MirrorOverlay key="mirror" frame={mirrorFrame} />}
      </AnimatePresence>
    </main>
  );
}
