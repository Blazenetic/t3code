import type { ComponentType } from "react";
import { GaugeIcon } from "lucide-react";

export type BlazeneticSettingsSectionPath = "/settings/blazenetic";

export const BLAZENETIC_SETTINGS_NAV_ITEMS: ReadonlyArray<{
  label: string;
  to: BlazeneticSettingsSectionPath;
  icon: ComponentType<{ className?: string }>;
}> = [{ label: "Blazenetic", to: "/settings/blazenetic", icon: GaugeIcon }];
