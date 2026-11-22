// The two Node APIs the contract test uses, declared here so no @types/node dependency is needed.
declare module 'node:fs' {
  export function readFileSync(path: URL | string, encoding: 'utf8'): string;
  export function writeFileSync(path: URL | string, data: string): void;
}
declare const process: { env: Record<string, string | undefined> };
