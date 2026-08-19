import { Card, CardHeader } from "@/components/ui/Card";
import type { DashboardResponse } from "@/lib/types";

export function WeakestTopics({
  topics,
}: {
  topics: DashboardResponse["weakest_topics"];
}) {
  return (
    <Card>
      <CardHeader title="Needs attention" />
      {topics.length === 0 ? (
        <p className="text-sm text-slate-500">
          Nothing flagged yet. Keep reviewing to surface weak spots here.
        </p>
      ) : (
        <ul className="space-y-3">
          {topics.map((topic) => (
            <li
              key={topic.topic_id}
              className="flex items-center justify-between rounded-lg bg-red-50 px-3 py-2"
            >
              <span className="text-sm font-medium text-red-800">
                {topic.topic_id}
              </span>
              <span className="text-sm font-semibold text-red-700">
                {topic.retention}% recall
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
