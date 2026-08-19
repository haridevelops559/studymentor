"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Question, ReviewRating } from "@/lib/types";

interface UseDueQuestionsResult {
  questions: Question[];
  current: Question | null;
  isLoading: boolean;
  error: string | null;
  attempted: number;
  correct: number;
  isComplete: boolean;
  rate: (rating: ReviewRating, givenAnswer: string) => Promise<void>;
}

export function useDueQuestions(topicId?: string): UseDueQuestionsResult {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [index, setIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempted, setAttempted] = useState(0);
  const [correct, setCorrect] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    api.questions
      .due(topicId)
      .then((data) => {
        if (!cancelled) setQuestions(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Could not load due questions."
          );
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [topicId]);

  const rate = useCallback(
    async (rating: ReviewRating, givenAnswer: string) => {
      const question = questions[index];
      if (!question) return;

      setAttempted((n) => n + 1);
      if (rating === "good" || rating === "easy") {
        setCorrect((n) => n + 1);
      }

      try {
        await api.reviews.submit({
          question_id: question._id,
          rating,
          given_answer: givenAnswer,
        });
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Could not save that review, but moving on."
        );
      } finally {
        setIndex((i) => i + 1);
      }
    },
    [questions, index]
  );

  return {
    questions,
    current: questions[index] ?? null,
    isLoading,
    error,
    attempted,
    correct,
    isComplete: !isLoading && index >= questions.length,
    rate,
  };
}
