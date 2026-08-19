"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { api, ApiError } from "@/lib/api";
import type { FeynmanExplanation, Topic } from "@/lib/types";

function FeynmanContent() {
  const searchParams = useSearchParams();
  const subjectId = searchParams.get("subject");

  const [topics, setTopics] = useState<Topic[]>([]);
  const [topicId, setTopicId] = useState<string | null>(null);
  const [checklist, setChecklist] = useState<string[]>(["", "", ""]);
  const [explanation, setExplanation] = useState("");
  const [result, setResult] = useState<FeynmanExplanation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!subjectId) return;
    api.subjects
      .topics(subjectId)
      .then((data) => {
        setTopics(data);
        if (data.length > 0) setTopicId(data[0]._id);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load topics.")
      );
  }, [subjectId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topicId || !explanation.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await api.feynman.submit({
        topic_id: topicId,
        explanation: explanation.trim(),
        checklist: checklist.map((c) => c.trim()).filter(Boolean),
      });
      setResult(created);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!subjectId) {
    return (
      <p className="text-sm text-slate-500">
        Pick a subject from the{" "}
        <a href="/subjects" className="text-brand-600 hover:underline">
          Subjects
        </a>{" "}
        page to start a Feynman explanation session.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Feynman mode
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Explain the concept as if teaching it to someone who has never
          encountered it. Self-explanation helps surface the gaps in your own
          understanding.
        </p>
      </div>

      {error && (
        <div className="card border-amber-200 bg-amber-50 text-sm text-amber-800">
          {error}
        </div>
      )}

      {topics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {topics.map((topic) => (
            <button
              key={topic._id}
              onClick={() => setTopicId(topic._id)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                topicId === topic._id
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-600 border border-slate-300 hover:bg-slate-50"
              }`}
            >
              {topic.name}
            </button>
          ))}
        </div>
      )}

      <Card>
        <CardHeader title="Key ideas to cover (optional)" />
        <div className="space-y-2">
          {checklist.map((item, i) => (
            <input
              key={i}
              value={item}
              onChange={(e) => {
                const next = [...checklist];
                next[i] = e.target.value;
                setChecklist(next);
              }}
              placeholder={`Key idea ${i + 1}`}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Your explanation" />
        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            rows={8}
            placeholder="Explain it in your own words..."
            className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <Button type="submit" disabled={isSubmitting || !topicId}>
            {isSubmitting ? "Checking..." : "Submit explanation"}
          </Button>
        </form>
      </Card>

      {result && (
        <Card>
          <CardHeader title="Self-check" />
          <ProgressBar
            percent={Math.round(result.check_result.coverage_ratio * 100)}
            label="Coverage"
            colorClassName="bg-brand-500"
          />
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-medium text-emerald-600">
                Covered
              </p>
              <ul className="space-y-1 text-sm text-slate-700">
                {result.check_result.covered.length === 0 && (
                  <li className="text-slate-400">Nothing detected yet</li>
                )}
                {result.check_result.covered.map((item) => (
                  <li key={item}>✓ {item}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-xs font-medium text-red-600">Missing</p>
              <ul className="space-y-1 text-sm text-slate-700">
                {result.check_result.missing.length === 0 && (
                  <li className="text-slate-400">Nothing missing 🎉</li>
                )}
                {result.check_result.missing.map((item) => (
                  <li key={item}>— {item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export default function FeynmanPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading...</p>}>
      <FeynmanContent />
    </Suspense>
  );
}
