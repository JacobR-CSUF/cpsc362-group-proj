// apps/web/components/posts/PostActions.tsx
"use client";

import React, { useState } from "react";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface PostActionsProps {
    mediaId: string | null; // media_id from posts table
}

// Shape of emotion analysis result
type EmotionResult = {
    topEmotion: string;
    score: number;
    allScores: Record<string, number>;
};

export function PostActions({ mediaId }: PostActionsProps) {
    // Transcript / summary state
    const [transcript, setTranscript] = useState<string | null>(null);
    const [summary, setSummary] = useState<string | null>(null);
    const [loadingTranscript, setLoadingTranscript] = useState(false);
    const [loadingSummary, setLoadingSummary] = useState(false);

    // Emotion analysis state
    const [emotionResult, setEmotionResult] = useState<EmotionResult | null>(
        null
    );
    const [loadingEmotion, setLoadingEmotion] = useState(false);

    // Generic error state
    const [error, setError] = useState<string | null>(null);

    // Visibility toggles for panels
    const [showTranscript, setShowTranscript] = useState(false);
    const [showSummary, setShowSummary] = useState(false);
    const [showEmotion, setShowEmotion] = useState(false);

    const accessToken =
        typeof window !== "undefined"
            ? localStorage.getItem("access_token")
            : null;

    /**
     * Load transcript for the given media.
     * Calls: GET /api/v1/media-ai/{mediaId}/transcript
     */
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
            // expected shape: { text: "..." }
            setTranscript(body.text);
            setShowTranscript(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoadingTranscript(false);
        }
    }

    /**
     * Load summary for the given media.
     * Calls: GET /api/v1/media-ai/{mediaId}/summary?style=brief
     */
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
            // expected shape: { summary: "..." }
            setSummary(body.summary);
            setShowSummary(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoadingSummary(false);
        }
    }

    /**
     * Analyze emotion from image for the given media.
     * Calls: GET /api/v1/media-ai/{mediaId}/emotion
     * (Should only be used when media is an image on the API side.)
     */
    async function handleAnalyzeEmotion() {
        if (!mediaId) {
            setError("This post has no media.");
            return;
        }
        if (!accessToken) {
            setError("You must be logged in to analyze emotion.");
            return;
        }

        setLoadingEmotion(true);
        setError(null);

        try {
            const res = await fetch(
                `${API_BASE_URL}/api/v1/media-ai/${mediaId}/emotion`,
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
                const msg = data?.detail ?? "Failed to analyze emotion.";
                throw new Error(msg);
            }

            const body = await res.json();
            // expected shape from AI service: { top_emotion, score, all_scores }
            const result: EmotionResult = {
                topEmotion: body.top_emotion,
                score: body.score,
                allScores: body.all_scores ?? {},
            };

            setEmotionResult(result);
            setShowEmotion(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoadingEmotion(false);
        }
    }

    return (
        <div className="mt-3 space-y-3">
            {/* Action buttons */}
            <div className="flex flex-wrap gap-2">
                {/* Show subtitles / transcript */}
                <button
                    type="button"
                    onClick={handleLoadTranscript}
                    disabled={loadingTranscript || !mediaId}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                    {loadingTranscript ? "Loading transcript..." : "Show subtitles"}
                </button>

                {/* Show summary */}
                <button
                    type="button"
                    onClick={handleLoadSummary}
                    disabled={loadingSummary || !mediaId}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                    {loadingSummary ? "Summarizing..." : "Show summary"}
                </button>

                {/* Analyze emotion (image only on API side) */}
                <button
                    type="button"
                    onClick={handleAnalyzeEmotion}
                    disabled={loadingEmotion || !mediaId}
                    className="rounded-full border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                    {loadingEmotion ? "Analyzing..." : "Analyze emotion"}
                </button>
            </div>

            {/* Global error message */}
            {error && <p className="text-xs text-red-500">{error}</p>}

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

            {/* Emotion analysis panel */}
            {showEmotion && emotionResult && (
                <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-800">
                    <div className="mb-1 flex items-center justify-between">
                        <span className="font-semibold text-gray-700">Emotion analysis</span>
                        <button
                            type="button"
                            className="text-[10px] text-gray-500 hover:text-gray-800"
                            onClick={() => setShowEmotion(false)}
                        >
                            Close
                        </button>
                    </div>

                    <p className="mb-1">
                        <span className="font-semibold">Top emotion:</span>{" "}
                        {emotionResult.topEmotion}{" "}
                        <span className="text-gray-500">
                            ({(emotionResult.score * 100).toFixed(1)}%)
                        </span>
                    </p>

                    {emotionResult.allScores && (
                        <div className="mt-1 space-y-0.5">
                            {Object.entries(emotionResult.allScores).map(
                                ([label, score]) => (
                                    <div
                                        key={label}
                                        className="flex items-center justify-between text-[11px] text-gray-600"
                                    >
                                        <span>{label}</span>
                                        <span>{(score * 100).toFixed(1)}%</span>
                                    </div>
                                )
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
