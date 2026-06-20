import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSession } from "@/stores/sessionStore";
import { History } from "lucide-react";

export function SessionPicker() {
  const { sessionId, setSessionId, sessions, loading } = useSession();

  if (loading && !sessionId) {
    return (
      <span className="text-xs text-muted-foreground">Loading sessions…</span>
    );
  }

  return (
    <Select value={sessionId ?? undefined} onValueChange={setSessionId}>
      <SelectTrigger className="h-8 w-[220px] font-mono text-xs">
        <History className="mr-2 h-3.5 w-3.5 shrink-0" />
        <SelectValue placeholder="Select run" />
      </SelectTrigger>
      <SelectContent>
        {sessions.map((s) => (
          <SelectItem key={s.session_id} value={s.session_id} className="font-mono text-xs">
            {s.repo_name ? `${s.repo_name} · ` : ""}
            {s.session_id}
            {s.overall_status ? ` · ${s.overall_status}` : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
