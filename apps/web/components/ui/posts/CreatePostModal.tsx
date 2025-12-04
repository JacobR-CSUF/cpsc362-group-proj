"use client";

import React, { useState, useRef } from "react";

interface CreatePostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPostCreated: () => void;
}

export default function CreatePostModal({
  isOpen,
  onClose,
  onPostCreated,
}: CreatePostModalProps) {
  // -------------------------
  // STATE VARIABLES
  // -------------------------
  const [caption, setCaption] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const accessToken = localStorage.getItem("accessToken");

  // If modal is closed, render nothing
  if (!isOpen) return null;

  // -------------------------
  // HANDLERS
  // -------------------------
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    if (!["video/mp4", "video/webm", "video/ogg", "video/quicktime", "image/png", "image/jpeg", "image/webp", "image/gif", ].includes(f.type)) {
      setError("Invalid file type.");
      return;
    }

    if (f.size > 10 * 1024 * 1024) {
      setError("File too large (max 10MB).");
      return;
    }

    setPreview(URL.createObjectURL(f));
    setFile(f);
    setError(null);
  };

  const handleSubmit = async () => {
    const accessToken = localStorage.getItem("accessToken");

    if (!accessToken) {
        setError("User is not logged in (missing token).");
        return;
    }

    if (!caption.trim()) {
      setError("Caption cannot be empty.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let image_url = null;

      if (file) {
        const formData = new FormData();
        formData.append("file", file);

        const uploadRes = await fetch("http://localhost:8001/api/v1/media/upload", {
          method: "POST",
          credentials: "include",
          headers: {"Authorization": `Bearer ${accessToken}`},
          body: formData,
        });

        if (!uploadRes.ok) throw new Error("Failed to upload image");

        const data = await uploadRes.json();
        image_url = data.public_url;
      }

      const postRes = await fetch("http://localhost:8001/api/v1/posts", {
        method: "POST",
        credentials: "include",
        headers: {"Authorization": `Bearer ${accessToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ caption, image_url }),
      });

      if (!postRes.ok) throw new Error("Post creation failed");

      setCaption("");
      setFile(null);
      setPreview(null);

      onPostCreated();
      onClose();
    } catch (err: any) {
      setError(err.message);
    }

    setLoading(false);
  };

  // -------------------------
  // JSX (the UI)
  // -------------------------
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-[600px] max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-8 shadow-xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Title */}
        <h2 className="mb-6 text-center text-xl font-medium tracking-[0.7em]">
          LET'S POST SOMETHING
        </h2>

        {/* Upload Box */}
        <div className="mb-6">
          {!preview ? (
            <div
              className="flex h-[420px] w-full cursor-pointer flex-col items-center justify-center rounded-2xl border-4 border-black/40 bg-gray-100/30 hover:bg-gray-200"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="border-4 border-black/40 p-12 rounded-xl">
                <span className="text-6xl text-gray-500">📷</span>
              </div>

              <p className="mt-4 text-gray-500">Click to upload</p>
            </div>
          ) : (
            <div className="relative">
              <img
                src={preview}
                className="w-full max-h-[420px] rounded-xl object-cover border-2 border-black"
              />
              <button
                className="absolute right-2 top-2 rounded-full bg-white px-3 py-1 shadow"
                onClick={() => {
                  setPreview(null);
                  setFile(null);
                }}
              >
                ✖
              </button>
            </div>
          )}

          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/*"
            onChange={handleFileSelect}
          />
        </div>

        {/* Caption */}
        <div className="mb-6">
          <textarea
            className="w-full rounded-xl border-2 border-black/40 p-4 text-lg resize-none"
            rows={5}
            placeholder="What's on your mind?"
            maxLength={2000}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
          ></textarea>
          <p className="mt-1 text-right text-sm text-gray-500">
            {caption.length}/2000
          </p>
        </div>

        {error && <p className="mb-4 text-center text-red-500">{error}</p>}

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full rounded-2xl bg-[#00D9FF] py-3 text-center text-2xl font-bold tracking-[0.7em] text-white shadow-md hover:brightness-105 disabled:opacity-50"
        >
          {loading ? "POSTING..." : "SEND"}
        </button>
      </div>
    </div>
  );
}
