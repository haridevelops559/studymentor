import Link from "next/link";
import { Card, CardHeader } from "@/components/ui/Card";
import { NewSubjectForm } from "@/components/notes/NewSubjectForm";
import { api, ApiError } from "@/lib/api";
import type { Subject } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function SubjectsPage() {
  let subjects: Subject[];
  let loadError: string | null = null;

  try {
    subjects = await api.subjects.list();
  } catch (error) {
    subjects = [];
    loadError =
      error instanceof ApiError ? error.message : "Could not load subjects.";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Subjects
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Organize your notes by subject, then break each one into topics and
          questions.
        </p>
      </div>

      <Card>
        <CardHeader title="Add a subject" />
        <NewSubjectForm />
      </Card>

      {loadError && (
        <div className="card border-amber-200 bg-amber-50 text-sm text-amber-800">
          {loadError}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {subjects.map((subject) => (
          <Card key={subject._id}>
            <h3 className="text-base font-semibold text-slate-900">
              {subject.name}
            </h3>
            {subject.description && (
              <p className="mt-1 text-sm text-slate-500">
                {subject.description}
              </p>
            )}
            <div className="mt-4 flex gap-4 text-sm">
              <Link
                href={`/practice?subject=${subject._id}`}
                className="font-medium text-brand-600 hover:text-brand-700"
              >
                Practice
              </Link>
              <Link
                href={`/review?subject=${subject._id}`}
                className="font-medium text-brand-600 hover:text-brand-700"
              >
                Review
              </Link>
            </div>
          </Card>
        ))}

        {subjects.length === 0 && !loadError && (
          <p className="text-sm text-slate-500">
            No subjects yet — add your first one above.
          </p>
        )}
      </div>
    </div>
  );
}
