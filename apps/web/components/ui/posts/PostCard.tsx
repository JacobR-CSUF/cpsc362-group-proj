// components/ui/posts/PostCard.tsx
"use client";

import Link from "next/link";
import { useState } from "react";
import { CommentToggle } from "@/components/comments/CommentToggle";
import { CommentsModal } from "@/components/comments/CommentsModal";
import { CommentsPreview } from "@/components/comments/CommentsPreview";
import { LikeButton } from "@/components/LikeButton";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";
import { useComments } from "@/hooks/useComments";

export interface PostAuthorSummary {
  user_id: string;
  username: string;
  profile_pic: string | null;
}

export interface PostMedia {
  id: string;
  public_url: string;
  media_type: "image" | "video";
  caption: string | null;
}

export interface PostCardPost {
  id: string;
  caption: string | null;
  author: PostAuthorSummary;
  media: PostMedia | null;
  created_at: string;
  likes_count?: number;
}

interface PostCardProps {
  post: PostCardPost;
  commentsHook?: ReturnType<typeof useComments>;
  className?: string;
}

export function PostCard({
  post,
  commentsHook,
  className = "",
}: PostCardProps) {
  const fallbackHook = useComments(
    commentsHook ? null : post?.id ?? null
  );
  const {
    comments,
    loading,
    error,
    addComment,
    deleteComment,
    currentUserId,
  } = commentsHook ?? fallbackHook;

  const [commentsModalOpen, setCommentsModalOpen] = useState(false);
  const [mediaModalOpen, setMediaModalOpen] = useState(false);

  const avatarFallback =
    post?.author?.username?.[0]?.toUpperCase() ?? "?";
  const createdAtLabel = post?.created_at
    ? new Date(post.created_at).toLocaleString()
    : "";

  return (
    <article
      className={`w-full rounded-lg bg-white border-2 border-green-200 p-4 shadow-md hover:border-green-300 transition-colors ${className}`}
    >
      <header className="mb-3 flex items-center gap-3">
        {post?.author?.profile_pic ? (
          <img
            src={post.author.profile_pic}
            alt={`${post.author.username}'s avatar`}
            className="h-10 w-10 rounded-full object-cover border-2 border-green-300"
          />
        ) : (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 border-2 border-green-300 text-sm font-semibold text-green-700">
            {avatarFallback}
          </div>
        )}
        <div className="min-w-0">
          <Link
            href={`/${post.author.username}`}
            className="text-sm font-semibold text-green-700 hover:text-green-600 hover:underline"
          >
            {post.author.username}
          </Link>
          {createdAtLabel && (
            <p className="text-xs text-gray-500">{createdAtLabel}</p>
          )}
        </div>
      </header>

      {post.media && post.media.public_url && (
        <button
          type="button"
          className="mb-3 w-full cursor-pointer overflow-hidden rounded-lg border-2 border-green-200 bg-black/5 hover:border-green-300 transition-colors"
          onClick={() => setMediaModalOpen(true)}
        >
          {post.media.media_type === "image" ? (
            <img
              src={post.media.public_url}
              alt={post.media.caption ?? "Post media"}
              className="max-h-[420px] w-full object-cover"
            />
          ) : (
            <video
              src={post.media.public_url}
              className="max-h-[420px] w-full object-cover"
              muted
              playsInline
              controls
            />
          )}
        </button>
      )}

      {post.caption && (
        <p className="mb-3 text-sm text-gray-900">{post.caption}</p>
      )}

      <div className="mb-2 flex items-center gap-4">
        <LikeButton initialCount={post.likes_count ?? 0} />
        <CommentToggle
          count={comments.length}
          onOpenModal={() => setCommentsModalOpen(true)}
        />
      </div>

      <CommentsPreview
        comments={comments}
        loading={loading}
        error={error}
        onOpenModal={() => setCommentsModalOpen(true)}
      />

      <CommentsModal
        isOpen={commentsModalOpen}
        onClose={() => setCommentsModalOpen(false)}
        postId={post.id}
        comments={comments}
        loading={loading}
        error={error}
        addComment={addComment}
        deleteComment={deleteComment}
        currentUserId={currentUserId}
      />

      <MediaViewerModal
        isOpen={mediaModalOpen}
        onClose={() => setMediaModalOpen(false)}
        mediaUrl={post.media?.public_url ?? null}
        mediaType={post.media?.media_type ?? null}
      />
    </article>
  );
}