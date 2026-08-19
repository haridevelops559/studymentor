import { cn } from "@/lib/utils";

export function ProgressBar({
  percent,
  colorClassName = "bg-brand-500",
  trackClassName = "bg-slate-100",
  label,
}: {
  percent: number;
  colorClassName?: string;
  trackClassName?: string;
  label?: string;
}) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div>
      {label && (
        <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
          <span>{label}</span>
          <span>{clamped}%</span>
        </div>
      )}
      <div className={cn("h-2 w-full overflow-hidden rounded-full", trackClassName)}>
        <div
          className={cn("h-full rounded-full transition-all", colorClassName)}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
