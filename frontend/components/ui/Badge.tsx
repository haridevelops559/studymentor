import { cn } from "@/lib/utils";

type Tone = "red" | "amber" | "emerald" | "slate" | "blue";

const TONE_CLASSES: Record<Tone, string> = {
  red: "bg-red-50 text-red-700",
  amber: "bg-amber-50 text-amber-700",
  emerald: "bg-emerald-50 text-emerald-700",
  slate: "bg-slate-100 text-slate-700",
  blue: "bg-blue-50 text-blue-700",
};

export function Badge({
  tone = "slate",
  children,
}: {
  tone?: Tone;
  children: React.ReactNode;
}) {
  return (
    <span className={cn("pill", TONE_CLASSES[tone])}>{children}</span>
  );
}
