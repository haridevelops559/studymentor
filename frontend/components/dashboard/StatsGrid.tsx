import { formatMinutes } from "@/lib/utils";
import type { DashboardResponse } from "@/lib/types";

export function StatsGrid({ data }: { data: DashboardResponse }) {
  const stats = [
    { label: "Studied today", value: formatMinutes(data.minutes_studied_today) },
    { label: "Reviews done", value: data.reviews_completed_today.toString() },
    { label: "Recall today", value: `${data.recall_percent_today}%` },
    { label: "Topics touched", value: data.topics_touched_today.toString() },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.label} className="stat-tile">
          <span className="text-2xl font-semibold text-slate-900">
            {stat.value}
          </span>
          <span className="text-xs text-slate-500">{stat.label}</span>
        </div>
      ))}
    </div>
  );
}
