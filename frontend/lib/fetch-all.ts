import { api, type ListBusinessesParams } from "@/lib/api";
import type { BusinessListItem } from "@/lib/types";

// The list endpoint caps `limit` at 200, so counts built from one page silently
// stop at 200 leads. This walks every page with the existing call instead.
const PAGE_SIZE = 200;

export async function fetchAllBusinesses(
  params: Omit<ListBusinessesParams, "limit" | "offset"> = {}
): Promise<BusinessListItem[]> {
  const items: BusinessListItem[] = [];
  let offset = 0;
  for (;;) {
    const page = await api.listBusinesses({ ...params, limit: PAGE_SIZE, offset });
    items.push(...page.items);
    offset += PAGE_SIZE;
    // Stop on the reported total, and on an empty page in case the total
    // shifts while paging (a lead deleted mid-walk).
    if (offset >= page.total || page.items.length === 0) return items;
  }
}
