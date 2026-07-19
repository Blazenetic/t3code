import { useAtomValue } from "@effect/atom-react";
import { Link } from "@tanstack/react-router";

import {
  primaryServerConfigAtom,
  primaryServerObservabilityAtom,
  primaryServerWelcomeAtom,
} from "../../state/server";
import { SettingsPageContainer, SettingsRow, SettingsSection } from "../settings/settingsLayout";
import { deriveObservabilitySummary, deriveRuntimeSummary } from "./BlazeneticSettings.logic";

const OPERATOR_COMMANDS = [
  ["Start observability", "t3b-obs up"],
  ["Inspect upstream", "t3b-upstream"],
  ["Inspect feature branch", "t3b-feature status"],
  ["Run quick checks", "t3b-check --quick"],
] as const;

function StateValue({ value }: { value: boolean | null }) {
  return (
    <span className="font-mono text-xs">
      {value === null ? "Unavailable" : value ? "Enabled" : "Disabled"}
    </span>
  );
}

function Command({ children }: { children: string }) {
  return (
    <code className="select-all rounded-md bg-muted px-2 py-1 font-mono text-xs text-foreground">
      {children}
    </code>
  );
}

export function BlazeneticSettingsPanel() {
  const config = useAtomValue(primaryServerConfigAtom);
  const welcome = useAtomValue(primaryServerWelcomeAtom);
  const observability = useAtomValue(primaryServerObservabilityAtom);
  const runtime = deriveRuntimeSummary(config, welcome);
  const telemetry = deriveObservabilitySummary(observability);

  return (
    <SettingsPageContainer>
      <SettingsSection title="Runtime">
        <SettingsRow
          title="Environment"
          description="The primary server environment currently connected to this client."
          control={
            <span className="text-xs">{runtime?.environmentLabel ?? "Waiting for server"}</span>
          }
        />
        <SettingsRow
          title="Server"
          description="Version and host platform reported by the server."
          control={
            <span className="font-mono text-xs">
              {runtime
                ? `${runtime.serverVersion} · ${runtime.os}/${runtime.architecture}`
                : "Unavailable"}
            </span>
          }
        />
        <SettingsRow
          title="Project"
          description={runtime?.workingDirectory ?? "Waiting for server welcome"}
          control={<span className="text-xs">{runtime?.projectName ?? "Unavailable"}</span>}
        />
      </SettingsSection>

      <SettingsSection title="Observability">
        <SettingsRow title={telemetry.title} description={telemetry.detail} />
        <SettingsRow
          title="Local traces"
          description="Trace recording retained by the T3 Code server."
          control={<StateValue value={telemetry.localTracingEnabled} />}
        />
        <SettingsRow
          title="OTLP traces"
          description={telemetry.otlpTracesUrl ?? "No trace export endpoint configured."}
          control={<StateValue value={telemetry.otlpTracesEnabled} />}
        />
        <SettingsRow
          title="OTLP metrics"
          description={telemetry.otlpMetricsUrl ?? "No metrics export endpoint configured."}
          control={<StateValue value={telemetry.otlpMetricsEnabled} />}
        />
        <SettingsRow
          title="Diagnostics"
          description="Inspect live traces, failures, and process diagnostics."
          control={
            <Link to="/settings/diagnostics" className="text-xs text-primary hover:underline">
              Open diagnostics
            </Link>
          }
        />
      </SettingsSection>

      <SettingsSection title="Operator toolkit">
        {OPERATOR_COMMANDS.map(([label, command]) => (
          <SettingsRow
            key={command}
            title={label}
            description="Select the command to copy it into a terminal."
            control={<Command>{command}</Command>}
          />
        ))}
        <SettingsRow
          title="Enable local OTLP export"
          description="Restart the server-bearing launcher after changing this setting."
          control={<Command>T3B_OTLP=1</Command>}
        />
      </SettingsSection>

      <SettingsSection title="Fork model">
        <SettingsRow
          title="main → blazenetic → feature/blazeprovements"
          description="Sync and publish are separate operations. Blazenetic tooling only publishes to origin and never pushes upstream."
        />
      </SettingsSection>
    </SettingsPageContainer>
  );
}
