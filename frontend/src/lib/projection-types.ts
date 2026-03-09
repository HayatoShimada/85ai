export type AppState = "IDLE" | "PREFERENCE" | "CAMERA_ACTIVE" | "ANALYZING" | "RESULT";

export type BodyMeasurements = {
  height: string;
  shoulder_width: string;
  chest: string;
  waist: string;
  weight: string;
};

export type ShopifyProduct = {
  id: string;
  title: string;
  description: string;
  price: string;
  image_url: string;
  url: string;
};

export type RecommendationPattern = {
  title: string;
  reason: string;
  product_ids: number[];
  category: string;
  shopify_products: ShopifyProduct[];
};

export type RecommendationData = {
  analyzed_outfit: string;
  detected_style: string[];
  box_ymin: number;
  box_xmin: number;
  box_ymax: number;
  box_xmax: number;
  recommendations: RecommendationPattern[];
};

export type ProjectionPayload = {
  selectedTags: string[];
  userName: string;
  capturedImage: string | null;
  recommendation: RecommendationData | null;
  analyzeTimedOut: boolean;
};

export type ProjectionMessage =
  | { type: "STATE_CHANGE"; state: AppState; payload: ProjectionPayload }
  | { type: "FLASH" }
  | { type: "REQUEST_STATE" }
  | { type: "MIRROR_FRAME"; frame: string };
