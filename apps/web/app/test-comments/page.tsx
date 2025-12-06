"use client";

import { useEffect, useState } from "react";
import { useComments } from "@/hooks/useComments";
import { CommentsPreview } from "@/components/comments/CommentsPreview";
import { CommentToggle } from "@/components/comments/CommentToggle";
import { CommentsModal } from "@/components/comments/CommentsModal";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";
import { LikeButton } from "@/components/LikeButton";

const API_BASE = "http://localhost:8001";

interface PostAuthor {
  user_id: string;
  username: string;
  profile_pic: string | null;
}

interface PostMedia {
  id: string;
  public_url: string;
  media_type: "image" | "video";
  caption: string | null;
  transcription_url?: string | null;
}

interface Post {
  id: string;
  caption: string | null;
  author: PostAuthor;
  media: PostMedia | null;
  created_at: string;
}

const DEFAULT_POST_ID = "2cef0bb1-ebd6-4ac5-83c3-a5c9dbbdf9c0"; // adjust as needed

export default function TestCommentsPage() {
  const [postIdInput, setPostIdInput] = useState(DEFAULT_POST_ID);
  const [postId, setPostId] = useState<string | null>(DEFAULT_POST_ID);
  const [post, setPost] = useState<Post | null>(null);
  const [postLoading, setPostLoading] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);

  const [commentsModalOpen, setCommentsModalOpen] = useState(false);

  const [mediaModalOpen, setMediaModalOpen] = useState(false);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<"image" | "video" | null>(null);
  const [transcriptionUrl, setTranscriptionUrl] = useState<string | null>(null);

  const {
    comments,
    loading: commentsLoading,
    error: commentsError,
    addComment,
    deleteComment,
    currentUserId,
    refetch: refetchComments,
  } = useComments(postId);

  // fetch post
  useEffect(() => {
    if (!postId) return;

    const fetchPost = async () => {
      setPostLoading(true);
      setPostError(null);
      try {
        const accessToken = localStorage.getItem("access_token");
        const res = await fetch(`${API_BASE}/api/v1/posts/${postId}`, {
          method: "GET",
          headers: {
            accept: "application/json",
            ...(accessToken
              ? { Authorization: `Bearer ${accessToken}` }
              : {}),
          },
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(
            text || `Failed to load post (${res.status})`
          );
        }

        const data = await res.json();
        setPost(data);
      } catch (err: any) {
        setPostError(err.message || "Failed to load post.");
        setPost(null);
      } finally {
        setPostLoading(false);
      }
    };

    fetchPost();
  }, [postId]);

  const handleLoadPost = () => {
    setPostId(postIdInput.trim() || null);
    // comments hook will auto-refetch based on new postId
    refetchComments();
  };

  const openMediaViewer = () => {
    if (!post?.media) return;
    setMediaUrl(post.media.public_url);
    setMediaType(post.media.media_type);
    setTranscriptionUrl(post.media.transcription_url ?? null);
    setMediaModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-xl">
        <h1 className="mb-4 text-2xl font-semibold">
          /test-comments sandbox
        </h1>

        {/* Post ID input */}
        <div className="mb-4 flex gap-2">
          <input
            type="text"
            className="flex-1 rounded-md border border-black/20 px-3 py-2 text-sm"
            value={postIdInput}
            onChange={(e) => setPostIdInput(e.target.value)}
            placeholder="Post ID"
          />
          <button
            type="button"
            onClick={handleLoadPost}
            className="rounded-md bg-black px-3 py-2 text-sm font-semibold text-white hover:bg-black/90"
          >
            Load post
          </button>
        </div>

        {/* Post card */}
        <div className="rounded-[10px] bg-white p-4 shadow-md">
          {postLoading && <p>Loading post…</p>}
          {postError && (
            <p className="text-sm text-red-500">{postError}</p>
          )}

          {post && (
            <>
              {/* header */}
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 text-sm font-semibold">
                  {post.author.username[0]?.toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold">
                    {post.author.username}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(post.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* media */}
              {post.media && (
                <div
                  className="mb-3 cursor-pointer overflow-hidden rounded-[10px] border border-black/10 bg-black/5"
                  onClick={openMediaViewer}
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
                    />
                  )}
                </div>
              )}

              {/* caption */}
              {post.caption && (
                <p className="mb-3 text-sm text-gray-900">
                  {post.caption}
                </p>
              )}

              {/* actions row */}
              <div className="mb-2 flex items-center gap-4">
                <LikeButton initialCount={0} />
                <CommentToggle
                  count={comments.length}
                  onOpenModal={() => setCommentsModalOpen(true)}
                />
              </div>

              {/* comments preview */}
              <CommentsPreview
                comments={comments}
                loading={commentsLoading}
                error={commentsError}
                onOpenModal={() => setCommentsModalOpen(true)}
              />
            </>
          )}
        </div>
      </div>

      {/* Comments modal */}
      <CommentsModal
        isOpen={commentsModalOpen}
        onClose={() => setCommentsModalOpen(false)}
        postId={postId}
        comments={comments}
        loading={commentsLoading}
        error={commentsError}
        addComment={addComment}    
        deleteComment={deleteComment}
        currentUserId={currentUserId}
      />

      {/* Media viewer modal */}
      <MediaViewerModal
        isOpen={mediaModalOpen}
        onClose={() => setMediaModalOpen(false)}
        mediaUrl={mediaUrl}
        mediaType={mediaType}
        transcriptionUrl={transcriptionUrl}
      />
    </div>
  );
}
