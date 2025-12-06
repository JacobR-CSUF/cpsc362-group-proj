"use client";

import { useEffect, useState } from "react";
import { AxiosError } from "axios";
import api from "@/lib/api";
import { decodeJwtPayload } from "@/utils/jwt";

export interface CommentAuthor {
  id: string;
  username: string;
  profile_pic: string | null;
}

export interface Comment {
  id: string;
  post_id: string;
  content: string;
  author: CommentAuthor;
  created_at: string;
  updated_at: string;
}

// simple in-memory cache keyed by postId
const commentsCache = new Map<string, Comment[]>();

function formatAxiosError(err: any): string {
  const axiosErr = err as AxiosError<any>;
  const data = axiosErr.response?.data;
  const detail = data?.detail ?? data?.message ?? data?.error;

  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => d?.msg || d?.message || JSON.stringify(d))
      .join(" | ");
  }
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return axiosErr.message || "Request failed.";
}

export function useComments(postId: string | null) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  // load from cache or fetch
  useEffect(() => {
    if (!postId) return;

    const cached = commentsCache.get(postId);
    if (cached) {
      setComments(cached);
      return;
    }

    fetchComments(postId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId]);

  // derive current user id from token (client-only)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    const payload = decodeJwtPayload(token);
    setCurrentUserId(payload?.sub ?? null);
  }, []);

  const fetchComments = async (id: string) => {
    setLoading(true);
    setError(null);

    try {
      const res = await api.get(`/api/v1/comments/posts/${id}/comments`, {
        params: { page: 1, page_size: 50 },
      });
      const results: Comment[] = res.data?.results ?? res.data?.data ?? [];
      commentsCache.set(id, results);
      setComments(results);
    } catch (err: any) {
      setError(formatAxiosError(err));
    } finally {
      setLoading(false);
    }
  };

  const addComment = async (content: string) => {
    if (!postId) return;
    const trimmed = content.trim();
    if (!trimmed) return;

    // optimistic comment
    const tempId = `temp-${Date.now()}`;
    const now = new Date().toISOString();

    const optimistic: Comment = {
      id: tempId,
      post_id: postId,
      content: trimmed,
      author: {
        id: currentUserId ?? "me",
        username: "You",
        profile_pic: null,
      },
      created_at: now,
      updated_at: now,
    };

    setComments((prev) => {
      const next = [optimistic, ...prev];
      commentsCache.set(postId, next);
      return next;
    });

    try {
      const res = await api.post(
        `/api/v1/comments/posts/${postId}/comments`,
        { content: trimmed },
        { withCredentials: true }
      );

      const created: Comment = res.data?.data ?? res.data;

      setComments((prev) => {
        const replaced = prev.map((c) => (c.id === tempId ? created : c));
        commentsCache.set(postId, replaced);
        return replaced;
      });
    } catch (err: any) {
      // rollback optimistic
      setComments((prev) => {
        const filtered = prev.filter((c) => c.id !== tempId);
        commentsCache.set(postId, filtered);
        return filtered;
      });
      throw new Error(formatAxiosError(err));
    }
  };

  const deleteComment = async (commentId: string) => {
    if (!postId) return;

    const prev = commentsCache.get(postId) ?? [];
    const updated = prev.filter((c) => c.id !== commentId);

    // optimistic removal
    commentsCache.set(postId, updated);
    setComments(updated);

    try {
      await api.delete(`/api/v1/comments/${commentId}`, {
        withCredentials: true,
      });
    } catch (err: any) {
      // rollback on error
      commentsCache.set(postId, prev);
      setComments(prev);
      throw new Error(formatAxiosError(err));
    }
  };

  return {
    comments,
    loading,
    error,
    addComment,
    deleteComment,
    currentUserId,
    refetch: () => postId && fetchComments(postId),
  };
}

// helper: relative time for timestamps
export function formatRelativeTime(iso: string, nowMs?: number): string {
  // Some backends return naive timestamps (no timezone). Treat them as UTC.
  const date = parseIsoAsUtc(iso);
  const now = nowMs ? new Date(nowMs) : new Date();
  const diffMs = now.getTime() - date.getTime();
  // If diff is negative due to timezone issues, clamp to zero so we don't show negative seconds.
  const diffSec = Math.max(0, Math.floor(diffMs / 1000));

  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD}d ago`;
  const diffW = Math.floor(diffD / 7);
  if (diffW < 4) return `${diffW}w ago`;
  const diffM = Math.floor(diffD / 30);
  if (diffM < 12) return `${diffM}mo ago`;
  const diffY = Math.floor(diffD / 365);
  return `${diffY}y ago`;
}

// Helper: parse ISO string, treating missing timezone as UTC
function parseIsoAsUtc(iso: string): Date {
  const hasZone = /[+-]\d\d:\d\d|Z$/.test(iso);
  const normalized = hasZone ? iso : `${iso}Z`;
  return new Date(normalized);
}

// helper: truncate for preview
export function truncateText(text: string, maxLength = 120): string {
  if (text.length <= maxLength) return text;
  const sliced = text.slice(0, maxLength);
  const lastSpace = sliced.lastIndexOf(" ");
  if (lastSpace === -1) return `${sliced}...`;
  return `${sliced.slice(0, lastSpace)}...`;
}

