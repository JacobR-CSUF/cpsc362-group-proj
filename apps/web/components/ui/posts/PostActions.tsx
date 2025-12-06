// apps/web/components/posts/PostActions.tsx
"use client";

import React, { useState } from "react";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface PostActionsProps {
    mediaId: string | null; // media_id from posts table
}

export function PostActions({ mediaId }: PostActionsProps) {
    const [transcript, setTranscript] = useState<string | null>(null);
    const [summary, setSummary] = useState<string | null>(null);
    const [loadingTranscript, setLoadingTranscript] = useState(false);
    const [loadingSummary, setLoadingSummary] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Simple toggle state
    const [showTranscript, setShowTranscript] = useState(false);
    const [showSummary, setShowSummary] = useState(false);

    const accessToken =
        typeof window !== "undefined"
            ? localStorage.getItem("accessToken")
            : null;

    async function handleLoadTranscript() {
        if (!mediaId) {
            setError("This post has no media.");
            return;
        }
        if (!accessToken) {
            setError("You must be logged in to view transcript.");
            return;
        }

        setLoadingTranscript(true);
        setError(null);

        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/media-ai/${mediaId}/transcript`,
                {
                    method: "GET",
                    credentials: "include",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                    },
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => null);
                const msg = data?.detail ?? "Failed to load transcript.";
                throw new Error(msg);
            }

            const body = await res.json();
            setTranscript(body.text);
            setShowTranscript(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoadingTranscript(false);
        }
    }

    async function handleLoadSummary() {
        if (!mediaId) {
            setError("This post has no media.");
            return;
        }
        if (!accessToken) {
            setError("You must be logged in to view summary.");
            return;
        }

        setLoadingSummary(true);
        setError(null);

        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/media-ai/${mediaId}/summary?style=brief`,
                {
                    method: "GET",
                    credentials: "include",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                    },
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => null);
                const msg = data?.detail ?? "Failed to load summary.";
                throw new Error(msg);
            }

            const body = await res.json();
            setSummary(body.summary);
            setShowSummary(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoadingSummary(false);
        }
    }

    return (
        <div className="mt-3 space-y-3">
            {/* Buttons */}
            <div className="flex flex-wrap gap-2">
                <button
                    type="button"
                    onClick={handleLoadTranscript}
                    disabled={loadingTranscript || !mediaId}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                    {loadingTranscript ? "Loading transcript..." : "Show subtitles"}
                </button>

                <button
                    type="button"
                    onClick={handleLoadSummary}
                    disabled={loadingSummary || !mediaId}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                    {loadingSummary ? "Summarizing..." : "Show summary"}
                </button>
            </div>

            {/* Error message */}
            {error && (
                <p className="text-xs text-red-500">
                    {error}
                </p>
            )}

            {/* Transcript panel */}
            {showTranscript && transcript && (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-800 whitespace-pre-wrap">
                    <div className="mb-1 flex items-center justify-between">
                        <span className="font-semibold text-gray-700">Subtitles</span>
                        <button
                            type="button"
                            className="text-[10px] text-gray-500 hover:text-gray-800"
                            onClick={() => setShowTranscript(false)}
                        >
                            Close
                        </button>
                    </div>
                    {transcript}
                </div>
            )}

            {/* Summary panel */}
            {showSummary && summary && (
                <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-800 whitespace-pre-wrap">
                    <div className="mb-1 flex items-center justify-between">
                        <span className="font-semibold text-gray-700">Summary</span>
                        <button
                            type="button"
                            className="text-[10px] text-gray-500 hover:text-gray-800"
                            onClick={() => setShowSummary(false)}
                        >
                            Close
                        </button>
                    </div>
                    {summary}
                </div>
            )}
        </div>
    );
}
