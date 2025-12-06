'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import CreatePostModal from '@/components/ui/posts/CreatePostModal';

interface NavbarProps {
  onPostCreated?: () => void;
}

export const Navbar = ({ onPostCreated }: NavbarProps) => {
  const { user, logout } = useAuth();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handlePostCreated = () => {
    setShowCreateModal(false);
    if (onPostCreated) {
      onPostCreated();
    }
  };

  return (
    <>
      <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo/Title */}
            <Link href="/feed" className="text-xl font-bold text-gray-900 hover:text-gray-700">
              Social App
            </Link>

            {/* Right side */}
            <div className="flex items-center gap-4">
              {/* Create Post Button */}
              <button
                onClick={() => setShowCreateModal(true)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Create Post
              </button>

              {user && (
                <span className="text-sm text-gray-700">
                  Welcome, <span className="font-semibold">{user.username}</span>
                </span>
              )}
              
              <button
                onClick={logout}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Create Post Modal */}
      <CreatePostModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onPostCreated={handlePostCreated}
      />
    </>
  );
};