export type AppState =
  | "IDLE"
  | "PREFERENCE"
  | "CAMERA_ACTIVE"
  | "ANALYZING"
  | "RESULT";

export interface ShopifyProduct {
  id: string;
  title: string;
  description: string;
  price: string;
  image_url: string;
  url: string;
}

export interface RecommendationItem {
  title: string;
  reason: string;
  search_keywords: string[];
  category: string;
  shopify_products: ShopifyProduct[];
}

export interface ClothingAnalysis {
  analyzed_outfit: string;
  detected_style: string[];
  box_ymin: number;
  box_xmin: number;
  box_ymax: number;
  box_xmax: number;
  recommendations: RecommendationItem[];
}

export interface ProjectionPayload {
  selectedTags: string[];
  userName: string;
  capturedImage: string | null;
  recommendation: ClothingAnalysis | null;
  analyzeTimedOut: boolean;
}
