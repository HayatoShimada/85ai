"use client";

import { motion } from "framer-motion";
import { User, Sparkles, Monitor, RotateCcw, MonitorPlay, Video } from "lucide-react";
import React from "react";

export const STYLE_CATEGORIES = {
  テイスト: ["かっこいい", "かわいい", "きれいめ", "ナチュラル", "個性的"],
  スタイル: ["ストリート", "アメカジ", "モード", "ヴィンテージ", "カジュアル", "スポーティ"],
  年代感: ["70s", "80s", "90s", "Y2K", "ミリタリー"],
};

interface PreferenceViewProps {
  userName: string;
  setUserName: (val: string) => void;
  userEmail: string;
  setUserEmail: (val: string) => void;
  selectedTags: string[];
  toggleTag: (tag: string) => void;
  onLookupCustomer: () => void;
  onProceed: () => void;
  // カメラ設定
  cameras: MediaDeviceInfo[];
  selectedCameraId: string;
  onSelectCamera: (deviceId: string) => void;
  mirrorCameras: any[];
  onSelectMirrorCamera: (index: number) => void;
  // ファイルアップロード
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function PreferenceView({
  userName,
  setUserName,
  userEmail,
  setUserEmail,
  selectedTags,
  toggleTag,
  onLookupCustomer,
  onProceed,
  cameras,
  selectedCameraId,
  onSelectCamera,
  mirrorCameras,
  onSelectMirrorCamera,
  onFileUpload,
}: PreferenceViewProps) {
  return (
    <motion.div
      key="preference"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-4xl mx-auto p-4 sm:p-8 space-y-8"
    >
      <div className="text-center space-y-2">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 flex items-center justify-center gap-2">
          <Sparkles className="w-6 h-6 text-emerald-400" />
          あなたの好みを教えてください
        </h2>
        <p className="text-slate-400">
          AIがよりパーソナライズされた提案を行います
        </p>
      </div>

      <div className="bg-slate-800/50 backdrop-blur-xl rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-700/50 space-y-8">
        {/* お客様情報 */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <User className="w-5 h-5 text-emerald-400" />
            お客様情報（任意）
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">お名前</label>
              <input
                type="text"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="田中 太郎"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">メールアドレス（リピーター復元用）</label>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                />
                <button
                  onClick={onLookupCustomer}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-xl transition-colors flex items-center gap-2 flex-shrink-0"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span className="hidden sm:inline">好みを復元</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* スタイルタグ選択 */}
        <div className="space-y-6">
          <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            好みのスタイル
          </h3>
          <div className="space-y-6">
            {Object.entries(STYLE_CATEGORIES).map(([category, tags]) => (
              <div key={category} className="space-y-3">
                <div className="text-sm font-medium text-slate-400 flex items-center gap-2">
                  <span className="w-8 h-[1px] bg-slate-700" />
                  {category}
                  <span className="flex-1 h-[1px] bg-slate-700" />
                </div>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => {
                    const isSelected = selectedTags.includes(tag);
                    return (
                      <button
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 border ${
                          isSelected
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                            : "bg-slate-900 text-slate-400 border-slate-700 hover:border-slate-500 hover:bg-slate-800"
                        }`}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 環境設定 (カメラ類) */}
        {cameras.length > 0 && (
          <div className="pt-6 mt-6 border-t border-slate-700/50 space-y-4">
            <h3 className="text-lg font-medium text-slate-200 flex items-center gap-2">
              <Monitor className="w-5 h-5 text-emerald-400" />
              システム設定
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1 flex items-center gap-1">
                  <Monitor className="w-4 h-4" />
                  撮影用カメラ (ブラウザ)
                </label>
                <select
                  value={selectedCameraId}
                  onChange={(e) => onSelectCamera(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  {cameras.map((camera) => (
                    <option key={camera.deviceId} value={camera.deviceId}>
                      {camera.label || `カメラ ${camera.deviceId.slice(0, 5)}...`}
                    </option>
                  ))}
                </select>
              </div>

              {mirrorCameras.length > 0 && (
                <div>
                  <label className="block text-sm text-slate-400 mb-1 flex items-center gap-1">
                    <Video className="w-4 h-4" />
                    ミラーカメラ (サーバー)
                  </label>
                  <select
                    onChange={(e) => onSelectMirrorCamera(parseInt(e.target.value))}
                    defaultValue=""
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="" disabled>フロントエンドからは変更不可</option>
                    {mirrorCameras.map((cam: any) => (
                      <option key={cam.index} value={cam.index}>
                        {cam.name} {cam.is_active ? "(稼働中)" : ""}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-4 pt-4">
        <button
          onClick={onProceed}
          className="flex-1 px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-emerald-500/25 active:scale-[0.98] text-lg text-center"
        >
          カメラで撮影に進む
        </button>
        
        <label className="flex-1 px-8 py-4 border-2 border-slate-700 hover:bg-slate-800 text-slate-300 rounded-2xl font-bold transition-all cursor-pointer text-center active:scale-[0.98]">
          <input
            type="file"
            accept="image/*"
            onChange={onFileUpload}
            className="hidden"
          />
          画像をアップロード
        </label>
      </div>
    </motion.div>
  );
}
