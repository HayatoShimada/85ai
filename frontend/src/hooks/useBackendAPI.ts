import { useCallback, useState } from "react";
import { ClothingAnalysis } from "@/lib/projection-types";

// フロントエンドのAPI URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useBackendAPI() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  /**
   * 画像と好みタグをAPIに送信して解析結果を取得する
   */
  const sendImageToAPI = useCallback(async (
    imageBlob: Blob, 
    previewUrl: string, 
    selectedTags: string[], 
    userName: string, 
    userEmail: string
  ): Promise<{ data: ClothingAnalysis; warning?: string } | null> => {
    setIsAnalyzing(true);
    setAnalyzeError(null);

    const formData = new FormData();
    formData.append("file", imageBlob, "capture.webp");
    formData.append("preferences", JSON.stringify(selectedTags));
    if (userName) formData.append("customer_name", userName);
    if (userEmail) formData.append("customer_email", userEmail);

    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`API Error: ${res.status}`);
      }
      
      const result = await res.json();
      return result;
    } catch (err: any) {
      console.error(err);
      setAnalyzeError(err.message || "解析中にエラーが発生しました");
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  /**
   * メールアドレスで既存顧客の好みを復元する
   */
  const lookupCustomerPreferences = useCallback(async (email: string) => {
    try {
      const res = await fetch(`${API_URL}/api/customers?email=${encodeURIComponent(email)}`);
      if (res.ok) {
        const data = await res.json();
        return data.preferences || []; // 取得したタグ配列を返す
      }
    } catch (err) {
      console.error("Failed to lookup customer:", err);
    }
    return [];
  }, []);

  /**
   * ミラーカメラデバイス一覧の取得
   */
  const fetchMirrorCameras = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/mirror/cameras`);
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.error("Failed to fetch mirror cameras:", err);
    }
    return null;
  }, []);

  /**
   * ミラーカメラの切り替えリクエスト
   */
  const switchMirrorCamera = useCallback(async (index: number) => {
    try {
      await fetch(`${API_URL}/api/mirror/cameras/${index}`, {
        method: "POST",
      });
    } catch (err) {
      console.error("Failed to switch mirror camera:", err);
    }
  }, []);

  /**
   * ヘルスチェック
   */
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/health`);
      if (res.ok) return await res.json();
    } catch (err) {
      console.error("Backend health check failed:", err);
    }
    return null;
  }, []);

  return {
    isAnalyzing,
    analyzeError,
    sendImageToAPI,
    lookupCustomerPreferences,
    fetchMirrorCameras,
    switchMirrorCamera,
    checkHealth,
  };
}
