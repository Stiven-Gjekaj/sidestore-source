import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/** One version of an app, as scripts/build.py writes it. */
export interface Version {
  version: string;
  date: string;
  localizedDescription: string;
  downloadURL: string;
  size: number;
  minOSVersion: string;
}

export interface App {
  name: string;
  bundleIdentifier: string;
  developerName: string;
  subtitle: string;
  localizedDescription: string;
  iconURL: string;
  tintColor?: string;
  category?: string;
  versions: Version[];
}

export interface Source {
  name: string;
  subtitle: string;
  description: string;
  website: string;
  iconURL: string;
  apps: App[];
}

/** The address that SideStore and AltStore read. */
export const sourceUrl = "https://stiven-gjekaj.github.io/sidestore-source/apps.json";

/**
 * Reads apps.json from the root of the repository. scripts/build.py writes it before the
 * build. The build runs in web/, so the file is one folder up.
 */
export function loadSource(): Source {
  const file = resolve(process.cwd(), "..", "apps.json");
  return JSON.parse(readFileSync(file, "utf8"));
}

/** The part of the address of an app page, such as "zettastream". */
export function slug(app: App): string {
  return app.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

/** A size such as "29.2 MB". */
export function formatSize(bytes: number): string {
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}

/** A date such as "21 October 2026". */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
}

/** The lines of a changelog entry, with the "- " of each item removed. */
export function changes(text: string): string[] {
  return text.split("\n").map((line) => line.replace(/^-\s+/, "").trim()).filter(Boolean);
}

/** The link that opens the source in an app, such as sidestore://source?url=... */
export function addLink(scheme: "sidestore" | "altstore"): string {
  return `${scheme}://source?url=${encodeURIComponent(sourceUrl)}`;
}
