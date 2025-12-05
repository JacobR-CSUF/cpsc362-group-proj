'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';

export default function FeedPage() {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h1 className="text-3xl font-bold mb-4">Feed</h1>
            <p className="text-gray-600 mb-4">
              Welcome, <span className="font-semibold">{user?.username}</span>!
            </p>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Your feed will appear here...</p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}