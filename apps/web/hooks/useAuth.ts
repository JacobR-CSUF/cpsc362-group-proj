'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';
import { getToken, removeToken, isAuthenticated } from '@/lib/auth';
import type { User } from '@/types';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuth, setIsAuth] = useState(false);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    if (!isAuthenticated()) {
      setLoading(false);
      setIsAuth(false);
      return;
    }

    try {
      const userData = await authAPI.getMe();
      setUser(userData);
      setIsAuth(true);
    } catch (error) {
      console.error('Failed to fetch user:', error); // Keep this one for debugging
      removeToken();
      setUser(null);
      setIsAuth(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const logout = useCallback(() => {
    authAPI.logout();
    setUser(null);
    setIsAuth(false);
    router.push('/login');
  }, [router]);

  const refetchUser = useCallback(() => {
    return fetchUser();
  }, [fetchUser]);

  return {
    user,
    loading,
    isAuthenticated: isAuth,
    logout,
    refetchUser,
  };
};