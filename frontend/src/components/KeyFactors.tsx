import { KeyFactor } from "@/types";
import { Panel } from "./Panel";
import { cn, impactLabel, importanceWeight } from "@/lib/utils";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export function KeyFactors({ factors }: { factors: KeyFactor[] }) {
  if (!factors || factors.length === 0) return null;
  return (
    <Panel
      title="Key Factors"
      subtitle="Drivers behind the prediction · with directional impact and importance"
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {factors.map((f, i) => (
          <FactorCard key={i} factor={f} index={i} />
        ))}
      </div>
    </Panel>
  );
}

function FactorCard({ factor, index }: { factor: KeyFactor; index: number }) {
  const impactKey = (factor.impact || "neutral").toString().toLowerCase();
  const importance = (factor.importance || "medium").toString().toLowerCase();

  const tone = impactKey.includes("home")
    ? "win"
    : impactKey.includes("away")
    ? "loss"
    : "court";

  const Icon = tone === "win" ? TrendingUp : tone === "loss" ? TrendingDown : Minus;
  const colorMap = {
    win: { border: "border-win/25", bg: "bg-win/5", text: "text-win", chip: "bg-win/15 text-win border-win/30" },
    loss: { border: "border-loss/25", bg: "bg-loss/5", text: "text-loss", chip: "bg-loss/15 text-loss border-loss/30" },
    court: { border: "border-court/25", bg: "bg-court/5", text: "text-court-glow", chip: "bg-court/15 text-court-glow border-court/30" },
  }[tone];

  const importanceText =
    importance === "high"
      ? "High Importance"
      : importance === "low"
      ? "Low Importance"
      : "Medium Importance";

  return (
    <div
      style={{ animationDelay: `${index * 60}ms` }}
      className={cn(
        "relative animate-fade-in-up rounded-xl border p-4",
        colorMap.border,
        colorMap.bg,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
            colorMap.chip,
          )}
        >
          <Icon className="h-3 w-3" />
          {impactLabel(impactKey)}
        </span>
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          {importanceText}
        </span>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-slate-200">{factor.factor}</p>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className={cn("h-full rounded-full", colorMap.text.replace("text-", "bg-"))}
          style={{ width: `${importanceWeight(importance)}%`, opacity: 0.6 }}
        />
      </div>
    </div>
  );
}
