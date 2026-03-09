"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Sparkles } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import QRCode from "../QRCode";
import { ClothingAnalysis } from "@/lib/projection-types";

interface ResultViewProps {
  analyzedImage: string | null;
  recommendation: ClothingAnalysis | null;
  selectedTags: string[];
  warningMessage?: string | null;
  onReset: () => void;
}

export function ResultView({
  analyzedImage,
  recommendation,
  selectedTags,
  warningMessage,
  onReset,
}: ResultViewProps) {
  const [activeTab, setActiveTab] = useState(0);

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

  // バウンディングボックスのピクセル変換 (0-1000座標系 -> 0-100%)
  const ymin = recommendation.box_ymin / 10;
  const xmin = recommendation.box_xmin / 10;
  const ymax = recommendation.box_ymax / 10;
  const xmax = recommendation.box_xmax / 10;

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-7xl mx-auto p-4 sm:p-8 space-y-8"
    >
      <div className="flex justify-between items-center bg-slate-800/50 p-4 sm:p-6 rounded-2xl backdrop-blur-md border border-slate-700/50">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            AIスタイリング提案
          </h2>
          {warningMessage && (
            <p className="text-amber-400 text-sm mt-1 flex items-center gap-1">
              ⚠️ {warningMessage}
            </p>
          )}
        </div>
        <button
          onClick={onReset}
          className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-bold transition-colors"
        >
          最初からやり直す
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* 左カラム: 解析結果 */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-800/80 rounded-2xl p-6 border border-slate-700 shadow-xl">
            <h3 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              現在のフィット分析
            </h3>
            
            <div className="relative w-full aspect-[4/3] rounded-xl overflow-hidden bg-black mb-6 border border-slate-700">
              {analyzedImage && (
                <img
                  src={analyzedImage}
                  alt="Captured"
                  className="w-full h-full object-contain"
                />
              )}
              {recommendation.box_ymin > 0 && (
                <div
                  className="absolute pointer-events-none border-2 border-emerald-400 bg-emerald-400/10 transition-all duration-1000 max-w-full max-h-full"
                  style={{
                    top: `${Math.max(0, Math.min(100, ymin))}%`,
                    left: `${Math.max(0, Math.min(100, xmin))}%`,
                    height: `${Math.max(0, Math.min(100, ymax - ymin))}%`,
                    width: `${Math.max(0, Math.min(100, xmax - xmin))}%`,
                  }}
                >
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] px-2 py-0.5 rounded-full font-bold shadow-lg whitespace-nowrap">
                    DETECTED ITEM
                  </div>
                </div>
              )}
            </div>

            <p className="text-slate-300 leading-relaxed text-sm p-4 bg-slate-900/50 rounded-xl">
              {recommendation.analyzed_outfit}
            </p>

            <div className="mt-4 space-y-2">
              <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">DETECTED TYPE & TAGS</span>
              <div className="flex flex-wrap gap-2">
                {recommendation.detected_style.map((tag, i) => (
                  <span key={i} className="px-3 py-1 bg-cyan-500/10 text-cyan-400 rounded-full text-xs font-medium border border-cyan-500/20">
                    {tag}
                  </span>
                ))}
                {selectedTags.map((tag, i) => (
                  <span key={`sel-${i}`} className="px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-medium border border-emerald-500/20 flex flex-center gap-1">
                    <Check className="w-3 h-3" /> {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 右カラム: 提案リスト */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {recommendation.recommendations.map((rec, index) => (
              <button
                key={index}
                onClick={() => setActiveTab(index)}
                className={`whitespace-nowrap px-6 py-4 rounded-xl font-bold transition-all flex items-center gap-2 ${
                  activeTab === index
                    ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/25"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                }`}
              >
                <span className="w-6 h-6 rounded-full bg-black/20 flex items-center justify-center text-sm">
                  {index + 1}
                </span>
                {rec.title}
              </button>
            ))}
          </div>

          <div className="bg-slate-800/90 rounded-2xl p-6 sm:p-8 border border-slate-700 min-h-[500px] shadow-2xl relative overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                <div className="space-y-4">
                  <h4 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-emerald-400" />
                    スタイリングの意図
                  </h4>
                  <p className="text-slate-300 text-lg leading-relaxed bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                    {recommendation.recommendations[activeTab].reason}
                  </p>
                </div>

                <div className="space-y-6">
                  <h4 className="text-xl font-bold text-slate-100 border-b border-slate-700 pb-2">
                    おすすめの一点モノ
                  </h4>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {recommendation.recommendations[activeTab].search_keywords.map((kw, idx) => (
                      <span key={idx} className="px-3 py-1 bg-slate-700 text-slate-300 text-xs rounded-full">
                        {kw}
                      </span>
                    ))}
                    <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs rounded-full">
                      {recommendation.recommendations[activeTab].category}
                    </span>
                  </div>

                  {recommendation.recommendations[activeTab].shopify_products?.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      {recommendation.recommendations[activeTab].shopify_products.map((product) => (
                        <div
                          key={product.id}
                          className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700 hover:border-emerald-500/50 transition-colors group flex flex-col"
                        >
                          <div className="relative aspect-square bg-slate-800 overflow-hidden">
                            {product.image_url ? (
                              <Image
                                src={product.image_url}
                                alt={product.title}
                                fill
                                sizes="(max-width: 768px) 100vw, 50vw"
                                className="object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                              />
                            ) : (
                              <div className="absolute inset-0 flex items-center justify-center text-slate-600">
                                No Image
                              </div>
                            )}
                            <div className="absolute top-3 right-3 bg-black/70 backdrop-blur-md px-3 py-1 rounded-full text-white font-bold text-sm shadow-xl">
                              ¥{parseInt(product.price).toLocaleString()}
                            </div>
                          </div>
                          
                          <div className="p-4 flex flex-col flex-1">
                            <h5 className="font-bold text-slate-100 line-clamp-2 text-sm leading-tight group-hover:text-emerald-400 transition-colors flex-1 min-h-[2.5rem]">
                              {product.title}
                            </h5>
                            
                            <QRCode url={product.url} productTitle={product.title} />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-slate-700 border-dashed">
                      <p className="text-slate-400">
                        該当する商品が見つかりませんでした。<br />
                        別のスタイル提案をご覧ください。
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
