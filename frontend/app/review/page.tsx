"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { RetrievalCard } from "@/components/review/RetrievalCard";
import { useDueQuestions } from "@/hooks/useDueQuestions";
import { score_session_label } from "@/lib/utils";

function ReviewContent() {
  const searchParams = useSearchParams();
  const topicId = searchParams.get("subject") ?? undefined;

  const { current, isLoading, error, attempted, correct, isComplete, rate } =
    useDueQuestions(topicId);

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading due reviews...</p>;
  }

  if (error && !current) {
    return (
      <div className="card border-amber-200 bg-amber-50 text-sm text-amber-800">
        {error}
      </div>
    );
  }

  if (isComplete || !current) {
    return (
      <div className="card text-center">
        <p className="text-3xl">🎉</p>
        <h2 className="mt-2 text-lg font-semibold text-slate-900">
          All caught up
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          {attempted > 0
            ? `You reviewed ${attempted} question${
                attempted === 1 ? "" : "s"
              } — ${score_session_label(attempted, correct)}.`
            : "No reviews are due right now. Nice work staying on top of it."}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span>Retrieval practice</span>
        <span>{attempted} reviewed this session</span>
      </div>
      <RetrievalCard
        key={current._id}
        question={current}
        onRated={(rating, givenAnswer) => rate(rating, givenAnswer)}
      />
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading...</p>}>
      <ReviewContent />
    </Suspense>
  );
}
