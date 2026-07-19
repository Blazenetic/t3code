import type { AnyProviderDriver } from "../provider/ProviderDriver.ts";

/** Infrastructure required by downstream drivers. Empty until one is added. */
export type BlazeneticDriversEnv = never;

/** Compile-time contribution seam for downstream provider drivers. */
export const BLAZENETIC_DRIVERS: ReadonlyArray<AnyProviderDriver<BlazeneticDriversEnv>> = [];
