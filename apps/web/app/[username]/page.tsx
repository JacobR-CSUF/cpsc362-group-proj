"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PostCard, type PostCardPost } from "@/components/ui/posts/PostCard";
import { Navbar } from "@/components/layout/Navbar";
import { useAuth } from "@/hooks/useAuth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

type UserProfile = {
  id: string;
  username: string;
  created_at: string;
  profile_pic?: string | null;
};

export default function UserProfilePage() {
  const params = useParams();
  const router = useRouter();
  const username = params.username as string;
  const { user: currentUser } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [posts, setPosts] = useState<PostCardPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  
  useEffect(() => {
    if (currentUser && currentUser.username === username) {
      router.replace('/me');
    }
  }, [currentUser, username, router]);

  useEffect(() => {
    if (!username) return;

    async function loadUserProfile() {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("access_token");
    
        const postsRes = await fetch(
          `${API_BASE}/api/v1/posts?page=1&limit=100`,
          {
            headers: {
              accept: "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
          }
        );

        if (!postsRes.ok) {
          throw new Error("Failed to load posts");
        }

        const postsData = await postsRes.json();
        const allPosts = (postsData.data ?? postsData.results ?? []) as PostCardPost[];
        
        // Filter posts by this username
        const userPosts = allPosts
          .filter((p) => p.author.username === username)
          .map((p) => ({
            ...p,
            media: p.media
              ? { ...p.media, transcription_url: p.media.transcription_url ?? null }
              : null,
          }));
        
        if (userPosts.length === 0) {
          throw new Error("User not found");
        }

        // Get user info from the first post
        const userInfo = userPosts[0].author;
        setProfile({
          id: userInfo.user_id,
          username: userInfo.username,
          profile_pic: userInfo.profile_pic,
          created_at: userPosts[0].created_at, // Approximate
        });

        setPosts(userPosts);
      } catch (err: any) {
        setError(err.message || "Failed to load profile");
      } finally {
        setLoading(false);
      }
    }

    loadUserProfile();
  }, [username]);

  if (loading) {
    return (
      <div className="min-h-screen bg-green-100">
        <Navbar />
        <p className="p-10 text-center text-green-700">Loading profile...</p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-green-100">
        <Navbar />
        <div className="p-10 text-center">
          <p className="text-red-500">{error || "User not found"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-green-100">
      <Navbar />
      
      <div className="w-full px-2 py-10 sm:px-4">
        <div className="mb-10 flex flex-col items-center gap-3">
          <img
            src={profile.profile_pic ?? "https://placehold.co/180x180?text=Profile"}
            alt={`${profile.username}'s avatar`}
            className="h-40 w-40 rounded-full object-cover border-4 border-green-300"
          />

          <h1 className="text-3xl font-semibold text-gray-800">{profile.username}</h1>
        </div>

        <hr className="-mx-4 my-8 border-t-2 border-green-300" />

        <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">Posts</h2>

        {posts.length === 0 && (
          <p className="text-center text-gray-600">No posts yet.</p>
        )}

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 justify-items-stretch">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      </div>
    </div>
  );
}
