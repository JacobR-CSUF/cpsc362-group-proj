// apps/web/components/ui/posts/EmotionResultModal.tsx
"use client";

import React from "react";

type EmotionResult = {
    top_emotion: string;
    score: number;
    all_scores: Record<string, number>;
};

type EmotionResultModalProps = {
    open: boolean;
    onClose: () => void;
    result: EmotionResult | null;
};

export function EmotionResultModal({
    open,
    onClose,
    result,
}: EmotionResultModalProps) {
    if (!open || !result) return null;

    const { top_emotion, score, all_scores } = result;
    const entries = Object.entries(all_scores || {}).sort(
        (a, b) => b[1] - a[1]
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
                <h2 className="mb-4 text-lg font-semibold text-gray-900">
                    Detected Emotion
                </h2>

                <p className="mb-2 text-sm text-gray-700">
                    <span className="font-semibold">Top emotion:</span>{" "}
                    <span className="uppercase tracking-wide">
                        {top_emotion} ({(score * 100).toFixed(1)}%)
                    </span>
                </p>

                <div className="mt-4">
                    <p className="mb-1 text-xs font-semibold text-gray-500">
                        All scores
                    </p>
                    <div className="space-y-1">
                        {entries.map(([label, value]) => (
                            <div key={label} className="flex items-center justify-between">
                                <span className="text-sm capitalize text-gray-800">
                                    {label}
                                </span>
                                <span className="text-xs text-gray-600">
                                    {(value * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={onClose}
                        className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
