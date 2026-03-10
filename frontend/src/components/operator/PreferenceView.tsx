"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Sparkles, Monitor, RotateCcw, Video, Ruler, Shield, ChevronLeft } from "lucide-react";
import React from "react";


export const STYLE_CATEGORIES = {
  テイスト: ["かっこいい", "かわいい", "きれいめ", "ナチュラル", "個性的"],
  スタイル: ["ストリート", "アメカジ", "モード", "ヴィンテージ", "カジュアル", "スポーティ"],
  年代感: ["70s", "80s", "90s", "Y2K", "ミリタリー"],
};

const BODY_FIELDS = [
  { key: "height", label: "身長", unit: "cm", placeholder: "170" },
  { key: "shoulder_width", label: "肩幅", unit: "cm", placeholder: "44" },
  { key: "chest", label: "胸囲", unit: "cm", placeholder: "92" },
  { key: "waist", label: "ウエスト", unit: "cm", placeholder: "78" },
  { key: "weight", label: "体重", unit: "kg", placeholder: "65" },
];

interface PreferenceViewProps {
  userName: string;
  setUserName: (val: string) => void;
  userEmail: string;
  setUserEmail: (val: string) => void;
  selectedTags: string[];
  toggleTag: (tag: string) => void;
  onLookupCustomer: () => Promise<boolean>;
  onProceed: () => void;
  onSkipToCamera: () => void;
  onSkipFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  // カメラ設定
  cameras: MediaDeviceInfo[];
  selectedCameraId: string;
  onSelectCamera: (deviceId: string) => void;
  mirrorCameras: any[];
  onSelectMirrorCamera: (index: number) => void;
  // ファイルアップロード
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  // 体型情報
  bodyMeasurements: Record<string, number>;
  setBodyMeasurements: (val: Record<string, number>) => void;
  // 同意・マーケティング
  emailMarketingConsent: boolean;
  setEmailMarketingConsent: (val: boolean) => void;
  privacyAgreed: boolean;
  setPrivacyAgreed: (val: boolean) => void;
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
  onSkipToCamera,
  onSkipFileUpload,
  cameras,
  selectedCameraId,
  onSelectCamera,
  mirrorCameras,
  onSelectMirrorCamera,
  onFileUpload,
  bodyMeasurements,
  setBodyMeasurements,
  emailMarketingConsent,
  setEmailMarketingConsent,
  privacyAgreed,
  setPrivacyAgreed,
}: PreferenceViewProps) {
  const [step, setStep] = useState(1);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [isLookingUp, setIsLookingUp] = useState(false);

  const canProceedToStep2 = userName.trim() !== "" && userEmail.trim() !== "" && privacyAgreed;

  const handleLookup = async () => {
    setIsLookingUp(true);
    try {
      const found = await onLookupCustomer();
      if (found) setStep(2);
    } finally {
      setIsLookingUp(false);
    }
  };

  const updateMeasurement = (key: string, value: string) => {
    const num = parseFloat(value);
    if (value === "" || isNaN(num)) {
      const next = { ...bodyMeasurements };
      delete next[key];
      setBodyMeasurements(next);
    } else {
      setBodyMeasurements({ ...bodyMeasurements, [key]: num });
    }
  };

  return (
    <motion.div
      key="preference"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-4xl mx-auto p-4 sm:p-8 space-y-8"
    >
      {/* ヘッダー */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl sm:text-3xl font-bold text-text flex items-center justify-center gap-2">
          {step === 1 ? (
            <>
              <User className="w-6 h-6 text-primary" />
              お客様情報の入力
            </>
          ) : (
            <>
              <Sparkles className="w-6 h-6 text-primary" />
              あなたの好みを教えてください
            </>
          )}
        </h2>
        <p className="text-text-muted">
          {step === 1
            ? "お名前とメールアドレスを入力してください"
            : "AIがよりパーソナライズされた提案を行います"}
        </p>
        {/* ステップインジケーター */}
        <div className="flex items-center justify-center gap-2 pt-2">
          <div className={`w-8 h-1 rounded-full transition-colors ${step >= 1 ? "bg-primary" : "bg-border"}`} />
          <div className={`w-8 h-1 rounded-full transition-colors ${step >= 2 ? "bg-primary" : "bg-border"}`} />
        </div>
      </div>

      <div className="bg-card rounded-3xl p-6 sm:p-8 shadow-[0_0_3px_rgba(30,58,95,0.06)] border border-border space-y-8">
        <AnimatePresence mode="wait">
          {/* ===== ステップ1: お客様情報 ===== */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              {/* 名前・メール入力 */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-text-muted mb-1">お名前</label>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    placeholder="田中 太郎"
                    className="w-full bg-white border border-border rounded-xl px-4 py-3 text-text focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm text-text-muted mb-1">メールアドレス</label>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={userEmail}
                      onChange={(e) => setUserEmail(e.target.value)}
                      placeholder="user@example.com"
                      className="flex-1 bg-white border border-border rounded-xl px-4 py-3 text-text focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                    />
                    <button
                      onClick={handleLookup}
                      disabled={!userEmail.trim() || isLookingUp}
                      className="px-4 py-2 bg-[#F5F6F7] hover:bg-border text-text rounded-xl transition-colors flex items-center gap-2 flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <RotateCcw className={`w-4 h-4 ${isLookingUp ? "animate-spin" : ""}`} />
                      <span className="hidden sm:inline">復元</span>
                    </button>
                  </div>
                  <p className="text-xs text-text-muted mt-1">
                    以前ご利用いただいた方はメールアドレスから情報を復元できます
                  </p>
                </div>
              </div>

              {/* 同意チェックボックス */}
              <div className="space-y-3 pt-2 border-t border-border">
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={emailMarketingConsent}
                    onChange={(e) => setEmailMarketingConsent(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-border bg-white text-primary focus:ring-primary focus:ring-offset-0"
                  />
                  <span className="text-sm text-text-body group-hover:text-text transition-colors">
                    新着商品やセール情報をメールで受け取る
                  </span>
                </label>
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={privacyAgreed}
                    onChange={(e) => setPrivacyAgreed(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-border bg-white text-primary focus:ring-primary focus:ring-offset-0"
                  />
                  <span className="text-sm text-text-body group-hover:text-text transition-colors">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        setShowPolicyModal(true);
                      }}
                      className="text-primary underline underline-offset-2 hover:text-primary-light transition-colors"
                    >
                      個人情報の取り扱いについて
                    </button>
                    に同意する
                  </span>
                </label>
              </div>
            </motion.div>
          )}

          {/* ===== ステップ2: 好み・体型・カメラ設定 ===== */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              {/* 戻るボタン */}
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-1 text-sm text-text-muted hover:text-text transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                お客様情報に戻る
              </button>

              {/* スタイルタグ選択 */}
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-text flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  好みのスタイル
                </h3>
                <div className="space-y-6">
                  {Object.entries(STYLE_CATEGORIES).map(([category, tags]) => (
                    <div key={category} className="space-y-3">
                      <div className="text-sm font-medium text-text-muted flex items-center gap-2">
                        <span className="w-8 h-[1px] bg-border" />
                        {category}
                        <span className="flex-1 h-[1px] bg-border" />
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
                                  ? "bg-primary/15 text-primary border-primary/50 shadow-[0_0_10px_rgba(255,107,53,0.15)]"
                                  : "bg-[#F5F6F7] text-text-muted border-border hover:border-text-muted hover:bg-white"
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

              {/* 体型情報 */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-text flex items-center gap-2">
                  <Ruler className="w-5 h-5 text-primary" />
                  体型情報（任意）
                </h3>
                <p className="text-sm text-text-muted">
                  入力するとサイズに合った商品を優先的に提案します
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {BODY_FIELDS.map((field) => (
                    <div key={field.key}>
                      <label className="block text-sm text-text-muted mb-1">
                        {field.label}（{field.unit}）
                      </label>
                      <input
                        type="number"
                        value={bodyMeasurements[field.key] ?? ""}
                        onChange={(e) => updateMeasurement(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full bg-white border border-border rounded-xl px-4 py-3 text-text focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* 環境設定 (カメラ類) */}
              {cameras.length > 0 && (
                <div className="pt-6 mt-6 border-t border-border space-y-4">
                  <h3 className="text-lg font-medium text-text flex items-center gap-2">
                    <Monitor className="w-5 h-5 text-primary" />
                    システム設定
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-text-muted mb-1 flex items-center gap-1">
                        <Monitor className="w-4 h-4" />
                        撮影用カメラ (ブラウザ)
                      </label>
                      <select
                        value={selectedCameraId}
                        onChange={(e) => onSelectCamera(e.target.value)}
                        className="w-full bg-white border border-border rounded-xl px-4 py-3 text-text outline-none focus:ring-2 focus:ring-primary"
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
                        <label className="block text-sm text-text-muted mb-1 flex items-center gap-1">
                          <Video className="w-4 h-4" />
                          ミラーカメラ (サーバー)
                        </label>
                        <select
                          onChange={(e) => onSelectMirrorCamera(parseInt(e.target.value))}
                          defaultValue=""
                          className="w-full bg-white border border-border rounded-xl px-4 py-3 text-text outline-none focus:ring-2 focus:ring-primary"
                        >
                          <option value="" disabled>ミラーカメラを選択</option>
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ===== ボタンエリア ===== */}
      {step === 1 && (
        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <button
            onClick={() => setStep(2)}
            disabled={!canProceedToStep2}
            className="flex-1 px-8 py-4 bg-primary hover:bg-primary-dark text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-primary/25 active:scale-[0.98] text-lg text-center disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-primary disabled:hover:shadow-none disabled:active:scale-100"
          >
            次へ
          </button>
          <button
            onClick={onSkipToCamera}
            className="flex-1 px-8 py-4 border-2 border-border hover:bg-[#F5F6F7] text-text-body rounded-2xl font-bold transition-all text-center active:scale-[0.98]"
          >
            スキップして撮影へ
          </button>
          <label className="flex-1 px-8 py-4 border-2 border-border hover:bg-[#F5F6F7] text-text-body rounded-2xl font-bold transition-all cursor-pointer text-center active:scale-[0.98]">
            <input
              type="file"
              accept="image/*"
              onChange={onSkipFileUpload}
              className="hidden"
            />
            画像で診断
          </label>
        </div>
      )}

      {step === 2 && (
        <div className="flex flex-col sm:flex-row gap-4 pt-4">
          <button
            onClick={onProceed}
            className="flex-1 px-8 py-4 bg-primary hover:bg-primary-dark text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-primary/25 active:scale-[0.98] text-lg text-center"
          >
            カメラで撮影に進む
          </button>
          <label className="flex-1 px-8 py-4 border-2 border-border hover:bg-[#F5F6F7] text-text-body rounded-2xl font-bold transition-all cursor-pointer text-center active:scale-[0.98]">
            <input
              type="file"
              accept="image/*"
              onChange={onFileUpload}
              className="hidden"
            />
            画像をアップロード
          </label>
        </div>
      )}

      {/* ===== プライバシーポリシーモーダル ===== */}
      {showPolicyModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-navy/60 p-4"
          onClick={() => setShowPolicyModal(false)}
        >
          <div
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 sm:p-8 border border-border shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-6">
              <Shield className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-bold text-text">プライバシーポリシー</h2>
            </div>
            <div className="text-sm text-text-body space-y-4 leading-relaxed">
              <p className="text-text-muted">最終更新日：2025年12月5日</p>

              <p>
                85-store は、この店舗およびウェブサイト（関連するすべての情報、コンテンツ、機能、ツール、商品およびサービスを含む）を運営し、お客様に厳選されたショッピング体験（「サービス」）を提供しています。
                85-store は Shopify により運営されており、これにより私たちはサービスを提供することが可能となっています。
                本プライバシーポリシーは、お客様がサービスを訪問、利用、購入やその他の取引を行う際、またはその他の方法で当社と連絡を取る際に、当社がどのようにお客様の個人情報を収集、使用、開示するかについて説明しています。
              </p>

              <h3 className="text-base font-semibold text-text pt-2">当社が収集または処理する個人情報</h3>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li><span className="text-text-body">連絡先情報</span> — お名前、住所、電話番号、メールアドレス</li>
                <li><span className="text-text-body">財務情報</span> — クレジットカード、決済情報、取引の詳細</li>
                <li><span className="text-text-body">アカウント情報</span> — ユーザー名、パスワード、各種設定</li>
                <li><span className="text-text-body">取引情報</span> — 閲覧・購入・返品履歴</li>
                <li><span className="text-text-body">デバイス情報</span> — デバイス、ブラウザ、IPアドレス</li>
                <li><span className="text-text-body">使用用途に関する情報</span> — サービスとのやり取りに関する情報</li>
              </ul>

              <h3 className="text-base font-semibold text-text pt-2">お客様の個人情報の利用方法</h3>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li>サービスの提供、カスタマイズ、および改善</li>
                <li>マーケティングおよび広告</li>
                <li>セキュリティおよび詐欺防止</li>
                <li>お客様とのコミュニケーション</li>
                <li>法的理由</li>
              </ul>

              <h3 className="text-base font-semibold text-text pt-2">個人情報の開示方法</h3>
              <p className="text-text-muted">
                Shopifyや、当社に代わってサービスを提供するベンダー（IT管理、決済処理、データ分析、カスタマーサポート、クラウドストレージ、フルフィルメントおよび配送）などの第三者に個人情報を開示する場合があります。
              </p>

              <h3 className="text-base font-semibold text-text pt-2">お客様の権利と選択</h3>
              <ul className="list-disc list-inside space-y-1 text-text-muted">
                <li>アクセス権 / 知る権利</li>
                <li>削除権</li>
                <li>訂正権</li>
                <li>データポータビリティ権</li>
                <li>コミュニケーションの各種設定の管理</li>
              </ul>

              <h3 className="text-base font-semibold text-text pt-2">子どものデータ</h3>
              <p className="text-text-muted">
                本サービスは子どもを対象としておらず、16歳未満の個人から意図的に個人情報を収集することはありません。
              </p>

              <h3 className="text-base font-semibold text-text pt-2">ご連絡先</h3>
              <p className="text-text-muted">
                ご質問がある場合は info@85-store.com までメールでご連絡ください。
              </p>
              <p className="text-text-muted">
                本町四丁目１００番地, 南砺市, JP-16, 932-0217, JP
              </p>
            </div>
            <button
              onClick={() => setShowPolicyModal(false)}
              className="mt-6 w-full px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl font-bold transition-all active:scale-[0.98]"
            >
              閉じる
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
