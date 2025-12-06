"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PostCard,
  type PostCardPost,
} from "@/components/ui/posts/PostCard";
import { useAuth } from "@/hooks/useAuth";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type ProfileUser = {
  id: string;
  username: string;
  created_at: string;
  profile_pic?: string | null;
  email?: string;
};

export default function MePage() {
  const router = useRouter();
  const {
    user,
    loading: authLoading,
    isAuthenticated,
    refetchUser,
  } = useAuth();

  const [posts, setPosts] = useState<PostCardPost[]>([]);
  const [postsLoading, setPostsLoading] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [avatarPreviewOpen, setAvatarPreviewOpen] = useState(false);

  async function moderateProfileImage(
    fileUrl: string
  ): Promise<{ isSafe: boolean; reason?: string }> {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/api/v1/media/moderate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          file_url: fileUrl,
          user: profile.username,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Moderation failed (${res.status})`);
      }
      const data = await res.json();
      return { isSafe: !!data?.is_safe, reason: data?.reason };
    } catch (err: any) {
      throw new Error(
        "Sensitive Content. Failed to upload. Action has been reported to the administrators."
      );
    }
  }

  async function deleteMedia(mediaId: string, token: string) {
    try {
      await fetch(`${API_BASE}/api/v1/media/${mediaId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Best-effort cleanup; ignore errors.
    }
  }

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!user || !isAuthenticated) return;

    const controller = new AbortController();

    async function loadPosts() {
      setPostsLoading(true);
      setPostsError(null);

      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(
          `${API_BASE}/api/v1/posts/user/${user.id}?page=1&limit=20`,
          {
            signal: controller.signal,
            headers: {
              accept: "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
          }
        );

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `Failed to load posts (${res.status})`);
        }

        const data = await res.json();
        const list = ((data.data ?? data.results ?? []) as PostCardPost[]).map(
          (p) => ({
            ...p,
            media: p.media
              ? { ...p.media, transcription_url: p.media.transcription_url ?? null }
              : null,
          })
        );

        setPosts(list);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setPostsError(err.message || "Failed to load posts");
        setPosts([]);
      } finally {
        setPostsLoading(false);
      }
    }

    loadPosts();
    return () => controller.abort();
  }, [user, isAuthenticated]);

  const handleAvatarClick = () => {
    setAvatarPreviewOpen(true);
  };

  const handlePenClick = () => {
    if (!isAuthenticated) return;
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setAvatarError("Please select an image file (including GIF).");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setAvatarError("Missing access token. Please log in again.");
      return;
    }

    setAvatarUploading(true);
    setAvatarError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("caption", "profile picture");

      const uploadRes = await fetch(
        `${API_BASE}/api/v1/media/upload`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!uploadRes.ok) {
        const text = await uploadRes.text();
        throw new Error(text || "Failed to upload image.");
      }

      const uploadJson = await uploadRes.json();
      const publicUrl = uploadJson?.data?.public_url;
      const mediaId = uploadJson?.data?.id;
      if (!publicUrl) {
        throw new Error("Upload succeeded but no URL returned.");
      }

      // Moderate profile image (handles GIFs via backend pipeline)
      if (!mediaId) {
        throw new Error("Upload missing media id for moderation.");
      }

      const moderation = await moderateProfileImage(publicUrl);
      if (!moderation.isSafe) {
        await deleteMedia(mediaId, token);
        throw new Error(
          "Sensitive Content. Failed to upload. Action has been reported to the administrators."
        );
      }

      const updateRes = await fetch(
        `${API_BASE}/api/v1/users/me`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ profile_pic: publicUrl }),
        }
      );

      if (!updateRes.ok) {
        const text = await updateRes.text();
        throw new Error(text || "Failed to save profile picture.");
      }

      await refetchUser();
    } catch (err: any) {
      setAvatarError(err.message || "Could not update profile picture.");
    } finally {
      setAvatarUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  if (authLoading) {
    return <p className="p-10 text-center">Loading profile...</p>;
  }

  if (!isAuthenticated || !user) return null;

  const profile = user as ProfileUser;
  const joined = profile.created_at
    ? new Date(profile.created_at).toLocaleDateString()
    : "Unknown";

  return (
    <div className="w-full px-2 py-10 sm:px-4">
      <div className="mb-10 flex flex-col items-center gap-3">
        <div className="relative">
          <button
            type="button"
            onClick={handleAvatarClick}
            className="block"
            aria-label="View profile picture"
            disabled={avatarUploading}
          >
            <img
              src={
                profile.profile_pic ??
                "https://placehold.co/180x180?text=Profile"
              }
              alt={`${profile.username}'s avatar`}
              className="h-40 w-40 rounded-full object-cover"
            />
            {avatarUploading && (
              <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 text-sm font-semibold text-white">
                Uploading...
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={handlePenClick}
            aria-label="Change profile picture"
            className="absolute -bottom-0 -right-0 flex h-10 w-10 items-center justify-center rounded-full bg-white shadow"
          >
            <img
              src="https://img.icons8.com/ios/50/pen.png"
              alt="Edit"
              className="h-6 w-6"
            />
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleAvatarChange}
        />

        <h1 className="text-3xl font-semibold">{profile.username}</h1>

        <p className="text-sm text-gray-500">Joined: {joined}</p>

        {profile.email && (
          <p className="text-sm text-gray-500">{profile.email}</p>
        )}
        {avatarError && (
          <p className="text-sm text-red-500">{avatarError}</p>
        )}
      </div>

      <hr className="-mx-4 my-8 border-t-2 border-black/20" />

      {postsError && (
        <p className="mb-4 text-center text-sm text-red-500">
          {postsError}
        </p>
      )}

      {postsLoading && <p className="text-center">Loading posts...</p>}

      {!postsLoading && !postsError && posts.length === 0 && (
        <p className="text-center text-gray-500">
          You have not posted yet.
        </p>
      )}

      <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 justify-items-stretch">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>

      <MediaViewerModal
        isOpen={avatarPreviewOpen}
        onClose={() => setAvatarPreviewOpen(false)}
        mediaUrl={
          profile.profile_pic ??
          "https://placehold.co/180x180?text=Profile"
        }
        mediaType="image"
      />
    </div>
  );
}
