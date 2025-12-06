"use client";

import { useState } from "react";
import { Comment } from "@/hooks/useComments";
import { CommentItem } from "./CommentItem";

interface CommentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  postId: string | null;
  comments: Comment[];
  loading: boolean;
  error: string | null;
  addComment: (content: string) => Promise<void>;
  deleteComment: (id: string) => Promise<void>;
  currentUserId: string | null;
}

export function CommentsModal({
  isOpen,
  onClose,
  postId,
  comments,
  loading,
  error,
  addComment,
  deleteComment,
  currentUserId,
}: CommentsModalProps) {
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!isOpen || !postId) return null;

  const handleSubmit = async () => {
    const trimmed = content.trim();
    if (!trimmed) return;
    if (trimmed.length > 500) {
      setSubmitError("Comment must be 500 characters or less.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      await addComment(trimmed);
      setContent("");
    } catch (err: any) {
      setSubmitError(err.message || "Failed to submit comment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="relative flex max-h-[80vh] w-full max-w-xl flex-col rounded-[10px] bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 rounded-full px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 hover:text-black"
          aria-label="Close comments"
        >
          Close
        </button>

        <div className="no-scrollbar flex-1 space-y-3 overflow-y-auto px-4 pt-10 pb-3">
          {loading && comments.length === 0 && (
            <p className="text-sm text-gray-500">Loading comments...</p>
          )}

          {error && comments.length === 0 && (
            <p className="text-sm text-red-500">Could not load comments.</p>
          )}

          {!loading && !error && comments.length === 0 && (
            <p className="text-sm text-gray-500">
              No comments yet. Be the first to say something!
            </p>
          )}

          {comments.map((c) => (
            <CommentItem
              key={c.id}
              comment={c}
              canDelete={currentUserId === c.author.id}
              onDelete={() => deleteComment(c.id)}
            />
          ))}
        </div>

        <div className="border-t border-black/10 px-4 py-3">
          <textarea
            className="w-full resize-none rounded-md border border-black/20 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-black/40"
            rows={3}
            placeholder="Write a comment..."
            maxLength={500}
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>{content.length}/500</span>
            {submitError && (
              <span className="text-red-500">{submitError}</span>
            )}
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={
              submitting || !content.trim() || content.trim().length > 500
            }
            className="mt-2 w-full rounded-md bg-black py-2 text-sm font-semibold text-white hover:bg-black/90 disabled:opacity-50"
          >
            {submitting ? "Posting..." : "Post"}
          </button>
        </div>
      </div>
    </div>
  );
}
