'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import CreatePostModal from '@/components/ui/posts/CreatePostModal';
import { FungoLogo } from './FungoLogo';

interface NavbarProps {
  onPostCreated?: () => void;
}

export const Navbar = ({ onPostCreated }: NavbarProps) => {
  const { user, logout } = useAuth();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const router = useRouter();

  const handlePostCreated = () => {
    setShowCreateModal(false);
    if (onPostCreated) {
      onPostCreated();
    }
  };

  return (
    <>
      <nav className="sticky top-0 z-50 border-b-4 border-green-200 bg-white shadow-sm">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex h-20 items-center justify-between">
            {/* Logo */}
            <button 
              onClick={() => router.push('/feed')}
              className="hover:opacity-80 transition-opacity"
            >
              <FungoLogo />
            </button>

            {/* Center Navigation */}
            <div className="flex items-center gap-8">
              <button
                onClick={() => router.push('/feed')}
                className="text-gray-700 hover:text-green-600 transition-colors"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
              
              <button
                onClick={() => setShowCreateModal(true)}
                className="text-gray-700 hover:text-green-600 transition-colors"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/me')}
                className="flex items-center gap-2 text-gray-700 hover:text-green-600 transition-colors"
              >
                <img
                  src={user?.profile_pic || "https://placehold.co/40x40?text=U"}
                  alt="Profile"
                  className="h-10 w-10 rounded-full border-2 border-gray-200 hover:border-green-500 transition-colors"
                />
              </button>
              
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-red-600 border-2 border-red-500 hover:border-red-600 px-3 py-1.5 rounded-md transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <CreatePostModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onPostCreated={handlePostCreated}
      />
    </>
  );
};