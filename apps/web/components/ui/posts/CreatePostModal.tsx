"use client";

import React, { useEffect, useRef, useState } from "react";
import { AxiosError } from "axios";
import api from "@/lib/api";
import { MediaViewerModal } from "@/components/media/MediaViewerModal";
import { UnsafeContentModal } from "@/components/ui/common/UnsafeContentModal";

function formatAxiosError(err: any): string {
  const axiosErr = err as AxiosError<any>;
  const data = axiosErr.response?.data;

  const detail = data?.detail ?? data?.message ?? data?.error;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => d?.msg || d?.message || JSON.stringify(d))
      .join(" | ");
  }
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return axiosErr.message || "Request failed.";
}

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
  const [uploadedMediaId, setUploadedMediaId] = useState<string | null>(null);
  const [uploadedMediaUrl, setUploadedMediaUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [mounted, setMounted] = useState(false);

  // MediaModal
  const [mediaModalOpen, setMediaModalOpen] = useState(false);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<"image" | "video" | null>(null);

  // UnsafeContentModal
  const [unsafeModalOpen, setUnsafeModalOpen] = useState(false);
  const [unsafeReason, setUnsafeReason] = useState<string>("");
  const [unsafeMediaType, setUnsafeMediaType] = useState<"image" | "video">("image");


  // Avoid SSR/client mismatches for any browser-only APIs used in this modal
  useEffect(() => {
    setMounted(true);
  }, []);

  // If modal is closed, render nothing
  if (!isOpen || !mounted) return null;

  // -------------------------
  // HANDLERS
  // -------------------------
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    if (!["video/mp4", "video/webm", "video/ogg", "video/quicktime", "image/png", "image/jpeg", "image/webp", "image/gif"].includes(f.type)) {
      setError("Invalid file type.");
      return;
    }

    if (f.size > 50 * 1024 * 1024) {
      setError("File too large (max 50MB).");
      return;
    }

    setPreview(URL.createObjectURL(f));
    setFile(f);
    setError(null);
  };

  const handleSubmit = async () => {
    const accessToken = localStorage.getItem("access_token");

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
      let mediaId = uploadedMediaId;
      let mediaType: "image" | "video" | null = null;

      // If a new file is selected, upload it first
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("caption", caption);

        const uploadRes = await api.post("/api/v1/media/upload", formData, {
          headers: {
            // Explicitly override default JSON header for multipart
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${accessToken}`,
          },
          withCredentials: true,
        });

        const data = uploadRes.data;

        // Check for unsafe-content flag from backend
        if (
          uploadRes.status === 400 &&
          typeof data?.detail === "string" &&
          (data.detail.includes("unsafe") ||
            data.detail.includes("flagged") ||
            data.detail.includes("inappropriate"))
        ) {
          setUnsafeReason(data.detail);
          setUnsafeMediaType(file.type.startsWith("video/") ? "video" : "image");
          setUnsafeModalOpen(true);
          setFile(null);
          setPreview(null);
          setLoading(false);
          return; // stop execution
        }

        mediaId = data?.data?.id ?? null;
        setUploadedMediaId(mediaId);
        setUploadedMediaUrl(data?.data?.public_url ?? null);
        mediaId = data?.data?.id || null;
        setUploadedMediaId(mediaId);
        setUploadedMediaUrl(data?.data?.public_url || null);
        mediaType = file.type.startsWith("video/") ? "video" : "image";

        // Moderate uploaded media via backend proxy (images and videos)
        try {
          const modRes = await api.post(
            "/api/v1/media/moderate",
            { file_url: data?.data?.public_url, media_type: mediaType, user: undefined },
            {
              headers: { Authorization: `Bearer ${accessToken}` },
              withCredentials: true,
            }
          );
          const modData = modRes.data;
          if (!modData?.is_safe) {
            // cleanup uploaded media
            if (mediaId) {
              try {
                await api.delete(`/api/v1/media/${mediaId}`, {
                  headers: { Authorization: `Bearer ${accessToken}` },
                  withCredentials: true,
                });
              } catch {
                // ignore cleanup errors
              }
              setUnsafeReason(
                modData?.reason ||
                "Sensitive Content. Failed to upload. Action has been reported to the administrators."
              );
              setUnsafeMediaType("image"); 
              setUnsafeModalOpen(true);
              setFile(null);
              setPreview(null);
              setUploadedMediaId(null);
              setUploadedMediaUrl(null);
              setLoading(false);
              return;
            }
          } catch (modErr: any) {
            try {
              await api.delete(`/api/v1/media/${mediaId}`, {
                headers: { Authorization: `Bearer ${accessToken}` },
                withCredentials: true,
              });
            } catch {
              // ignore cleanup errors
            }
            setUnsafeReason(
              "Sensitive Content. Failed to upload. Action has been reported to the administrators."
            );
            setUnsafeMediaType("image");
            setUnsafeModalOpen(true);
            setFile(null);
            setPreview(null);
            setUploadedMediaId(null);
            setUploadedMediaUrl(null);
            setLoading(false);
            return;
          }
        }
      }

      await api.post(
        "/api/v1/posts",
        { caption, media_id: mediaId },
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          withCredentials: true,
        }
      );

      setCaption("");
      setFile(null);
      setPreview(null);
      setUploadedMediaId(null);
      setUploadedMediaUrl(null);

      onPostCreated();
      onClose();
    } catch (err: any) {
      setError(formatAxiosError(err));
    }

    setLoading(false);
  };

  // -------------------------
  // JSX (the UI)
  // -------------------------
  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <div
          className="w-[600px] max-h-[90vh] overflow-y-auto rounded-2xl bg-white border-4 border-green-300 p-8 shadow-xl relative no-scrollbar"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Title */}
          <h2 className="mb-6 text-center text-xl font-medium tracking-[0.7em] text-green-700">
            LET'S POST SOMETHING
          </h2>

          {/* Upload Box */}
          <div className="mb-6">
            {!preview ? (
              <div
                className="flex h-[420px] w-full cursor-pointer flex-col items-center justify-center rounded-2xl border-4 border-green-300 bg-green-50 hover:bg-green-100 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="border-4 border-green-400 p-12 rounded-xl bg-white">
                  <span className="text-6xl">📷</span>
                </div>

                <p className="mt-4 text-green-700 font-medium">Click to upload</p>
              </div>
            ) : (
              <div
                className="relative mb-3 overflow-hidden rounded-2xl border-4 border-green-300 bg-black/5 cursor-pointer"
                onClick={() => {
                  setMediaUrl(preview!);
                  setMediaType(file?.type.startsWith("video/") ? "video" : "image");
                  setMediaModalOpen(true);
                }}
              >
                {/* IMAGE or VIDEO PREVIEW */}
                {file?.type.startsWith("video/") ? (
                  <div className="relative">
                    <video
                      src={preview}
                      className="max-h-[420px] w-full object-cover"
                      muted
                      loop
                      playsInline
                      controls
                    />
                    {/* Overlay to block play/pause clicks but still open modal */}
                    <div
                      className="absolute inset-0 cursor-pointer"
                      onClick={() => {
                        setMediaUrl(preview);
                        setMediaType("video");
                        setMediaModalOpen(true);
                      }}
                    />
                  </div>
                ) : (
                  <img
                    src={preview}
                    className="max-h-[420px] w-full object-cover select-none cursor-pointer"
                    onClick={() => {
                      setMediaUrl(preview);
                      setMediaType("image");
                      setMediaModalOpen(true);
                    }}
                  />
                )}

                {/* CLEAR BUTTON */}
                <button
                  className="absolute right-2 top-2 z-10 rounded-full bg-red-500 hover:bg-red-600 px-3 py-1 text-white font-semibold shadow transition-colors"
                  onClick={(e) => {
                    e.stopPropagation(); // prevent modal from opening
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
              accept="image/*, video/*"
              onChange={handleFileSelect}
            />
          </div>

          {/* Caption */}
          <div className="mb-6">
            <textarea
              className="w-full rounded-xl border-2 border-green-300 focus:border-green-500 focus:ring-2 focus:ring-green-200 p-4 text-lg resize-none outline-none transition-all"
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
            className="w-full rounded-2xl bg-green-600 hover:bg-green-700 py-3 text-center text-2xl font-bold tracking-[0.7em] text-white shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "POSTING..." : "SEND"}
          </button>
        </div>
      </div>

      {/* Media Viewer Modal */}
      <MediaViewerModal
        isOpen={mediaModalOpen}
        onClose={() => setMediaModalOpen(false)}
        mediaUrl={mediaUrl}
        mediaType={mediaType}
      />

      {/* Unsafe Content Modal */}
      <UnsafeContentModal
        open={unsafeModalOpen}
        onClose={() => setUnsafeModalOpen(false)}
        mediaType={unsafeMediaType}
        reason={unsafeReason}
      />
    </>
  );
}
