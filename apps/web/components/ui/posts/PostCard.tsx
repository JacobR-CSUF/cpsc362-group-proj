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
import { useAuth } from "@/hooks/useAuth";
import { PostActions } from "@/components/ui/posts/PostActions";

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
    const { user } = useAuth();
    
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
    const [deleting, setDeleting] = useState(false);

    const avatarFallback =
        post?.author?.username?.[0]?.toUpperCase() ?? "?";
    const createdAtLabel = post?.created_at
        ? new Date(post.created_at).toLocaleString()
        : "";

    // Check if this is the current user's post
    const isMyPost = user?.id === post.author.user_id;

    // Handle post deletion
    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this post?")) {
            return;
        }

        setDeleting(true);
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(
                `http://localhost:8001/api/v1/posts/${post.id}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Failed to delete post");
            }

            // Refresh the page to update the feed
            window.location.reload();
        } catch (err) {
            alert("Failed to delete post. Please try again.");
            setDeleting(false);
        }
    };

    return (
        <article
            className={`w-full rounded-lg bg-white border-2 border-green-200 p-4 shadow-md hover:border-green-300 transition-colors relative ${className}`}
        >
            {/* Delete button - only show on your own posts */}
            {isMyPost && (
                <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="absolute top-2 right-2 p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full transition-colors disabled:opacity-50"
                    title="Delete post"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            )}
            
            {/* Header: author + timestamp */}
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
                        href={user?.id === post.author.user_id ? '/me' : `/${post.author.username}`}
                        className="text-sm font-semibold text-green-700 hover:text-green-600 hover:underline"
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

            {/* Text caption */}
            {post.caption && (
                <p className="mb-3 text-sm text-gray-900">{post.caption}</p>
            )}

            {/* AI actions: transcript / summary / emotion */}
            <PostActions
              mediaId={post.media?.id ?? null}
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