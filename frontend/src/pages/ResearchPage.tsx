import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { Loader2, Play } from "lucide-react";
import { api } from "@/lib/api";
import { Panel } from "@/components/Panel";
import { StatChip } from "@/components/StatChip";
import { formatNumber, methodDisplayName } from "@/lib/utils";
import type { BacktestSummaryRow, CalibrationRow, PredictionRow } from "@/types";

const NUMERIC_METRICS = [
  "accuracy",
  "precision",
  "recall",
  "f1",
  "log_loss",
  "brier_score",
  "mae_prob",
  "avg_confidence",
  "avg_gap",
  "ece",
] as const;

type Metric = (typeof NUMERIC_METRICS)[number];

const COLORS: Record<string, string> = {
  multi_agent_debate: "#ff8c61",
  single_agent: "#60a5fa",
  chain_of_thought: "#00d4a4",
};

export default function ResearchPage() {
  const qc = useQueryClient();

  const summary = useQuery({ queryKey: ["bt-summary"], queryFn: api.backtestSummary });
  const predictions = useQuery({ queryKey: ["bt-preds"], queryFn: api.backtestPredictions });
  const calibration = useQuery({ queryKey: ["bt-cal"], queryFn: api.backtestCalibration });
  const ablations = useQuery({ queryKey: ["bt-ablations"], queryFn: api.backtestAblations });

  const summaryRows = (summary.data?.summary ?? []) as BacktestSummaryRow[];
  const meta = summary.data?.metadata ?? {};
  const predRows = predictions.data ?? [];
  const calRows = calibration.data ?? [];

  const [nGames, setNGames] = useState(25);
  const [season, setSeason] = useState("2025-26");
  const [minHist, setMinHist] = useState(10);

  const runMut = useMutation({
    mutationFn: () =>
      api.backtestRun({ n_games: nGames, season, min_history: minHist }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bt-summary"] });
      qc.invalidateQueries({ queryKey: ["bt-preds"] });
      qc.invalidateQueries({ queryKey: ["bt-cal"] });
      qc.invalidateQueries({ queryKey: ["bt-ablations"] });
    },
  });

  const availableMetrics = useMemo(
    () => NUMERIC_METRICS.filter((m) => summaryRows.some((r) => typeof (r as any)[m] === "number")),
    [summaryRows],
  );

  const [primaryMetric, setPrimaryMetric] = useState<Metric>("brier_score");
  const [chartMetric, setChartMetric] = useState<Metric>("accuracy");

  const empty = summaryRows.length === 0;

  return (
    <div className="space-y-6">
      <Hero />

      <Panel title="Backtest Controls" subtitle="Run a fresh sweep against historical data.">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Field label="Number of Games">
            <input
              className="input"
              type="number"
              min={5}
              max={150}
              value={nGames}
              onChange={(e) => setNGames(parseInt(e.target.value || "0", 10))}
            />
          </Field>
          <Field label="Season">
            <select
              className="input"
              value={season}
              onChange={(e) => setSeason(e.target.value)}
            >
              {["2025-26", "2024-25", "2023-24", "2022-23", "All"].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Min Prior Games">
            <input
              className="input"
              type="number"
              min={5}
              max={20}
              value={minHist}
              onChange={(e) => setMinHist(parseInt(e.target.value || "0", 10))}
            />
          </Field>
          <div className="flex items-end">
            <button
              type="button"
              className="btn-primary w-full"
              onClick={() => runMut.mutate()}
              disabled={runMut.isPending}
            >
              {runMut.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              Run / Refresh Backtest
            </button>
          </div>
        </div>

        {runMut.isError && (
          <p className="mt-3 text-xs text-loss">
            Backtest failed: {(runMut.error as Error).message}
          </p>
        )}
        {runMut.data && (
          <details className="mt-3 rounded-lg border border-white/[0.06] bg-bg-panel2/60 p-3 text-xs text-slate-400">
            <summary className="cursor-pointer text-slate-300">View backtest output</summary>
            <pre className="mt-2 max-h-64 overflow-y-auto whitespace-pre-wrap font-mono text-[11px] text-slate-400">
              {runMut.data.output.slice(-4000)}
            </pre>
          </details>
        )}
      </Panel>

      {meta && Object.keys(meta).length > 0 && <RunHealth meta={meta} />}

      {empty ? (
        <Panel>
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center text-sm text-slate-400">
            <span className="font-display text-base font-semibold text-slate-100">
              No backtest results yet
            </span>
            Run a backtest from the controls above to populate this page.
          </div>
        </Panel>
      ) : (
        <>
          <Panel
            title="Headline Metrics"
            subtitle="Higher is better for accuracy, precision, recall, F1. Lower is better for log loss, Brier, MAE, ECE."
          >
            <div className="mb-4 flex items-center gap-2">
              <span className="label">Primary metric</span>
              <select
                className="input max-w-xs"
                value={primaryMetric}
                onChange={(e) => setPrimaryMetric(e.target.value as Metric)}
              >
                {availableMetrics.map((m) => (
                  <option key={m} value={m}>
                    {prettyMetric(m)}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <BestMetric rows={summaryRows} metric={primaryMetric} />
              <BestMetric rows={summaryRows} metric="accuracy" />
              <BestMetric rows={summaryRows} metric="log_loss" />
              <BestMetric rows={summaryRows} metric="ece" />
            </div>

            <div className="mt-6 overflow-x-auto rounded-xl border border-white/[0.06]">
              <table className="w-full text-left text-sm">
                <thead className="bg-white/[0.02] text-[11px] uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Method</th>
                    {availableMetrics.map((m) => (
                      <th key={m} className="px-3 py-2 text-right">
                        {prettyMetric(m)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {summaryRows.map((r) => (
                    <tr key={r.method} className="hover:bg-white/[0.02]">
                      <td className="px-3 py-2 font-medium text-slate-100">
                        {methodDisplayName(r.method)}
                      </td>
                      {availableMetrics.map((m) => (
                        <td key={m} className="px-3 py-2 text-right font-mono text-slate-300">
                          {fmt(r[m as keyof BacktestSummaryRow] as number, m)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel
            title="Metric Comparison"
            subtitle="Visual head-to-head between methods on a single metric."
            action={
              <select
                className="input max-w-xs"
                value={chartMetric}
                onChange={(e) => setChartMetric(e.target.value as Metric)}
              >
                {availableMetrics.map((m) => (
                  <option key={m} value={m}>
                    {prettyMetric(m)}
                  </option>
                ))}
              </select>
            }
          >
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={summaryRows.map((r) => ({
                  method: methodDisplayName(r.method),
                  raw: r.method,
                  value: r[chartMetric as keyof BacktestSummaryRow] as number,
                }))}
              >
                <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="method" stroke="rgba(255,255,255,0.5)" />
                <YAxis stroke="rgba(255,255,255,0.5)" />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(v: number) => fmt(v, chartMetric)}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {summaryRows.map((r, i) => (
                    <Cell key={i} fill={COLORS[r.method] ?? "#60a5fa"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Panel>

          {calRows.length > 0 && (
            <Panel
              title="Calibration"
              subtitle="Below the diagonal = overconfident. Above = underconfident."
            >
              <ResponsiveContainer width="100%" height={360}>
                <LineChart>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    domain={[0, 1]}
                    stroke="rgba(255,255,255,0.5)"
                    tickFormatter={(v) => `${Math.round(v * 100)}%`}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    domain={[0, 1]}
                    stroke="rgba(255,255,255,0.5)"
                    tickFormatter={(v) => `${Math.round(v * 100)}%`}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
                  />
                  <Legend />
                  <ReferenceLine
                    segment={[
                      { x: 0, y: 0 },
                      { x: 1, y: 1 },
                    ]}
                    stroke="rgba(255,255,255,0.2)"
                    strokeDasharray="4 4"
                    ifOverflow="extendDomain"
                  />
                  {Object.keys(COLORS).map((method) => {
                    const data = calRows
                      .filter((r) => r.method === method)
                      .map((r: CalibrationRow) => ({
                        x: r.avg_pred_home_win_prob,
                        y: r.actual_home_win_rate,
                      }))
                      .sort((a, b) => a.x - b.x);
                    if (data.length === 0) return null;
                    return (
                      <Line
                        key={method}
                        data={data}
                        type="monotone"
                        dataKey="y"
                        stroke={COLORS[method]}
                        strokeWidth={2.4}
                        dot={{ r: 4 }}
                        name={methodDisplayName(method)}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </Panel>
          )}

          {ablations.data && ablations.data.length > 0 && (
            <Panel
              title="Ablation Study (RQ3)"
              subtitle="Per-source Brier delta vs the CoT baseline. Larger positive delta means the source matters more."
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ablations.data}>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="source" stroke="rgba(255,255,255,0.5)" />
                  <YAxis stroke="rgba(255,255,255,0.5)" />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(v: number) => v.toFixed(4)}
                  />
                  <ReferenceLine y={0} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />
                  <Bar dataKey="brier_delta" radius={[6, 6, 0, 0]}>
                    {ablations.data.map((r, i) => (
                      <Cell key={i} fill={r.brier_delta > 0 ? "#ff5470" : "#00d4a4"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Panel>
          )}

          <InfoDensity rows={predRows} />

          <PredictionTable rows={predRows} />
        </>
      )}
    </div>
  );
}

function Hero() {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-white/[0.06] bg-bg-panel/60 p-7">
      <div className="pointer-events-none absolute -right-12 -top-12 h-44 w-44 rounded-full bg-court/30 blur-3xl" />
      <span className="chip">Research mode</span>
      <h1 className="mt-3 text-balance font-display text-3xl font-bold tracking-tight text-slate-50 md:text-4xl">
        Backtesting & calibration dashboard
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-slate-400">
        Compare multi-agent debate, single-agent reasoning, and chain-of-thought baselines on
        historical NBA games. Calibration, info density (RQ1), and per-source ablation (RQ3) all
        live here.
      </p>
    </div>
  );
}

function RunHealth({ meta }: { meta: Record<string, any> }) {
  const skipped = meta.games_skipped ?? 0;
  const ok = !skipped;
  return (
    <Panel title="Run Health">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatChip label="Requested" value={String(meta.n_games_requested ?? "—")} />
        <StatChip label="Selected" value={String(meta.candidate_games_selected ?? "—")} />
        <StatChip
          label="Skipped"
          value={String(skipped)}
          tone={ok ? "win" : "loss"}
          hint={ok ? "All games completed" : "Insufficient history or failures"}
        />
        <StatChip label="Prediction Rows" value={String(meta.prediction_rows ?? "—")} />
      </div>
    </Panel>
  );
}

function BestMetric({
  rows,
  metric,
}: {
  rows: BacktestSummaryRow[];
  metric: Metric;
}) {
  const higherBetter = ["accuracy", "precision", "recall", "f1"].includes(metric);
  const sorted = [...rows].sort((a, b) =>
    higherBetter
      ? ((b[metric] as number) ?? -Infinity) - ((a[metric] as number) ?? -Infinity)
      : ((a[metric] as number) ?? Infinity) - ((b[metric] as number) ?? Infinity),
  );
  const best = sorted[0];
  return (
    <StatChip
      label={`Best ${prettyMetric(metric)}`}
      value={fmt(best?.[metric] as number, metric)}
      hint={best ? methodDisplayName(best.method) : ""}
      tone={higherBetter ? "win" : "court"}
    />
  );
}

function PredictionTable({ rows }: { rows: PredictionRow[] }) {
  const [methodFilter, setMethodFilter] = useState("All");
  const [correctness, setCorrectness] = useState("All");

  const methods = useMemo(
    () => Array.from(new Set(rows.map((r) => r.method))).filter(Boolean),
    [rows],
  );

  const filtered = useMemo(() => {
    let data = rows.slice();
    if (methodFilter !== "All") data = data.filter((r) => r.method === methodFilter);
    if (correctness === "Correct Only") data = data.filter((r) => r.correct === 1);
    if (correctness === "Incorrect Only") data = data.filter((r) => r.correct === 0);
    return data.slice(0, 100);
  }, [rows, methodFilter, correctness]);

  if (rows.length === 0) return null;

  return (
    <Panel
      title="Prediction Inspector"
      subtitle="Drill into individual game-level predictions."
    >
      <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
        <select
          className="input"
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
        >
          <option value="All">All Methods</option>
          {methods.map((m) => (
            <option key={m} value={m}>
              {methodDisplayName(m)}
            </option>
          ))}
        </select>
        <select
          className="input"
          value={correctness}
          onChange={(e) => setCorrectness(e.target.value)}
        >
          <option>All</option>
          <option>Correct Only</option>
          <option>Incorrect Only</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
        <table className="w-full text-left text-sm">
          <thead className="bg-white/[0.02] text-[11px] uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Matchup</th>
              <th className="px-3 py-2">Method</th>
              <th className="px-3 py-2 text-right">Home %</th>
              <th className="px-3 py-2 text-right">Away %</th>
              <th className="px-3 py-2">Result</th>
              <th className="px-3 py-2">Conf</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {filtered.map((r, i) => (
              <tr key={i} className="hover:bg-white/[0.02]">
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{r.date}</td>
                <td className="px-3 py-2 text-slate-200">
                  {r.away_team} @ {r.home_team}
                </td>
                <td className="px-3 py-2 text-slate-300">{methodDisplayName(r.method)}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {Math.round(r.home_win_prob * 100)}%
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {Math.round(r.away_win_prob * 100)}%
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                      r.correct === 1
                        ? "border-win/30 bg-win/10 text-win"
                        : "border-loss/30 bg-loss/10 text-loss"
                    }`}
                  >
                    {r.correct === 1 ? "Correct" : "Wrong"}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-300">{r.confidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function InfoDensity({ rows }: { rows: PredictionRow[] }) {
  const cols: { key: keyof PredictionRow; label: string }[] = [
    { key: "info_density_context_tokens", label: "Context Tokens" },
    { key: "info_density_vector_hits", label: "Vector Hits" },
    { key: "info_density_news_articles", label: "News Articles" },
    { key: "info_density_youtube_comments", label: "YouTube Comments" },
  ];
  const available = cols.filter((c) => rows.some((r) => typeof r[c.key] === "number"));
  if (available.length === 0 || !rows.some((r) => typeof r.brier_score === "number")) {
    return null;
  }
  const [pick, setPick] = [available[0].key as keyof PredictionRow, () => {}];
  const data = rows
    .filter(
      (r) =>
        typeof r[pick] === "number" &&
        typeof r.brier_score === "number" &&
        !Number.isNaN(r.brier_score),
    )
    .map((r) => ({ x: r[pick] as number, y: r.brier_score!, method: r.method }));

  return (
    <Panel
      title="Information Density vs Prediction Quality (RQ1)"
      subtitle="Lower Brier = better. Negative correlation = more info → better predictions."
    >
      <ResponsiveContainer width="100%" height={340}>
        <ScatterChart>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="x" stroke="rgba(255,255,255,0.5)" name={available[0].label} />
          <YAxis dataKey="y" stroke="rgba(255,255,255,0.5)" name="Brier" />
          <ZAxis range={[60, 60]} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
          {Object.keys(COLORS).map((m) => (
            <Scatter
              key={m}
              name={methodDisplayName(m)}
              data={data.filter((d) => d.method === m)}
              fill={COLORS[m]}
            />
          ))}
          <Legend />
        </ScatterChart>
      </ResponsiveContainer>
    </Panel>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label mb-1 inline-block">{label}</span>
      {children}
    </label>
  );
}

function prettyMetric(m: string) {
  return m.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function fmt(v: number | undefined, m: string) {
  if (typeof v !== "number" || Number.isNaN(v)) return "—";
  if (["accuracy", "precision", "recall", "f1"].includes(m)) {
    return `${(v * 100).toFixed(1)}%`;
  }
  return formatNumber(v, 4);
}

const tooltipStyle = {
  background: "#0d1424",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "10px",
  fontSize: "12px",
  color: "#e2e8f0",
};
