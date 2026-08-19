"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

export function NewSubjectForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await api.subjects.create(name.trim(), description.trim() || undefined);
      setName("");
      setDescription("");
      router.refresh();
    } catch {
      setError("Couldn't create the subject. Is the backend running?");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Subject name (e.g. Operating Systems)"
        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        required
      />
      <input
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (optional)"
        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adding..." : "Add subject"}
      </Button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}
