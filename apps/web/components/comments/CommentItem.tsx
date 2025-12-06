"use client";

import Link from "next/link";
import { Comment } from "@/hooks/useComments";
import { formatRelativeTime } from "@/hooks/useComments";
import { useEffect, useState } from "react";

interface CommentItemProps {
    comment: Comment;
    canDelete: boolean;
    onDelete: () => void;
}

export function CommentItem({ comment, canDelete, onDelete }: CommentItemProps) {
    const { author } = comment;
    const initial = author.username?.[0]?.toUpperCase() ?? "?";
    const [nowMs, setNowMs] = useState(() => Date.now());

    // Tick every second so relative time updates live
    useEffect(() => {
        const id = setInterval(() => setNowMs(Date.now()), 1000);
        return () => clearInterval(id);
    }, []);

    return (
        <div className="flex gap-3 border-b border-black/10 pb-3 last:border-b-0">
            {/* Avatar */}
            <div className="mt-1 h-10 w-10 flex-shrink-0 rounded-full bg-gray-200 flex items-center justify-center text-sm font-semibold">
                {initial}
            </div>

            {/* Body */}
            <div className="flex-1">
                <div className="flex items-center gap-2 text-sm">
                    <Link
                        href={`/${author.username}`}
                        className="font-semibold hover:underline"
                    >
                        {author.username}
                    </Link>

                    <span className="text-xs text-gray-500">
                        {formatRelativeTime(comment.created_at, nowMs)}
                    </span>

                    {/* Delete button (right-aligned) */}
                    {canDelete && (
                        <button
                            onClick={onDelete}
                            className="ml-auto text-xs text-red-500 hover:underline"
                        >
                            Delete
                        </button>
                    )}
                </div>

                <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                    {comment.content}
                </p>
            </div>
        </div>
    );
}
