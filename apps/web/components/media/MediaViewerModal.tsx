"use client";
import { useEffect, useRef, useState } from "react";
import { Captions } from "./Captions";

interface MediaViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaUrl: string | null;
  mediaType: "image" | "video" | null;
  transcriptionUrl?: string | null;
  transcription_url?: string | null; // allow snake_case payloads directly
  mediaId?: string | null;
  sourceLabel?: string | null;
}

export function MediaViewerModal({
  isOpen,
  onClose,
  mediaUrl,
  mediaType,
  transcriptionUrl = null,
  transcription_url = null,
  mediaId = null,
  sourceLabel = null,
}: MediaViewerModalProps) {
  const resolvedTranscriptionUrl = transcription_url ?? transcriptionUrl ?? null;
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [currentTime, setCurrentTime] = useState(0);
  const [captions, setCaptions] = useState<string>("");
  const [captionsError, setCaptionsError] = useState<string | null>(null);
  const [captionsLoading, setCaptionsLoading] = useState(false);
  const [captionsStatus, setCaptionsStatus] = useState<string>("idle");

  const dragging = useRef(false);
  const last = useRef({ x: 0, y: 0 });

  const pinchData = useRef<{
    active: boolean;
    startDistance: number;
    startScale: number;
  }>({ active: false, startDistance: 0, startScale: 1 });

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    // Reset transform + captions when modal closes/opens
    if (!isOpen) {
      setScale(1);
      setPos({ x: 0, y: 0 });
      setCurrentTime(0);
      setCaptions("");
      setCaptionsError(null);
      setCaptionsLoading(false);
      setCaptionsStatus("idle");
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
  }, [isOpen]);

  useEffect(() => {
    // Fetch captions when modal is open and a transcription URL exists (even if mediaType is mis-set)
    if (!isOpen || !resolvedTranscriptionUrl) {
      setCaptions("");
      setCaptionsError(null);
      setCaptionsLoading(false);
      setCaptionsStatus("none");
      return;
    }

    const controller = new AbortController();
    const fetchCaptions = async () => {
      setCaptionsLoading(true);
      setCaptionsError(null);
      setCaptionsStatus("loading");
      try {
        const res = await fetch(resolvedTranscriptionUrl, { signal: controller.signal, mode: "cors" });
        if (!res.ok) throw new Error(`Failed to load captions (${res.status})`);
        const text = await res.text();
        setCaptions(text);
        setCaptionsStatus(text.trim() ? "ready" : "empty");
      } catch (err: any) {
        if (controller.signal.aborted) return;
        setCaptionsError(err?.message || "Unable to load captions");
        setCaptions("");
        setCaptionsStatus("error");
      } finally {
        if (!controller.signal.aborted) setCaptionsLoading(false);
      }
    };

    fetchCaptions();
    return () => controller.abort();
  }, [isOpen, mediaType, resolvedTranscriptionUrl]);

  if (!isOpen || !mediaUrl || !mediaType) return null;

  function handleWheel(e: React.WheelEvent) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale((s) => Math.min(Math.max(0.5, s + delta), 5));
  }

  function handleMouseDown(e: React.MouseEvent) {
    dragging.current = true;
    last.current = { x: e.clientX, y: e.clientY };
  }

  function handleMouseMove(e: React.MouseEvent) {
    if (!dragging.current) return;
    const dx = e.clientX - last.current.x;
    const dy = e.clientY - last.current.y;
    last.current = { x: e.clientX, y: e.clientY };
    setPos((p) => ({ x: p.x + dx, y: p.y + dy }));
  }

  function handleMouseUp() {
    dragging.current = false;
  }

  function getDistance(t1: Touch, t2: Touch) {
    const dx = t1.clientX - t2.clientX;
    const dy = t1.clientY - t2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function handleTouchStart(e: React.TouchEvent) {
    if (e.touches.length === 2) {
      const t1 = e.touches[0] as unknown as Touch;
      const t2 = e.touches[1] as unknown as Touch;
      const dist = getDistance(t1, t2);
      pinchData.current = {
        active: true,
        startDistance: dist,
        startScale: scale,
      };
    }
  }

  function handleTouchMove(e: React.TouchEvent) {
    if (e.touches.length === 2 && pinchData.current.active) {
      e.preventDefault();
      const t1 = e.touches[0] as unknown as Touch;
      const t2 = e.touches[1] as unknown as Touch;
      const dist = getDistance(t1, t2);
      const ratio = dist / pinchData.current.startDistance;
      const newScale = pinchData.current.startScale * ratio;
      setScale(Math.min(Math.max(0.5, newScale), 5));
    }
  }

  function handleTouchEnd() {
    pinchData.current.active = false;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative h-[90vh] w-[90vw] overflow-hidden rounded-[10px] bg-black/80 p-2"
        onClick={(e) => e.stopPropagation()}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-3 top-3 z-10 rounded-full bg-black/70 px-2 py-1 text-sm text-white hover:bg-black"
        >
          Close
        </button>

        <div className="flex h-full w-full items-center justify-center">
          <div
            style={{
              transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
              transition:
                pinchData.current.active || dragging.current
                  ? "none"
                  : "transform 0.1s ease-out",
            }}
          >
            {mediaType === "image" ? (
              <img
                src={mediaUrl}
                alt="Post media"
                className="max-h-[80vh] max-w-[85vw] object-contain"
                draggable={false}
                onDragStart={(e) => e.preventDefault()}
              />
            ) : (
              <div className="relative max-h-[80vh] max-w-[85vw]">
                <video
                  src={mediaUrl}
                  controls
                  autoPlay
                  className="max-h-[80vh] max-w-[85vw] object-contain"
                  draggable={false}
                  onDragStart={(e) => e.preventDefault()}
                  onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                />

                {captionsLoading && (
                  <div className="pointer-events-none absolute inset-0 flex items-end justify-center pb-4">
                    <span className="rounded-md bg-black/70 px-3 py-1 text-xs text-white">
                      Loading captions...
                    </span>
                  </div>
                )}

                {captionsError && (
                  <div className="pointer-events-none absolute inset-0 flex items-end justify-center pb-4">
                    <span className="rounded-md bg-black/70 px-3 py-1 text-xs text-red-200">
                      {captionsError}
                    </span>
                  </div>
                )}

                {!captionsLoading && !captionsError && captions && (
                  <Captions subtitlesText={captions} currentTime={currentTime} />
                )}

              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
