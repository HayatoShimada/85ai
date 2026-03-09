"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import QRCode from "../QRCode";
import { ProjectionPayload } from "@/lib/projection-types";

// ============================================
// RESULT SCENE (Projection)
// アラート: 操作不可のプロジェクター向けに、すべての情報を一覧性高く表示
// ============================================
export function ProjectionResultScene({ payload }: { payload: ProjectionPayload }) {
  const rec = payload.recommendation;
  if (!rec) return null;

  const ymin = rec.box_ymin / 10;
  const xmin = rec.box_xmin / 10;
  const ymax = rec.box_ymax / 10;
  const xmax = rec.box_xmax / 10;

  return (
    <motion.div
      key="result"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
      className="absolute inset-0 p-12 flex flex-col z-20"
    >
      {/* 画面上部: 解析結果とタグ (操作UIとは異なり、全体で共有するサマリーとして表示) */}
      <div className="flex gap-12 h-[35%] w-full mb-8 bg-black/40 p-8 rounded-3xl backdrop-blur-md border border-slate-700/50 shadow-2xl">
        {/* 左: 撮影画像（バウンディングボックス付き） */}
        <div className="relative h-full aspect-[4/3] bg-black rounded-2xl overflow-hidden border border-slate-700 shadow-[0_0_20px_rgba(0,0,0,0.5)]">
          {payload.capturedImage && (
             <img src={payload.capturedImage} className="w-full h-full object-contain" alt="Captured" />
          )}
          {rec.box_ymin > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="absolute pointer-events-none border-4 border-emerald-400 bg-emerald-400/20"
              style={{
                top: `${Math.max(0, Math.min(100, ymin))}%`,
                left: `${Math.max(0, Math.min(100, xmin))}%`,
                height: `${Math.max(0, Math.min(100, ymax - ymin))}%`,
                width: `${Math.max(0, Math.min(100, xmax - xmin))}%`,
              }}
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-sm px-4 py-1 rounded-full font-bold shadow-lg">
                DETECTED
              </div>
            </motion.div>
          )}
        </div>

        {/* 右: 解析テキストとタグ */}
        <div className="flex-1 flex flex-col justify-center space-y-6">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent drop-shadow-lg">
            AI STYLING ANALYSIS
          </h2>
          <p className="text-2xl text-slate-200 leading-relaxed font-light drop-shadow-md">
            {rec.analyzed_outfit}
          </p>
          <div className="flex flex-wrap gap-3">
            {rec.detected_style.map((tag, i) => (
              <span key={`detected-${i}`} className="px-5 py-2 bg-cyan-500/20 border border-cyan-400/50 text-cyan-300 rounded-full text-lg shadow-[0_0_10px_rgba(6,182,212,0.3)]">
                {tag}
              </span>
            ))}
            {payload.selectedTags.map((tag, i) => (
              <span key={`sel-${i}`} className="px-5 py-2 bg-emerald-500/20 border border-emerald-400/50 text-emerald-300 rounded-full text-lg shadow-[0_0_10px_rgba(16,185,129,0.3)]">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* 画面下部: 最大3つの提案を横並びで表示 (インタラクション不要の一覧性) */}
      <div className="flex-1 flex gap-8 w-full">
        {rec.recommendations.map((recommendation, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.2 }}
            className="flex-1 bg-black/60 rounded-3xl p-6 border border-slate-700/50 backdrop-blur-xl flex flex-col relative overflow-hidden shadow-2xl"
          >
            {/* 装飾用背景 */}
            <div className="absolute top-0 right-0 text-[10rem] font-black text-white/[0.03] leading-none -mt-4 mr-2 pointer-events-none">
              {i + 1}
            </div>

            <h3 className="text-2xl font-bold text-slate-100 mb-2 border-b border-slate-700/80 pb-3 flex items-center justify-between z-10">
              {recommendation.title}
              <span className="text-sm px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                {recommendation.category}
              </span>
            </h3>

            <p className="text-slate-300 text-lg my-4 flex-1 line-clamp-3 z-10 drop-shadow">
              {recommendation.reason}
            </p>

            {/* 商品表示部分 */}
            {recommendation.shopify_products?.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 h-56 z-10">
                {recommendation.shopify_products.slice(0, 2).map((product) => (
                  <div key={product.id} className="relative bg-slate-800 rounded-xl overflow-hidden shadow-lg border border-slate-600/50 group">
                    {product.image_url && (
                       <Image 
                         src={product.image_url} 
                         alt={product.title} 
                         fill 
                         className="object-cover"
                         sizes="200px"
                       />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex flex-col justify-end p-3">
                      <p className="text-white text-xs font-bold line-clamp-2 leading-tight drop-shadow-md">
                        {product.title}
                      </p>
                      <p className="text-emerald-400 text-sm font-black mt-1 drop-shadow-md">
                        ¥{parseInt(product.price).toLocaleString()}
                      </p>
                    </div>
                    {/* プロジェクター側でもQRコードを表示し、離れた位置からでも読み取れるようにする */}
                    <div className="absolute top-2 right-2 bg-white p-1 rounded-md shadow-lg opacity-90 scale-75 origin-top-right">
                       <QRCode url={product.url} productTitle={product.title} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
                <div className="h-48 flex items-center justify-center text-slate-500 bg-slate-900/50 rounded-xl border border-dashed border-slate-700">
                  NO ITEM
                </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
