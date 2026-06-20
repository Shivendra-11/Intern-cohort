import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ChartCardProps {
  title: string;
  description?: string;
  lastUpdated?: string | null;
  className?: string;
  children: ReactNode;
}

export function ChartCard({
  title,
  description,
  lastUpdated,
  className,
  children,
}: ChartCardProps) {
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {description && (
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {lastUpdated && (
            <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
              live
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="h-[280px] pb-4">{children}</CardContent>
    </Card>
  );
}

export const CHART_COLORS = [
  "hsl(var(--chart-1, 262 83% 58%))",
  "hsl(221 83% 53%)",
  "hsl(142 71% 45%)",
  "hsl(38 92% 50%)",
  "hsl(0 72% 51%)",
  "hsl(199 89% 48%)",
];
