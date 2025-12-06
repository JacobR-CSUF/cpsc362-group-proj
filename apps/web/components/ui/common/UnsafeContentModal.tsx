// apps/web/components/ui/common/UnsafeContentModal.tsx
"use client";

import React from "react";

interface UnsafeContentModalProps {
    open: boolean;
    onClose: () => void;
    mediaType?: "image" | "video";
    reason?: string;
}

export function UnsafeContentModal({
    open,
    onClose,
    mediaType,
    reason,
}: UnsafeContentModalProps) {
    if (!open) return null;

    const label = mediaType === "video" ? "video" : "image";

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
                <h3 className="mb-3 text-lg font-semibold text-red-600">
                    Unsafe content detected
                </h3>
                <p className="mb-2 text-sm text-red-600">
                    The {label} you tried to upload was flagged as unsafe by the AI
                    moderation system. It has not been saved.
                </p>
                {reason && (
                    <p className="mb-3 text-xs text-red-500">
                        <span className="font-semibold">Reason:</span> {reason}
                    </p>
                )}
                <div className="mt-4 flex justify-end">
                    <button
                        onClick={onClose}
                        className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
