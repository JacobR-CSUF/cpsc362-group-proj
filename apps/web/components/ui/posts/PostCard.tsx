// apps/web/components/posts/PostCard.tsx

import { PostActions } from "@/components/posts/PostActions";

type PostCardProps = {
    id: string;
    caption: string;
    mediaId: string | null;
    // ...other props
};

export function PostCard({ id, caption, mediaId }: PostCardProps) {
    return (
        <article className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-900">{caption}</p>

            {/* AI actions: subtitles & summary */}
            <PostActions mediaId={mediaId} />
        </article>
    );
}
