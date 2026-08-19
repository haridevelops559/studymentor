export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatMinutes(totalMinutes: number): string {
  if (totalMinutes < 60) return `${totalMinutes} min`;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}

export function formatSeconds(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function relativeDueLabel(isoDate: string): string {
  const due = new Date(isoDate).getTime();
  const now = Date.now();
  const diffMs = due - now;
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `Overdue by ${Math.abs(diffDays)}d`;
  if (diffDays === 0) return "Due today";
  if (diffDays === 1) return "Due tomorrow";
  return `Due in ${diffDays}d`;
}

export function score_session_label(attempted: number, correct: number): string {
  if (attempted === 0) return "no questions attempted";
  const pct = Math.round((100 * correct) / attempted);
  return `${pct}% recalled correctly`;
}

export function retentionColor(percent: number): string {
  if (percent >= 80) return "bg-emerald-500";
  if (percent >= 60) return "bg-amber-500";
  return "bg-red-500";
}
