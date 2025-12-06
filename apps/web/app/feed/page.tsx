// app/feed/page.tsx
'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Navbar } from '@/components/layout/Navbar';
import { PostCard, PostCardPost } from '@/components/ui/posts/PostCard';
import { usePosts } from '@/hooks/usePosts';
import type { Post } from '@/types';

// Map Post to PostCardPost
function mapToPostCardPost(post: Post): PostCardPost {
  return {
    id: post.id,
    caption: post.caption,
    author: {
      user_id: post.author.user_id,
      username: post.author.username,
      profile_pic: post.author.profile_pic,
    },
    media: post.media ? {
      id: post.media.id,
      public_url: post.media.public_url,
      media_type: post.media.media_type as 'image' | 'video',
      caption: post.media.caption,
    } : null,
    created_at: post.created_at,
    likes_count: post.likes_count,
  };
}

export default function FeedPage() {
  const { posts, loading, error, refreshPosts } = usePosts();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-green-100">
        <Navbar onPostCreated={refreshPosts} />
        
        <main className="mx-auto max-w-2xl px-4 py-8">
          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-lg text-green-800 font-semibold">Loading posts...</div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
              <p className="font-semibold">Error loading posts</p>
              <p className="text-sm">{error}</p>
              <button
                onClick={refreshPosts}
                className="mt-2 text-sm text-green-600 underline hover:no-underline"
              >
                Try again
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && posts && posts.length === 0 && (
            <div className="rounded-lg bg-white border-2 border-green-300 p-8 text-center shadow-sm">
              <p className="text-lg text-gray-600">No posts yet</p>
              <p className="mt-2 text-sm text-gray-500">
                Be the first to create a post!
              </p>
            </div>
          )}

          {/* Posts List */}
          {!loading && !error && posts && posts.length > 0 && (
            <div className="space-y-6">
              {posts.map((post) => (
                <PostCard key={post.id} post={mapToPostCardPost(post)} />
              ))}
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}