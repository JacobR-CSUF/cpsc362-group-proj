"use client";

import { useEffect, useMemo, useState } from "react";

type Cue = { start: number; end: number; text: string };

function toSeconds(time: string): number {
  const parts = time.replace(",", ".").split(":");
  let seconds = 0;
  for (const p of parts) seconds = seconds * 60 + parseFloat(p);
  return seconds;
}

function parseCaptions(text: string): Cue[] {
  const blocks = text
    .replace(/\r/g, "")
    .split(/\n\n+/)
    .map((block) => block.trim())
    .filter(Boolean);

  return blocks
    .map((block) => {
      const lines = block.split("\n");
      if (lines.length < 2) return null;

      const timeLine = lines[0].includes("-->") ? lines[0] : lines[1];
      const [start, end] = timeLine.split("-->").map((t) => t.trim());
      const textLines = lines[0].includes("-->") ? lines.slice(1) : lines.slice(2);

      return {
        start: toSeconds(start),
        end: toSeconds(end),
        text: textLines.join("\n"),
      };
    })
    .filter(Boolean) as Cue[];
}

interface CaptionsProps {
  subtitlesText: string; // raw VTT/SRT file text
  currentTime: number; // video time in seconds
}

export function Captions({ subtitlesText, currentTime }: CaptionsProps) {
  const cues = useMemo(() => parseCaptions(subtitlesText), [subtitlesText]);
  const [active, setActive] = useState<string>("");

  useEffect(() => {
    if (!cues.length) return;
    const cue = cues.find((c) => currentTime >= c.start && currentTime <= c.end);
    setActive(cue ? cue.text : "");
  }, [currentTime, cues]);

  if (!active) return null;

  return (
    <div className="captions-overlay pointer-events-none fixed inset-0 z-40 flex items-end justify-center pb-[6%] px-4">
      <div className="captions-text max-w-[80%] rounded-md bg-black/80 px-3 py-2 text-center text-white shadow-lg backdrop-blur-sm">
        <span className="whitespace-pre-wrap text-sm leading-relaxed md:text-base">{active}</span>
      </div>
    </div>
  );
}
