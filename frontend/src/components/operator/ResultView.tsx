"use client";

import { motion } from "framer-motion";
import { Check, RotateCcw, Sparkles } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import QRCode from "../QRCode";
import { ClothingAnalysis, RecommendationItem } from "@/lib/projection-types";

interface ResultViewProps {
  analyzedImage: string | null;
  recommendation: ClothingAnalysis | null;
  selectedTags: string[];
  warningMessage?: string | null;
  onReset: () => void;
}

/** 提案カード1枚分 */
function RecommendationCard({
  rec,
  index,
}: {
  rec: RecommendationItem;
  index: number;
}) {
  const [expanded, setExpanded] = useState(true);
  const colors = [
    { accent: "emerald", bg: "bg-emerald-500/10", border: "border-emerald-500/40", badge: "bg-emerald-500", text: "text-emerald-400" },
    { accent: "cyan",    bg: "bg-cyan-500/10",    border: "border-cyan-500/40",    badge: "bg-cyan-500",    text: "text-cyan-400" },
    { accent: "violet",  bg: "bg-violet-500/10",  border: "border-violet-500/40",  badge: "bg-violet-500",  text: "text-violet-400" },
  ][index] || { accent: "emerald", bg: "bg-emerald-500/10", border: "border-emerald-500/40", badge: "bg-emerald-500", text: "text-emerald-400" };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`rounded-2xl border ${colors.border} ${colors.bg} overflow-hidden`}
    >
      {/* ヘッダー: タップで開閉 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 p-5 text-left active:bg-white/5 transition-colors"
      >
        <span className={`shrink-0 w-10 h-10 rounded-full ${colors.badge} flex items-center justify-center text-white font-bold text-lg shadow-lg`}>
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-bold text-slate-100 truncate">{rec.title}</h3>
          <span className={`text-xs font-medium ${colors.text}`}>{rec.category}</span>
        </div>
        <span className={`text-xs ${colors.text} shrink-0`}>
          {rec.shopify_products?.length || 0}点
        </span>
        <svg
          className={`w-5 h-5 text-slate-400 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4">
          {/* 提案理由 */}
          <p className="text-slate-300 text-sm leading-relaxed bg-slate-900/40 p-3 rounded-xl">
            {rec.reason}
          </p>

          {/* 商品リスト: 横スクロール */}
          {rec.shopify_products?.length > 0 ? (
            <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 snap-x snap-mandatory">
              {rec.shopify_products.map((product) => (
                <div
                  key={product.id}
                  className="snap-start shrink-0 w-40 bg-slate-900 rounded-xl overflow-hidden border border-slate-700/50"
                >
                  <div className="relative aspect-square bg-slate-800">
                    {product.image_url ? (
                      <Image
                        src={product.image_url}
                        alt={product.title}
                        fill
                        sizes="160px"
                        className="object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-xs">
                        No Image
                      </div>
                    )}
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-2 pt-6">
                      <span className="text-white font-bold text-sm">
                        ¥{parseInt(product.price).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="p-2.5">
                    <h5 className="font-medium text-slate-200 text-xs leading-tight line-clamp-2 min-h-[2rem]">
                      {product.title}
                    </h5>
                    <QRCode url={product.url} productTitle={product.title} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-4">該当商品なし</p>
          )}
        </div>
      )}
    </motion.div>
  );
}

export function ResultView({
  analyzedImage,
  recommendation,
  selectedTags,
  warningMessage,
  onReset,
}: ResultViewProps) {
  const [showAnalysis, setShowAnalysis] = useState(false);

  if (!recommendation) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <p className="text-red-400">解析データが見つかりません</p>
        <button onClick={onReset} className="px-4 py-2 bg-slate-800 rounded-lg">
          戻る
        </button>
      </div>
    );
  }

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto p-4 sm:p-6 space-y-4 pb-24"
    >
      {/* ヘッダー: コンパクト */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <h2 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            AIスタイリング提案
          </h2>
          {warningMessage && (
            <p className="text-amber-400 text-xs mt-1">⚠️ {warningMessage}</p>
          )}
        </div>
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={onReset}
          className="flex items-center gap-2 px-5 py-3 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-white rounded-xl font-bold text-sm transition-colors border border-slate-700"
        >
          <RotateCcw className="w-4 h-4" />
          やり直す
        </motion.button>
      </div>

      {/* 解析サマリー: 折りたたみ式 */}
      <button
        onClick={() => setShowAnalysis(!showAnalysis)}
        className="w-full flex items-center gap-3 bg-slate-800/60 backdrop-blur rounded-xl p-3 border border-slate-700/50 active:bg-slate-700/60 transition-colors"
      >
        {analyzedImage && (
          <img
            src={analyzedImage}
            alt="Captured"
            className="w-12 h-12 rounded-lg object-cover shrink-0"
          />
        )}
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm text-slate-300 truncate">{recommendation.analyzed_outfit}</p>
          <div className="flex gap-1 mt-1 overflow-hidden">
            {recommendation.detected_style.slice(0, 4).map((tag, i) => (
              <span key={i} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded-full text-[10px] font-medium shrink-0">
                {tag}
              </span>
            ))}
            {selectedTags.slice(0, 3).map((tag, i) => (
              <span key={`s-${i}`} className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded-full text-[10px] font-medium shrink-0 flex items-center gap-0.5">
                <Check className="w-2.5 h-2.5" />{tag}
              </span>
            ))}
          </div>
        </div>
        <svg
          className={`w-4 h-4 text-slate-500 shrink-0 transition-transform ${showAnalysis ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {showAnalysis && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50 space-y-3"
        >
          <div className="relative w-full aspect-[4/3] rounded-lg overflow-hidden bg-black">
            {analyzedImage && (
              <img src={analyzedImage} alt="Captured" className="w-full h-full object-contain" />
            )}
            {recommendation.box_ymin > 0 && (
              <div
                className="absolute pointer-events-none border-2 border-emerald-400 bg-emerald-400/10"
                style={{
                  top: `${Math.max(0, Math.min(100, recommendation.box_ymin / 10))}%`,
                  left: `${Math.max(0, Math.min(100, recommendation.box_xmin / 10))}%`,
                  height: `${Math.max(0, Math.min(100, (recommendation.box_ymax - recommendation.box_ymin) / 10))}%`,
                  width: `${Math.max(0, Math.min(100, (recommendation.box_xmax - recommendation.box_xmin) / 10))}%`,
                }}
              />
            )}
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{recommendation.analyzed_outfit}</p>
          <div className="flex flex-wrap gap-1.5">
            {recommendation.detected_style.map((tag, i) => (
              <span key={i} className="px-2.5 py-1 bg-cyan-500/10 text-cyan-400 rounded-full text-xs border border-cyan-500/20">
                {tag}
              </span>
            ))}
            {selectedTags.map((tag, i) => (
              <span key={`sel-${i}`} className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs border border-emerald-500/20 flex items-center gap-1">
                <Check className="w-3 h-3" />{tag}
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {/* 3つの提案カード — すべて一覧表示 */}
      <div className="space-y-3">
        {recommendation.recommendations.map((rec, index) => (
          <RecommendationCard key={index} rec={rec} index={index} />
        ))}
      </div>
    </motion.div>
  );
}
