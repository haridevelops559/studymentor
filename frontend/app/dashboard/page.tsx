import { RetentionSnapshot } from "@/components/dashboard/RetentionSnapshot";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { TodayPlan } from "@/components/dashboard/TodayPlan";
import { WeakestTopics } from "@/components/dashboard/WeakestTopics";
import { api, ApiError } from "@/lib/api";

// Server Component: fetches the aggregated dashboard payload directly on
// the server for a fast first paint, no client-side loading spinner needed.
export default async function DashboardPage() {
  try {
    const data = await api.dashboard.get();

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Good to see you 👋
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Here&apos;s your learning plan for today.
          </p>
        </div>

        <StatsGrid data={data} />

        <div className="grid gap-6 md:grid-cols-2">
          <TodayPlan due={data.due} />
          <WeakestTopics topics={data.weakest_topics} />
        </div>

        <RetentionSnapshot retentionByTopic={data.retention_by_topic} />
      </div>
    );
  } catch (error) {
    const message =
      error instanceof ApiError
        ? error.message
        : "Could not reach the StudyMentor API.";

    return (
      <div className="card border-amber-200 bg-amber-50">
        <h1 className="text-lg font-semibold text-amber-900">
          Backend not reachable
        </h1>
        <p className="mt-2 text-sm text-amber-800">{message}</p>
        <p className="mt-2 text-sm text-amber-800">
          Start the API with{" "}
          <code className="rounded bg-amber-100 px-1.5 py-0.5">
            uvicorn app.main:app --reload
          </code>{" "}
          from <code className="rounded bg-amber-100 px-1.5 py-0.5">backend/</code>,
          then refresh.
        </p>
      </div>
    );
  }
}
