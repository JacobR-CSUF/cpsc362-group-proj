"use client";

import { useEffect, useState } from "react";
import {
  PostCard,
  type PostCardPost,
} from "@/components/ui/posts/PostCard";
import { useParams } from "next/navigation";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type ProfileUser = {
  id: string;
  username: string;
  created_at: string;
  profile_pic: string | null;
};

interface UserProfilePageProps {
  params: { username: string };
}

export default function UserProfilePage({
  params,
}: UserProfilePageProps) {
  const paramsFromHook = useParams<{ username?: string }>();
  const username =
    paramsFromHook?.username ||
    (typeof params?.username === "string" ? params.username : undefined);

  const [user, setUser] = useState<ProfileUser | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [posts, setPosts] = useState<PostCardPost[]>([]);
  const [postsLoading, setPostsLoading] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchUser() {
      if (!username) {
        setNotFound(true);
        setProfileLoading(false);
        return;
      }

      setProfileLoading(true);
      setProfileError(null);
      setNotFound(false);

      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(
          `${API_BASE}/api/v1/users/username/${encodeURIComponent(
            username
          )}`,
          {
            signal: controller.signal,
            headers: {
              accept: "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
          }
        );

        if (res.status === 404) {
          setNotFound(true);
          setUser(null);
          return;
        }

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `Failed to load user (${res.status})`);
        }

        const json = await res.json();
        const data = json.data ?? json;
        if (!data) {
          setNotFound(true);
          setUser(null);
          return;
        }
        setUser(data);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setProfileError(err.message || "Failed to load profile.");
        setUser(null);
      } finally {
        setProfileLoading(false);
      }
    }

    fetchUser();
    return () => controller.abort();
  }, [username]);

  useEffect(() => {
    if (!user || notFound) {
      setPosts([]);
      return;
    }

    const controller = new AbortController();

    async function fetchPosts() {
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

        const json = await res.json();
        const list = (json.data ?? json.results ?? []) as PostCardPost[];
        setPosts(list);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setPostsError(err.message || "Failed to load posts");
        setPosts([]);
      } finally {
        setPostsLoading(false);
      }
    }

    fetchPosts();
    return () => controller.abort();
  }, [user, notFound]);

  if (profileLoading) {
    return <p className="py-10 text-center">Loading profile...</p>;
  }

  if (notFound) {
    return (
      <div className="py-20 text-center text-gray-500">
        User <span className="font-semibold">{username}</span> not
        found.
      </div>
    );
  }

  if (!user) {
    return (
      <p className="py-10 text-center">
        {profileError ?? "Could not load profile."}
      </p>
    );
  }

  const joined = user.created_at
    ? new Date(user.created_at).toLocaleDateString()
    : "Unknown";

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-10 flex flex-col items-center gap-3">
        <img
          src={
            user.profile_pic ??
            "https://placehold.co/180x180?text=Profile"
          }
          alt={`${user.username}'s avatar`}
          className="h-40 w-40 rounded-full object-cover"
        />

        <h1 className="text-3xl font-semibold">{user.username}</h1>

        <p className="text-sm text-gray-500">Joined: {joined}</p>
      </div>

      {postsError && (
        <p className="mb-4 text-center text-sm text-red-500">
          {postsError}
        </p>
      )}

      {postsLoading && <p className="text-center">Loading posts...</p>}

      {!postsLoading && !postsError && posts.length === 0 && (
        <p className="text-center text-gray-500">No posts found.</p>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
