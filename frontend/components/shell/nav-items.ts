import { Columns3, Compass, LayoutDashboard, type LucideIcon, Send, Users } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  // Second key of the "g then <key>" shortcut.
  key: string;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, key: "d" },
  { href: "/prospects", label: "Leads", icon: Users, key: "l" },
  { href: "/pipeline", label: "Pipeline", icon: Columns3, key: "p" },
  { href: "/discover", label: "Discover", icon: Compass, key: "x" },
  { href: "/outreach", label: "Outreach", icon: Send, key: "o" },
];

export function isActive(href: string, pathname: string | null): boolean {
  if (!pathname) return false;
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
