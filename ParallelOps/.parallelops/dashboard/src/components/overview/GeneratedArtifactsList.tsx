import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatRelativeTime } from "@/lib/utils";
import type { GeneratedArtifact } from "@/types/overview";
import { FileCode2, FileJson, FileText, Paperclip } from "lucide-react";

interface GeneratedArtifactsListProps {
  artifacts: GeneratedArtifact[];
}

const kindIcon = {
  json: FileJson,
  markdown: FileText,
  log: FileCode2,
  attachment: Paperclip,
};

export function GeneratedArtifactsList({ artifacts }: GeneratedArtifactsListProps) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Generated Artifacts
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 pb-2">
        <ScrollArea className="h-[280px] px-6">
          <ul className="space-y-2">
            {artifacts.map((artifact) => {
              const Icon = kindIcon[artifact.kind] ?? FileText;
              return (
                <li
                  key={artifact.id}
                  className="flex items-start gap-3 rounded-lg border bg-muted/30 p-3 transition-colors hover:bg-muted/50"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-background">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-sm font-medium">{artifact.label}</p>
                      <Badge variant="secondary" className="shrink-0 font-mono text-[10px]">
                        {artifact.agent}
                      </Badge>
                    </div>
                    <p className="mt-0.5 truncate font-mono text-xs text-muted-foreground">
                      {artifact.path}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatRelativeTime(artifact.updated_at)}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
