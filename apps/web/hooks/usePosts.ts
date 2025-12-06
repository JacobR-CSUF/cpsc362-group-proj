// hooks/usePosts.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Post } from '@/types';

// Backend response structure
interface PostsResponse {
  meta: {
    total_count: number;
    page: number;
    limit: number;
    has_next: boolean;
    has_previous: boolean;
    next_page: number | null;
    previous_page: number | null;
  };
  results: Post[];
}

export const usePosts = (page: number = 1, limit: number = 20) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const fetchPosts = useCallback(async () => {
    console.log('Fetching posts...');
    setLoading(true);
    setError(null);

    try {
      console.log('Making API request to /api/v1/posts');
      const response = await api.get<PostsResponse>('/api/v1/posts', {
        params: { page, limit }
      });

      console.log('Posts received:', response.data.results.length);
      setPosts(response.data.results);
      setTotalCount(response.data.meta.total_count);
      setHasNext(response.data.meta.has_next);
      setHasPrev(response.data.meta.has_previous);
    } catch (err: any) {
      console.error('Failed to fetch posts:', err);
      setError(err.response?.data?.detail || 'Failed to load posts');
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, [page, limit]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const refreshPosts = useCallback(() => {
    return fetchPosts();
  }, [fetchPosts]);

  return {
    posts,
    loading,
    error,
    totalCount,
    hasNext,
    hasPrev,
    refreshPosts,
  };
};