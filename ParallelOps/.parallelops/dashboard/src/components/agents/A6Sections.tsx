import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { A6Data, BenchmarkPoint, ProfileHotspot } from "@/types/agents";
import { CheckCircle2, Cpu, Gauge, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

export function SpeedupHeroCard({ data }: { data: A6Data }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Baseline Latency</p>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600 dark:text-red-400">
            {data.baseline.wall_time_ms}
            <span className="ml-1 text-base font-normal text-muted-foreground">ms</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">cProfile · {data.baseline.hotspot}</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">After Fix Latency</p>
            <TrendingUp className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-400">
            {data.after.wall_time_ms}
            <span className="ml-1 text-base font-normal text-muted-foreground">ms</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">set-based dedup</p>
        </CardContent>
      </Card>

      <Card className="border-emerald-500/30 bg-emerald-500/5">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Speedup</p>
            <Zap className="h-4 w-4 text-amber-500" />
          </div>
          <p className="mt-2 text-3xl font-bold text-amber-600 dark:text-amber-400">
            {data.after.speedup}×
          </p>
          <p className="mt-1 text-xs text-muted-foreground">wall-time improvement</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Tests After Fix</p>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-3xl font-bold">
            {data.test_results.after_fix.passed}
            <span className="ml-1 text-base font-normal text-muted-foreground">passed</span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{data.test_results.command}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export function TargetFunctionCard({ data }: { data: A6Data }) {
  return (
    <SectionCard
      title="Profiled Bottleneck"
      description="Root cause identified by cProfile"
    >
      <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">
        <div className="flex items-start gap-3">
          <Cpu className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="destructive" className="font-mono">
                {data.target.function}
              </Badge>
              <span className="font-mono text-xs text-muted-foreground">
                {data.target.file}:{data.target.line}
              </span>
            </div>
            <p className="mt-2 text-sm">{data.target.description}</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-3 text-xs">
              <div>
                <span className="text-muted-foreground">Tool: </span>
                <span className="font-mono font-medium">{data.baseline.tool}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Total calls: </span>
                <span className="font-mono font-medium">{data.baseline.total_calls.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Entries: </span>
                <span className="font-mono font-medium">{data.baseline.entries_processed}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export function FixCard({ data }: { data: A6Data }) {
  return (
    <SectionCard
      title="Applied Fix"
      description="Minimal targeted change — no broad rewrite"
    >
      <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
        <div className="flex items-start gap-3">
          <Zap className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
          <div>
            <p className="font-medium">{data.fix.description}</p>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="font-mono">branch: {data.fix.branch}</span>
              <span>{data.fix.diff_lines_changed} lines changed</span>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export function HotspotTable({ hotspots }: { hotspots: ProfileHotspot[] }) {
  const maxMs = Math.max(...hotspots.map((h) => h.total_ms));

  return (
    <SectionCard
      title="Profile Hotspots"
      description="cProfile output — ranked by total time"
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">#</TableHead>
            <TableHead>Function</TableHead>
            <TableHead>File</TableHead>
            <TableHead className="text-right">Calls</TableHead>
            <TableHead className="text-right">Total (ms)</TableHead>
            <TableHead className="w-40">% Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {hotspots.map((h) => (
            <TableRow key={h.rank}>
              <TableCell className="font-mono text-xs text-muted-foreground">{h.rank}</TableCell>
              <TableCell className="font-mono text-xs font-medium">{h.function}</TableCell>
              <TableCell className="font-mono text-xs text-muted-foreground">{h.file}</TableCell>
              <TableCell className="text-right text-sm">{h.calls.toLocaleString()}</TableCell>
              <TableCell className="text-right text-sm font-medium">{h.total_ms}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress
                    value={(h.total_ms / maxMs) * 100}
                    className="h-1.5 flex-1"
                  />
                  <span className="w-10 text-right text-xs text-muted-foreground">
                    {h.pct_time}%
                  </span>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

export function BenchmarkComparisonChart({ data }: { data: BenchmarkPoint[] }) {
  const maxRps = Math.max(...data.map((d) => d.throughput_rps));
  const maxMs = Math.max(...data.map((d) => d.wall_time_ms));

  return (
    <SectionCard
      title="Benchmark Comparison"
      description="Before vs after — wall time and throughput"
    >
      <div className="space-y-6">
        <div>
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Wall Time (ms) — lower is better
          </p>
          <div className="space-y-3">
            {data.map((d) => (
              <div key={d.label} className="flex items-center gap-3">
                <span className="w-20 shrink-0 text-sm">{d.label}</span>
                <div className="flex flex-1 items-center gap-2">
                  <div
                    className="h-8 rounded-md transition-all"
                    style={{
                      width: `${(d.wall_time_ms / maxMs) * 100}%`,
                      background:
                        d.label === "Baseline"
                          ? "rgb(239 68 68 / 0.7)"
                          : "rgb(34 197 94 / 0.7)",
                    }}
                  />
                  <span className="shrink-0 font-mono text-sm font-medium">{d.wall_time_ms}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Throughput (req/s) — higher is better
          </p>
          <div className="space-y-3">
            {data.map((d) => (
              <div key={d.label} className="flex items-center gap-3">
                <span className="w-20 shrink-0 text-sm">{d.label}</span>
                <div className="flex flex-1 items-center gap-2">
                  <div
                    className="h-8 rounded-md transition-all"
                    style={{
                      width: `${(d.throughput_rps / maxRps) * 100}%`,
                      background:
                        d.label === "After Fix"
                          ? "rgb(34 197 94 / 0.7)"
                          : "rgb(239 68 68 / 0.7)",
                    }}
                  />
                  <span className="shrink-0 font-mono text-sm font-medium">{d.throughput_rps} rps</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-2">
        <Gauge className="h-4 w-4 text-emerald-500" />
        <p className="text-sm">
          <span className="font-semibold text-emerald-600 dark:text-emerald-400">7.3× speedup</span>
          <span className="ml-2 text-muted-foreground">· throughput up from 54 → 398 req/s</span>
        </p>
      </div>
    </SectionCard>
  );
}
