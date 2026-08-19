import { cn } from "@/lib/utils";
import type { ReviewRating } from "@/lib/types";

const RATINGS: { value: ReviewRating; label: string; emoji: string; className: string }[] = [
  { value: "again", label: "Again", emoji: "😓", className: "bg-recall-again/10 text-recall-again hover:bg-recall-again/20" },
  { value: "hard", label: "Hard", emoji: "😐", className: "bg-recall-hard/10 text-recall-hard hover:bg-recall-hard/20" },
  { value: "good", label: "Good", emoji: "🙂", className: "bg-recall-good/10 text-recall-good hover:bg-recall-good/20" },
  { value: "easy", label: "Easy", emoji: "😎", className: "bg-recall-easy/10 text-recall-easy hover:bg-recall-easy/20" },
];

export function RatingButtons({
  onRate,
  disabled,
}: {
  onRate: (rating: ReviewRating) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {RATINGS.map((rating) => (
        <button
          key={rating.value}
          disabled={disabled}
          onClick={() => onRate(rating.value)}
          className={cn(
            "flex flex-col items-center gap-1 rounded-xl py-3 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
            rating.className
          )}
        >
          <span className="text-xl" aria-hidden>
            {rating.emoji}
          </span>
          {rating.label}
        </button>
      ))}
    </div>
  );
}
