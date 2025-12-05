"use client";

import { useState } from "react";

interface LikeButtonProps {
  initialCount?: number;
}

export function LikeButton({ initialCount = 0 }: LikeButtonProps) {
  const [liked, setLiked] = useState(false);
  const [count, setCount] = useState(initialCount);

  const toggle = () => {
    setLiked((prev) => !prev);
    setCount((c) => (liked ? c - 1 : c + 1));
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="inline-flex items-center gap-1 text-sm text-gray-700 hover:text-red-600"
    >
      <span>{liked ? "❤️" : "♡"}</span>
      <span>{count}</span>
    </button>
  );
}
