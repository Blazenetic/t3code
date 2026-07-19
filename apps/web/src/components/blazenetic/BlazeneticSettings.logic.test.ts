import type { ServerConfig, ServerLifecycleWelcomePayload } from "@t3tools/contracts";
import { describe, expect, it } from "vite-plus/test";

import { deriveObservabilitySummary, deriveRuntimeSummary } from "./BlazeneticSettings.logic";

const environment = {
  environmentId: "local-test",
  label: "Local development",
  platform: { os: "linux", arch: "x64" },
  serverVersion: "0.0.28",
  capabilities: { repositoryIdentity: true },
} as const;

describe("BlazeneticSettings.logic", () => {
  it("returns a safe disconnected runtime state", () => {
    expect(deriveRuntimeSummary(null, null)).toBeNull();
    expect(deriveObservabilitySummary(null).readiness).toBe("unavailable");
  });

  it("combines config and welcome runtime information", () => {
    const config = {
      environment,
      cwd: "/workspace/fallback",
    } as ServerConfig;
    const welcome = {
      environment,
      cwd: "/workspace/t3code",
      projectName: "t3code",
    } as ServerLifecycleWelcomePayload;
    expect(deriveRuntimeSummary(config, welcome)).toEqual({
      environmentLabel: "Local development",
      serverVersion: "0.0.28",
      os: "linux",
      architecture: "x64",
      projectName: "t3code",
      workingDirectory: "/workspace/t3code",
    });
  });

  it("classifies disabled OTLP with local recording active", () => {
    expect(
      deriveObservabilitySummary({
        logsDirectoryPath: "/logs",
        localTracingEnabled: true,
        otlpTracesEnabled: false,
        otlpMetricsEnabled: false,
      }).readiness,
    ).toBe("disabled");
  });

  it("classifies a single exporter as partial", () => {
    expect(
      deriveObservabilitySummary({
        logsDirectoryPath: "/logs",
        localTracingEnabled: true,
        otlpTracesEnabled: true,
        otlpTracesUrl: "http://127.0.0.1:4318/v1/traces",
        otlpMetricsEnabled: false,
      }).readiness,
    ).toBe("partial");
  });

  it("classifies local traces and both exporters as ready", () => {
    const summary = deriveObservabilitySummary({
      logsDirectoryPath: "/logs",
      localTracingEnabled: true,
      otlpTracesEnabled: true,
      otlpTracesUrl: "http://127.0.0.1:4318/v1/traces",
      otlpMetricsEnabled: true,
      otlpMetricsUrl: "http://127.0.0.1:4318/v1/metrics",
    });
    expect(summary.readiness).toBe("ready");
    expect(summary.otlpMetricsUrl).toContain("/v1/metrics");
  });
});
