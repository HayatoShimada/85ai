"use client";

import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { QrCode, X } from "lucide-react";

interface QRCodeButtonProps {
  url: string;
  productTitle: string;
}

export default function QRCodeButton({ url, productTitle }: QRCodeButtonProps) {
  const [showQR, setShowQR] = useState(false);

  if (!url || url === "#") return null;

  return (
    <>
      <button
        onClick={() => setShowQR(true)}
        className="inline-flex items-center gap-1 px-3 py-1 bg-slate-700 hover:bg-slate-600 text-xs text-white rounded font-medium transition-colors"
        title="QRコードを表示"
      >
        <QrCode className="w-3.5 h-3.5" />
        QR
      </button>

      {showQR && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
          onClick={() => setShowQR(false)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-xs w-full mx-4 flex flex-col items-center gap-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start w-full">
              <h4 className="text-slate-800 font-bold text-sm line-clamp-2 flex-1 pr-2">
                {productTitle}
              </h4>
              <button
                onClick={() => setShowQR(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <QRCodeSVG
              value={url}
              size={200}
              level="M"
              marginSize={2}
            />
            <p className="text-slate-500 text-xs text-center">
              スマホで読み取ってオンラインで購入できます
            </p>
          </div>
        </div>
      )}
    </>
  );
}
