"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { api, ApiError } from "@/lib/api";
import type { Question, Topic } from "@/lib/types";

function NewQuestionForm({
  topicId,
  onCreated,
}: {
  topicId: string;
  onCreated: (question: Question) => void;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    setIsSubmitting(true);
    try {
      const created = await api.questions.create({
        topic_id: topicId,
        question: question.trim(),
        answer: answer.trim(),
      });
      onCreated(created);
      setQuestion("");
      setAnswer("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">
          Question
        </label>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What problem does virtual memory solve?"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">
          Answer
        </label>
        <input
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="It lets a process use more address space than physical RAM."
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Adding..." : "Add question"}
      </Button>
    </form>
  );
}

function NewTopicForm({
  subjectId,
  onCreated,
}: {
  subjectId: string;
  onCreated: (topic: Topic) => void;
}) {
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      const created = await api.subjects.createTopic(subjectId, name.trim());
      onCreated(created);
      setName("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="New topic name (e.g. Virtual Memory)"
        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      <Button type="submit" variant="secondary" disabled={isSubmitting}>
        {isSubmitting ? "Adding..." : "Add topic"}
      </Button>
    </form>
  );
}

function PracticeContent() {
  const searchParams = useSearchParams();
  const subjectId = searchParams.get("subject");

  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subjectId) return;
    api.subjects
      .topics(subjectId)
      .then((data) => {
        setTopics(data);
        if (data.length > 0) setSelectedTopicId(data[0]._id);
      })
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Could not load topics.")
      );
  }, [subjectId]);

  useEffect(() => {
    if (!selectedTopicId) return;
    api.questions
      .listByTopic(selectedTopicId)
      .then(setQuestions)
      .catch(() => setQuestions([]));
  }, [selectedTopicId]);

  if (!subjectId) {
    return (
      <p className="text-sm text-slate-500">
        Pick a subject from the{" "}
        <a href="/subjects" className="text-brand-600 hover:underline">
          Subjects
        </a>{" "}
        page to practice its questions.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Practice
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Build up a question bank for this subject&apos;s topics.
        </p>
      </div>

      {error && (
        <div className="card border-amber-200 bg-amber-50 text-sm text-amber-800">
          {error}
        </div>
      )}

      <Card>
        <CardHeader title="Topics" />
        <div className="mb-3 flex flex-wrap gap-2">
          {topics.map((topic) => (
            <button
              key={topic._id}
              onClick={() => setSelectedTopicId(topic._id)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                selectedTopicId === topic._id
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-600 border border-slate-300 hover:bg-slate-50"
              }`}
            >
              {topic.name}
            </button>
          ))}
          {topics.length === 0 && (
            <p className="text-sm text-slate-500">
              No topics yet for this subject &mdash; add one below.
            </p>
          )}
        </div>
        <NewTopicForm
          subjectId={subjectId}
          onCreated={(t) => {
            setTopics((prev) => [...prev, t]);
            setSelectedTopicId(t._id);
          }}
        />
      </Card>

      {selectedTopicId && (
        <Card>
          <CardHeader title="Add a question" />
          <NewQuestionForm
            topicId={selectedTopicId}
            onCreated={(q) => setQuestions((prev) => [...prev, q])}
          />
        </Card>
      )}

      <Card>
        <CardHeader title={`Question bank (${questions.length})`} />
        {questions.length === 0 ? (
          <p className="text-sm text-slate-500">
            No questions yet for this topic — add one above.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {questions.map((q) => (
              <li key={q._id} className="py-3">
                <p className="text-sm font-medium text-slate-800">
                  {q.question}
                </p>
                <p className="mt-1 text-sm text-slate-500">{q.answer}</p>
                <p className="mt-1 text-xs text-slate-400">
                  Reviewed {q.review_count}× · ease {q.difficulty}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export default function PracticePage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading...</p>}>
      <PracticeContent />
    </Suspense>
  );
}
