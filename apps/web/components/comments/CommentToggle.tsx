"use client";

interface CommentToggleProps {
  count: number;
  onOpenModal: () => void;
}

export function CommentToggle({ count, onOpenModal }: CommentToggleProps) {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 text-sm text-gray-700 hover:text-black"
      onClick={onOpenModal}
      aria-label="Open comments"
    >
      <svg
        aria-hidden="true"
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12c0 3.866-4.03 7-9 7-.92 0-1.81-.1-2.64-.3L3 20l1.47-3.53C3.56 15.47 3 13.8 3 12c0-3.866 4.03-7 9-7s9 3.134 9 7Z" />
      </svg>
      <span>{count}</span>
    </button>
  );
}
