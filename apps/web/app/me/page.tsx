"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PostCard,
  type PostCardPost,
} from "@/components/ui/posts/PostCard";
import { useAuth } from "@/hooks/useAuth";

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
  const { user, loading: authLoading, isAuthenticated } = useAuth();

  const [posts, setPosts] = useState<PostCardPost[]>([]);
  const [postsLoading, setPostsLoading] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);

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
        const list = (data.data ?? data.results ?? []) as PostCardPost[];
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

  if (authLoading) {
    return <p className="p-10 text-center">Loading profile...</p>;
  }

  if (!isAuthenticated || !user) return null;

  const profile = user as ProfileUser;
  const joined = profile.created_at
    ? new Date(profile.created_at).toLocaleDateString()
    : "Unknown";

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-10 flex flex-col items-center gap-3">
        <img
          src={
            profile.profile_pic ??
            "https://placehold.co/180x180?text=Profile"
          }
          alt={`${profile.username}'s avatar`}
          className="h-40 w-40 rounded-full object-cover"
        />

        <h1 className="text-3xl font-semibold">{profile.username}</h1>

        <p className="text-sm text-gray-500">Joined: {joined}</p>

        {profile.email && (
          <p className="text-sm text-gray-500">{profile.email}</p>
        )}
      </div>

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

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
