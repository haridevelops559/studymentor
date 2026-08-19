import type {
  DashboardResponse,
  FeynmanExplanation,
  Question,
  Review,
  ReviewRating,
  StudySession,
  Subject,
  Topic,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    // Dashboard-style data should stay fresh; callers that want caching can
    // override this per-call.
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new ApiError(
      `${options.method ?? "GET"} ${path} failed: ${response.status} ${body}`,
      response.status
    );
  }

  return (await response.json()) as T;
}

export const api = {
  dashboard: {
    get: () => request<DashboardResponse>("/dashboard"),
  },

  subjects: {
    list: () => request<Subject[]>("/subjects"),
    create: (name: string, description?: string) =>
      request<Subject>("/subjects", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      }),
    topics: (subjectId: string) =>
      request<Topic[]>(`/subjects/${subjectId}/topics`),
    createTopic: (subjectId: string, name: string) =>
      request<Topic>(`/subjects/${subjectId}/topics`, {
        method: "POST",
        body: JSON.stringify({ subject_id: subjectId, name }),
      }),
  },

  questions: {
    listByTopic: (topicId: string) =>
      request<Question[]>(`/questions?topic_id=${topicId}`),
    due: (topicId?: string) =>
      request<Question[]>(
        `/questions/due${topicId ? `?topic_id=${topicId}` : ""}`
      ),
    create: (payload: {
      topic_id: string;
      question: string;
      answer: string;
      type?: "recall" | "cloze" | "application";
    }) =>
      request<Question>("/questions", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  reviews: {
    submit: (payload: {
      question_id: string;
      rating: ReviewRating;
      given_answer?: string;
    }) =>
      request<Review>("/reviews", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  feynman: {
    listByTopic: (topicId: string) =>
      request<FeynmanExplanation[]>(`/feynman/${topicId}`),
    submit: (payload: {
      topic_id: string;
      explanation: string;
      checklist: string[];
    }) =>
      request<FeynmanExplanation>("/feynman", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  sessions: {
    start: (planned_activities: string[] = []) =>
      request<StudySession>("/sessions", {
        method: "POST",
        body: JSON.stringify({ planned_activities }),
      }),
    finish: (
      sessionId: string,
      payload: {
        questions_attempted: number;
        questions_correct: number;
        topics_reviewed: string[];
      }
    ) =>
      request<StudySession>(`/sessions/${sessionId}/finish`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
  },
};

export { ApiError };
