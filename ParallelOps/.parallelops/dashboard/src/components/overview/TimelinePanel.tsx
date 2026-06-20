import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, formatDateTime } from "@/lib/utils";
import type { TimelineEvent } from "@/types/overview";
import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  Info,
  XCircle,
} from "lucide-react";

interface TimelinePanelProps {
  events: TimelineEvent[];
}

const levelConfig = {
  info: {
    icon: Info,
    dot: "bg-blue-500",
    line: "border-blue-500/30",
  },
  success: {
    icon: CheckCircle2,
    dot: "bg-emerald-500",
    line: "border-emerald-500/30",
  },
  warning: {
    icon: AlertTriangle,
    dot: "bg-amber-500",
    line: "border-amber-500/30",
  },
  error: {
    icon: XCircle,
    dot: "bg-red-500",
    line: "border-red-500/30",
  },
};

export function TimelinePanel({ events }: TimelinePanelProps) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[320px] pr-4">
          <div className="relative space-y-0 pl-2">
            {events.map((event, index) => {
              const config = levelConfig[event.level];
              const Icon = config.icon;
              const isLast = index === events.length - 1;

              return (
                <div key={event.id} className="relative flex gap-4 pb-6">
                  {!isLast && (
                    <div
                      className={cn(
                        "absolute left-[11px] top-6 h-full w-px border-l",
                        config.line,
                      )}
                    />
                  )}
                  <div
                    className={cn(
                      "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ring-4 ring-background",
                      config.dot,
                    )}
                  >
                    <Icon className="h-3 w-3 text-white" />
                  </div>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-medium text-muted-foreground">
                        {event.agent}
                      </span>
                      <span className="text-xs text-muted-foreground">·</span>
                      <span className="text-xs text-muted-foreground">
                        {event.phase}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm">{event.message}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDateTime(event.timestamp)}
                    </p>
                  </div>
                </div>
              );
            })}
            <div className="flex gap-4 pb-2">
              <Circle className="h-6 w-6 shrink-0 text-muted-foreground/40" />
              <p className="pt-0.5 text-xs text-muted-foreground">End of timeline</p>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
