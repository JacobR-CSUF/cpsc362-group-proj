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
    >
      <span>💬</span>
      <span>{count}</span>
    </button>
  );
}
