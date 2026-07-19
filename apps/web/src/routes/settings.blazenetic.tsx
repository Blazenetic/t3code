import { createFileRoute } from "@tanstack/react-router";

import { BlazeneticSettingsPanel } from "../components/blazenetic/BlazeneticSettings";

export const Route = createFileRoute("/settings/blazenetic")({
  component: BlazeneticSettingsPanel,
});
