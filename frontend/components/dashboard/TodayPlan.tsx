import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import type { DashboardResponse } from "@/lib/types";

export function TodayPlan({ due }: { due: DashboardResponse["due"] }) {
  const items = [
    {
      label: "Overdue reviews",
      count: due.overdue,
      tone: "red" as const,
      href: "/review",
      icon: "🔴",
    },
    {
      label: "Due today",
      count: due.due_today,
      tone: "amber" as const,
      href: "/review",
      icon: "🟡",
    },
    {
      label: "Upcoming",
      count: due.upcoming,
      tone: "slate" as const,
      href: "/review",
      icon: "🟢",
    },
  ];

  return (
    <Card>
      <CardHeader title="Today's plan" />
      <ul className="divide-y divide-slate-100">
        {items.map((item) => (
          <li key={item.label} className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg" aria-hidden>
                {item.icon}
              </span>
              <span className="text-sm font-medium text-slate-700">
                {item.label}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Badge tone={item.tone}>{item.count}</Badge>
              <Link
                href={item.href}
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Start
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
