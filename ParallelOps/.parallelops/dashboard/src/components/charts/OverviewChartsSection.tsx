import { ChartEngine } from "@/components/charts/ChartEngine";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useArtifactsIndex } from "@/hooks/useArtifactJson";
import { artifactsIndexPath } from "@/services/artifactClient";
import { AlertCircle, RefreshCw } from "lucide-react";

export function OverviewChartsSection() {
  const { data, loading, error, lastUpdated, reload } = useArtifactsIndex();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-base">Live Charts</CardTitle>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {artifactsIndexPath()} · auto-refresh
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={reload} disabled={loading && !data}>
          <RefreshCw className={loading ? "animate-spin" : ""} />
          Reload
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm">
            <AlertCircle className="h-4 w-4 text-destructive" />
            <span>{error}</span>
          </div>
        )}
        {data ? (
          <ChartEngine report={data} lastUpdated={lastUpdated} />
        ) : loading ? (
          <div className="grid gap-6 md:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-[320px] animate-pulse rounded-xl bg-muted" />
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
