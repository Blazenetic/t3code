import type {
  ServerConfig,
  ServerLifecycleWelcomePayload,
  ServerObservability,
} from "@t3tools/contracts";

export type ObservabilityReadiness = "ready" | "partial" | "disabled" | "unavailable";

export interface RuntimeSummary {
  readonly environmentLabel: string;
  readonly serverVersion: string;
  readonly os: string;
  readonly architecture: string;
  readonly projectName: string;
  readonly workingDirectory: string;
}

export interface ObservabilitySummary {
  readonly readiness: ObservabilityReadiness;
  readonly title: string;
  readonly detail: string;
  readonly localTracingEnabled: boolean | null;
  readonly otlpTracesEnabled: boolean | null;
  readonly otlpTracesUrl: string | null;
  readonly otlpMetricsEnabled: boolean | null;
  readonly otlpMetricsUrl: string | null;
}

export function deriveRuntimeSummary(
  config: ServerConfig | null,
  welcome: ServerLifecycleWelcomePayload | null,
): RuntimeSummary | null {
  const environment = config?.environment ?? welcome?.environment;
  if (!environment) return null;

  return {
    environmentLabel: environment.label,
    serverVersion: environment.serverVersion,
    os: environment.platform.os,
    architecture: environment.platform.arch,
    projectName: welcome?.projectName ?? "Waiting for server welcome",
    workingDirectory: welcome?.cwd ?? config?.cwd ?? "Waiting for server welcome",
  };
}

export function deriveObservabilitySummary(
  observability: ServerObservability | null,
): ObservabilitySummary {
  if (!observability) {
    return {
      readiness: "unavailable",
      title: "Waiting for server",
      detail: "Live observability configuration will appear when the primary server connects.",
      localTracingEnabled: null,
      otlpTracesEnabled: null,
      otlpTracesUrl: null,
      otlpMetricsEnabled: null,
      otlpMetricsUrl: null,
    };
  }

  const traces = observability.otlpTracesEnabled;
  const metrics = observability.otlpMetricsEnabled;
  const fullyReady = observability.localTracingEnabled && traces && metrics;
  const partiallyReady = traces || metrics || !observability.localTracingEnabled;
  const readiness: ObservabilityReadiness = fullyReady
    ? "ready"
    : partiallyReady
      ? "partial"
      : "disabled";

  const copy = {
    ready: {
      title: "Collector ready",
      detail: "Local traces, OTLP traces, and OTLP metrics are all enabled.",
    },
    partial: {
      title: "Partially configured",
      detail: "Some observability signals are enabled. Review the individual signal states below.",
    },
    disabled: {
      title: "OTLP export disabled",
      detail:
        "Local trace recording is active; start LGTM and restart the server with T3B_OTLP=1 to export.",
    },
    unavailable: { title: "Waiting for server", detail: "" },
  }[readiness];

  return {
    readiness,
    ...copy,
    localTracingEnabled: observability.localTracingEnabled,
    otlpTracesEnabled: traces,
    otlpTracesUrl: observability.otlpTracesUrl ?? null,
    otlpMetricsEnabled: metrics,
    otlpMetricsUrl: observability.otlpMetricsUrl ?? null,
  };
}
