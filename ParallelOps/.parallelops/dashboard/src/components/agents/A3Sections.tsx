import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { statusLabel, statusVariant } from "@/lib/status";
import { cn } from "@/lib/utils";
import type { A3Data, DataContract, StackComponent } from "@/types/agents";
import { ArrowRight, Box, Cpu, Server, TestTube2 } from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

const langColors: Record<string, string> = {
  Python: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
  "Node.js": "bg-green-500/15 text-green-700 dark:text-green-400",
  Rust: "bg-orange-500/15 text-orange-700 dark:text-orange-400",
};

const componentIcons: Record<string, typeof Server> = {
  fastapi: Server,
  node_worker: Box,
  rust_engine: Cpu,
};

export function ArchitectureGraph({
  flow,
  components,
}: {
  flow: string[];
  components: StackComponent[];
}) {
  return (
    <SectionCard
      title="Architecture Graph"
      description="Polyglot pipeline data flow"
    >
      <div className="overflow-x-auto rounded-xl border bg-muted/20 p-6">
        <div className="flex min-w-max items-center justify-center gap-2">
          {flow.map((node, i) => (
            <div key={`${node}-${i}`} className="flex items-center gap-2">
              <div
                className={cn(
                  "rounded-lg border px-4 py-2 text-center text-sm font-medium",
                  node === "File Queue"
                    ? "border-dashed bg-background"
                    : "bg-card shadow-sm",
                )}
              >
                {node}
              </div>
              {i < flow.length - 1 && (
                <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {components.map((c) => (
          <StackComponentCard key={c.id} component={c} />
        ))}
      </div>
    </SectionCard>
  );
}

function StackComponentCard({ component }: { component: StackComponent }) {
  const Icon = componentIcons[component.id] ?? Server;
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <p className="font-medium">{component.name}</p>
              <Badge
                className={cn("mt-1 text-[10px]", langColors[component.lang] ?? "")}
                variant="outline"
              >
                {component.lang}
              </Badge>
            </div>
          </div>
          <Badge variant={statusVariant(component.status)}>
            {statusLabel(component.status)}
          </Badge>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{component.role}</p>
        <p className="mt-1 font-mono text-xs text-muted-foreground">{component.path}</p>
        {component.port && (
          <p className="mt-1 text-xs">Port {component.port}</p>
        )}
        <div className="mt-3 flex gap-3 text-xs">
          <span className="text-emerald-600">{component.tests_passed} passed</span>
          {component.tests_failed > 0 && (
            <span className="text-red-600">{component.tests_failed} failed</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function DataContractsList({ contracts }: { contracts: DataContract[] }) {
  return (
    <SectionCard title="Data Contracts" description="Inter-component message formats">
      <div className="space-y-3">
        {contracts.map((dc) => (
          <div
            key={dc.id}
            className="rounded-lg border px-4 py-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px]">
                {dc.id}
              </Badge>
              <span className="text-sm font-medium">{dc.from}</span>
              <ArrowRight className="h-3 w-3 text-muted-foreground" />
              <span className="text-sm font-medium">{dc.to}</span>
            </div>
            <p className="mt-2 font-mono text-xs text-primary">{dc.format}</p>
            <p className="mt-1 text-sm text-muted-foreground">{dc.description}</p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function IntegrationTestsTable({
  tests,
}: {
  tests: A3Data["integration_tests"];
}) {
  return (
    <SectionCard title="Integration Tests" description="Cross-stack verification">
      <div className="space-y-2">
        {tests.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between rounded-lg border px-4 py-3"
          >
            <div className="flex items-start gap-3">
              <TestTube2 className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{t.name}</p>
                <p className="font-mono text-xs text-muted-foreground">{t.command}</p>
                <p className="mt-1 text-xs text-muted-foreground">suite: {t.suite}</p>
              </div>
            </div>
            <div className="text-right">
              <Badge variant={statusVariant(t.status)}>{statusLabel(t.status)}</Badge>
              <p className="mt-1 text-xs text-muted-foreground">
                {t.passed}/{t.passed + t.failed} tests
              </p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function StackComponentsRow({ components }: { components: StackComponent[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {components.map((c) => (
        <StackComponentCard key={c.id} component={c} />
      ))}
    </div>
  );
}
