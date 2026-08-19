import { Card, CardHeader } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { retentionColor } from "@/lib/utils";
import type { DashboardResponse } from "@/lib/types";

export function RetentionSnapshot({
  retentionByTopic,
}: {
  retentionByTopic: DashboardResponse["retention_by_topic"];
}) {
  const entries = Object.entries(retentionByTopic);

  return (
    <Card>
      <CardHeader title="Retention snapshot" />
      {entries.length === 0 ? (
        <p className="text-sm text-slate-500">
          No reviews yet — complete a retrieval-practice session and topic
          retention will show up here.
        </p>
      ) : (
        <div className="space-y-4">
          {entries.map(([topicId, percent]) => (
            <ProgressBar
              key={topicId}
              label={topicId}
              percent={percent}
              colorClassName={retentionColor(percent)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}
