"use client";

import { useState } from "react";
import CreatePostModal from "@/components/ui/posts/CreatePostModal";

export default function ModalTestPage() {
  const [open, setOpen] = useState(false);

  return (
    <div className="p-10">
      <button
        onClick={() => setOpen(true)}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Open modal and test upload
      </button>

      <CreatePostModal
        isOpen={open}
        onClose={() => setOpen(false)}
        onPostCreated={() => console.log("POST CREATED SUCCESSFULLY")}
      />
    </div>
  );
}
