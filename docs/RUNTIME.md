# Runtime

The website uses Vinext on Cloudflare Workers, with D1 storage through the `DB` binding. Runtime adapters and authentication helpers are retained from the working application.

## Local development

Run `npm ci` and `npm run dev`. Vite supplies a local D1 binding. Tables are defined in `db/schema.ts` and ordered SQL migrations under `drizzle/`; apply those migrations to your own database before exercising persistent writes. No production database or visitor records are distributed.

The landing page, archive, and inference engine use bundled data. Saved records require the API and database. Anonymous requests cannot save records.

## Authentication

The original hosting gateway supplies `oai-authenticated-user-id`. This is a trusted deployment contract, not client authentication. On another host, replace it with verified server-side sessions and preserve ownership checks. Never accept identity headers directly from untrusted clients.

`.openai/hosting.json` declares runtime bindings. The original project identifier is omitted to prevent accidental deployment to the existing site. This source release does not change that site's audience or deployment.

## Optional browser checks

`tests/browser-v5.mjs` and `tests/paper-ui.mjs` use Playwright. Install Playwright and its Chromium browser separately before running them against a local server. Set `TEST_BASE_URL` to override `http://localhost:3000`. Screenshots are written to ignored `test-artifacts/`.

`tests/api-v5.mjs` uses synthetic identities and must run only against an isolated local test database and test gateway, never production.
