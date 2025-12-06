"use client";

import Link from "next/link";
import { Comment } from "@/hooks/useComments";
import { truncateText } from "@/hooks/useComments";

interface CommentsPreviewProps {
  comments: Comment[];
  loading: boolean;
  error: string | null;
  onOpenModal: () => void;
}

export function CommentsPreview({
  comments,
  loading,
  error,
  onOpenModal,
}: CommentsPreviewProps) {
  if (loading && comments.length === 0) {
    return (
      <p className="mt-2 text-sm text-gray-500">Loading comments...</p>
    );
  }

  if (error && comments.length === 0) {
    return (
      <p className="mt-2 text-sm text-red-500">
        Could not load comments.
      </p>
    );
  }

  if (comments.length === 0) {
    return (
      <button
        type="button"
        className="mt-2 text-sm text-gray-500 hover:underline"
        onClick={onOpenModal}
      >
        Be the first to comment
      </button>
    );
  }

  const preview = comments.slice(0, 3);
  const hasMore = comments.length > 3;

  return (
    <div className="mt-2 space-y-1 text-sm">
      {preview.map((c) => (
        <div key={c.id}>
          <Link
            href={`/${c.author.username}`}
            className="font-semibold hover:underline"
          >
            {c.author.username}
          </Link>
          <span className="text-gray-900">: </span>
          <span className="text-gray-800">
            {truncateText(c.content, 120)}
          </span>
        </div>
      ))}

      {(hasMore || comments.length > 0) && (
        <button
          type="button"
          className="mt-1 text-xs text-gray-600 hover:underline"
          onClick={onOpenModal}
        >
          [+] View all comments
        </button>
      )}
    </div>
  );
}
