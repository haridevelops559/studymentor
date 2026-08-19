/**
 * Types mirroring the backend Pydantic schemas (backend/app/schemas/*.py).
 * Keeping these hand-in-sync is a deliberate, simple choice for the MVP;
 * see docs/API.md for the endpoint-by-endpoint contract.
 */

export interface Subject {
  _id: string;
  name: string;
  description?: string | null;
  created_at: string;
}

export interface Topic {
  _id: string;
  subject_id: string;
  name: string;
}

export interface Note {
  _id: string;
  topic_id: string;
  title: string;
  content: string;
  cues: string[];
  summary?: string | null;
  created_at: string;
  updated_at: string;
}

export type QuestionType = "recall" | "cloze" | "application";

export interface Question {
  _id: string;
  topic_id: string;
  question: string;
  answer: string;
  type: QuestionType;
  created_at: string;
  last_reviewed?: string | null;
  next_review: string;
  review_count: number;
  correct_count: number;
  difficulty: number;
}

export type ReviewRating = "again" | "hard" | "good" | "easy";

export interface Review {
  _id: string;
  question_id: string;
  user_id: string;
  rating: ReviewRating;
  given_answer: string;
  reviewed_at: string;
  next_review: string;
}

export interface FeynmanCheckResult {
  covered: string[];
  missing: string[];
  coverage_ratio: number;
}

export interface FeynmanExplanation {
  _id: string;
  topic_id: string;
  user_id: string;
  explanation: string;
  checklist: string[];
  created_at: string;
  check_result: FeynmanCheckResult;
}

export interface StudySession {
  _id: string;
  user_id: string;
  started_at: string;
  ended_at?: string | null;
  duration_seconds?: number | null;
  planned_activities: string[];
  questions_attempted: number;
  questions_correct: number;
  topics_reviewed: string[];
}

export interface DashboardResponse {
  minutes_studied_today: number;
  reviews_completed_today: number;
  recall_percent_today: number;
  topics_touched_today: number;
  due: {
    overdue: number;
    due_today: number;
    upcoming: number;
  };
  retention_by_topic: Record<string, number>;
  weakest_topics: { topic_id: string; retention: number }[];
}
