// apps/web/components/posts/PostCard.tsx
"use client";

import Link from "next/link";
import { useState } from "react";

import { CommentToggle } from "@/components/comments/CommentToggle";
import { CommentsModal } from "@/components/comments/CommentsModal";
import { CommentsPreview } from "@/components/comments/CommentsPreview";
import { LikeButton } from "@/components/LikeButton";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";
import { useComments } from "@/hooks/useComments";
import { PostActions } from "@/components/posts/PostActions";

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
            className={`w-full rounded-[10px] bg-white p-4 shadow-md ${className}`}
        >
            {/* Header: author + timestamp */}
            <header className="mb-3 flex items-center gap-3">
                {post?.author?.profile_pic ? (
                    <img
                        src={post.author.profile_pic}
                        alt={`${post.author.username}'s avatar`}
                        className="h-10 w-10 rounded-full object-cover"
                    />
                ) : (
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 text-sm font-semibold">
                        {avatarFallback}
                    </div>
                )}
                <div className="min-w-0">
                    <Link
                        href={`/${post.author.username}`}
                        className="text-sm font-semibold hover:underline"
                    >
                        {post.author.username}
                    </Link>
                    {createdAtLabel && (
                        <p className="text-xs text-gray-500">{createdAtLabel}</p>
                    )}
                </div>
            </header>

            {/* Media (image or video) */}
            {post.media && post.media.public_url && (
                <button
                    type="button"
                    className="mb-3 w-full cursor-pointer overflow-hidden rounded-[10px] border border-black/10 bg-black/5"
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

            {/* Text caption */}
            {post.caption && (
                <p className="mb-3 text-sm text-gray-900">{post.caption}</p>
            )}

            {/* AI actions: transcript / summary / emotion */}
            <PostActions
                mediaId={post.media?.id ?? null}
                mediaType={post.media?.media_type ?? null}
            />

            {/* Likes / comments row */}
            <div className="mt-2 mb-2 flex items-center gap-4">
                <LikeButton initialCount={post.likes_count ?? 0} />
                <CommentToggle
                    count={comments.length}
                    onOpenModal={() => setCommentsModalOpen(true)}
                />
            </div>

            {/* Comments preview */}
            <CommentsPreview
                comments={comments}
                loading={loading}
                error={error}
                onOpenModal={() => setCommentsModalOpen(true)}
            />

            {/* Full comments modal */}
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

            {/* Media viewer modal */}
            <MediaViewerModal
                isOpen={mediaModalOpen}
                onClose={() => setMediaModalOpen(false)}
                mediaUrl={post.media?.public_url ?? null}
                mediaType={post.media?.media_type ?? null}
            />
        </article>
    );
}
