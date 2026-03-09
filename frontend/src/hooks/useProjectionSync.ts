import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, ProjectionPayload } from "@/lib/projection-types";

// iPad -> バックエンド -> プロジェクター の同期
export function useProjectionSync(API_URL: string) {
  const wsRef = useRef<WebSocket | null>(null);
  
  // 接続処理
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    // http://... -> ws://... に変換
    const wsUrl = API_URL.replace(/^http/, "ws");
    const ws = new WebSocket(`${wsUrl}/ws/projection/control`);
    wsRef.current = ws;

    ws.onopen = () => console.log("[Projection WS] Connected (Operator)");
    ws.onclose = () => {
      console.log("[Projection WS] Disconnected. Reconnecting in 3s...");
      setTimeout(connect, 3000);
    };
    ws.onerror = (err) => console.error("[Projection WS] Error:", err);
  }, [API_URL]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // 状態変更の送信
  const broadcastState = useCallback((state: AppState, payload: Partial<ProjectionPayload>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "STATE_CHANGE",
          state,
          payload,
        })
      );
    } else {
      console.warn("WebSocket is not open. Cannot broadcast state.");
    }
  }, []);

  // フラッシュエフェクトの送信
  const triggerFlash = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "FLASH" }));
    }
  }, []);

  return {
    broadcastState,
    triggerFlash,
  };
}
