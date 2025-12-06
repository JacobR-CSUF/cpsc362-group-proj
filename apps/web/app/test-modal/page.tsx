"use client";

import { useState } from "react";
import CreatePostModal from "@/components/ui/posts/CreatePostModal";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";

export default function ModalTestPage() {
  const [open, setOpen] = useState(false);

  // Quick harness to test the media viewer + captions
  const [viewerOpen, setViewerOpen] = useState(false);
  const [mediaUrl, setMediaUrl] = useState("");
  const [transcriptionUrl, setTranscriptionUrl] = useState("");

  return (
    <div className="space-y-6 p-10">
      <div className="space-y-3 rounded-lg border border-black/10 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Create Post Modal</h2>
        <button
          onClick={() => setOpen(true)}
          className="rounded bg-blue-600 px-4 py-2 text-white shadow hover:bg-blue-500"
        >
          Open modal and test upload
        </button>
      </div>

      <div className="space-y-3 rounded-lg border border-black/10 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Media Viewer (captions)</h2>
        <p className="text-sm text-gray-600">
          Paste a video URL and optional VTT/SRT URL to verify captions in the modal.
        </p>
        <div className="space-y-2">
          <input
            type="text"
            placeholder="Video URL"
            className="w-full rounded border border-black/15 px-3 py-2 text-sm"
            value={mediaUrl}
            onChange={(e) => setMediaUrl(e.target.value)}
          />
          <input
            type="text"
            placeholder="Transcription (VTT/SRT) URL"
            className="w-full rounded border border-black/15 px-3 py-2 text-sm"
            value={transcriptionUrl}
            onChange={(e) => setTranscriptionUrl(e.target.value)}
          />
        </div>
        <button
          type="button"
          disabled={!mediaUrl}
          onClick={() => setViewerOpen(true)}
          className="rounded bg-black px-4 py-2 text-white disabled:cursor-not-allowed disabled:bg-black/50"
        >
          Open media viewer
        </button>
      </div>

      <CreatePostModal
        isOpen={open}
        onClose={() => setOpen(false)}
        onPostCreated={() => console.log("POST CREATED SUCCESSFULLY")}
      />

      <MediaViewerModal
        isOpen={viewerOpen}
        onClose={() => setViewerOpen(false)}
        mediaUrl={mediaUrl || null}
        mediaType="video"
        transcriptionUrl={transcriptionUrl || null}
      />
    </div>
  );
}
