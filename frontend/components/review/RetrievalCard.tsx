"use client";

import { useState } from "react";
import { RatingButtons } from "./RatingButtons";
import type { Question, ReviewRating } from "@/lib/types";

export function RetrievalCard({
  question,
  onRated,
}: {
  question: Question;
  onRated: (rating: ReviewRating, givenAnswer: string) => void;
}) {
  const [draftAnswer, setDraftAnswer] = useState("");
  const [revealed, setRevealed] = useState(false);

  return (
    <div className="card">
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
        Retrieval practice
      </p>
      <h2 className="mb-4 text-lg font-semibold text-slate-900">
        {question.question}
      </h2>

      {!revealed ? (
        <>
          <textarea
            value={draftAnswer}
            onChange={(e) => setDraftAnswer(e.target.value)}
            placeholder="Type your answer from memory..."
            rows={4}
            className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button
            onClick={() => setRevealed(true)}
            className="mt-3 w-full rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            Reveal answer
          </button>
        </>
      ) : (
        <>
          <div className="mb-4 space-y-3">
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs font-medium text-slate-400">
                Your answer
              </p>
              <p className="mt-1 text-sm text-slate-700">
                {draftAnswer || "(left blank)"}
              </p>
            </div>
            <div className="rounded-lg bg-emerald-50 p-3">
              <p className="text-xs font-medium text-emerald-600">
                Correct answer
              </p>
              <p className="mt-1 text-sm text-emerald-900">
                {question.answer}
              </p>
            </div>
          </div>
          <p className="mb-2 text-sm font-medium text-slate-600">
            How well did you retrieve this?
          </p>
          <RatingButtons
            onRate={(rating) => onRated(rating, draftAnswer)}
          />
        </>
      )}
    </div>
  );
}
