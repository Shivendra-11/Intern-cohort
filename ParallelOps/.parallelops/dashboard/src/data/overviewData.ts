import overviewMock from "@/data/mock/overview.json";
import type { OverviewData } from "@/types/overview";

export function getOverviewData(): OverviewData {
  return overviewMock as OverviewData;
}
