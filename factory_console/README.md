# factory_console

## What this is

The ModelPassport web dashboard. It runs in mock, live, and snapshot modes. Mock fixtures are illustrative sample data and are not validation results.

## Folder map

| Path | Contents |
| --- | --- |
| `Dockerfile` | Builds the dashboard and serves it with nginx on port 5173 for `docker compose up` at the repository root. |
| `src/` | Frontend application source. |
| `src/api/` | Contract types, the factory_core client, and query hooks. |
| `src/api/client.ts` | Public functions for every factory_core endpoint. |
| `src/api/apiTransport.ts` | Mode configuration and HTTP response handling. |
| `src/api/mockClient.ts` | Sample data access and in-memory gate workflow. |
| `src/api/hooks.ts` | TanStack Query hooks and run polling. |
| `src/api/types.ts` | Public re-exports of the API contract types. |
| `src/api/contractEnums.ts` | Contract enumerations and pipeline status shape. |
| `src/api/modelTypes.ts` | Model inventory and evidence types. |
| `src/api/documentationTypes.ts` | Documentation and document-drift types. |
| `src/api/workflowTypes.ts` | Run, stage, and gate types. |
| `src/api/redevelopmentTypes.ts` | Redevelopment and parity types. |
| `src/api/validationTypes.ts` | Validation metrics, findings, and report types. |
| `src/api/monitoringTypes.ts` | Monitoring batches, alerts, and trigger types. |
| `src/api/governanceTypes.ts` | Compliance, audit, metrics, and file response types. |
| `src/components/` | The application shell, mode banner, and reviewer switch. |
| `src/components/Sidebar.tsx` | Primary navigation. |
| `src/components/Topbar.tsx` | Workspace heading and reviewer control. |
| `src/components/ModeBanner.tsx` | Current mock, live, or snapshot mode notice. |
| `src/components/ReviewerProvider.tsx` | Shared reviewer identity state. |
| `src/components/ReviewerSwitch.tsx` | Reviewer role selector. |
| `src/components/StatusBadge.tsx` | Status with icon and text label. |
| `src/components/RatingBadge.tsx` | Validation rating display. |
| `src/components/TierBadge.tsx` | Risk tier display. |
| `src/components/MetricCard.tsx` | Headline metric display. |
| `src/components/ChartCard.tsx` | Chart surface and title. |
| `src/components/EmptyState.tsx` | Missing-data explanation. |
| `src/components/ErrorState.tsx` | Request failure display and retry action. |
| `src/components/StageStepper.tsx` | Five stage statuses and human sign-offs. |
| `src/components/GateReviewPanel.tsx` | Human stage approval and rejection controls. |
| `src/components/CodeViewer.tsx` | Highlighted source viewer with line numbers. |
| `src/components/EvidenceDrawer.tsx` | Loads and displays cited source evidence. |
| `src/tabs/PassportTab.tsx` | Inventory evidence, stage progress, and human review gate. |
| `src/tabs/DocumentationTab.tsx` | Grounded claims, source citations, and document drift. |
| `src/tabs/RedevelopmentTab.tsx` | Translation iterations, line mappings, and parity certificate. |
| `src/tabs/ValidationTab.tsx` | Validation metrics, fairness results, charts, and findings. |
| `src/tabs/MonitoringTab.tsx` | Batch drift, alert thresholds, and revalidation trigger. |
| `src/tabs/ComplianceTab.tsx` | Principle mapping and evidence coverage. |
| `src/tabs/AuditTab.tsx` | Model-scoped audit events and hash-chain status. |
| `src/mocks/` | JSON fixtures used by mock mode. |
| `src/pages/` | Landing, dashboard, inventory, and model workspace screens. |
| `src/pages/LandingPage.tsx` | Public landing page at `/`, built on screen by banna's cursors. |
| `src/landing.css` | Landing page styles, adapted from the banna demo and scoped under `.landing`. |
| `src/components/useBuildIn.ts` | Starts banna on the landing page and a light build of each console page header once per session. |
| `public/banna.js` | Vendored [banna](https://github.com/Rokhbin/banna) cursor-build script (MIT), patched so `Banna.start()` takes per-call options. |
| `public/banna-LICENSE.txt` | banna's MIT license. |
| `public/fonts/` | Vazirmatn Latin font for the landing page, with its SIL Open Font License. |
| `src/pages/DashboardPage.tsx` | Served at `/dashboard`: factory metrics, charts, scan action, and pipeline board. |
| `src/pages/InventoryPage.tsx` | Searchable and sortable model inventory. |
| `src/pages/ModelDetailPage.tsx` | Selected model header and seven model workspaces. |
| `src/formatting/` | Date, number, and status presentation helpers. |
| `package.json` | Scripts and application dependencies. |
| `package-lock.json` | Resolved dependency versions. |
| `.env.example` | Frontend mode and API URL settings. |
| `.gitignore` | Excludes local environment files and build output. |
| `tsconfig*.json` | TypeScript project configuration. |
| `README.md` | Setup, structure, environment, and API notes. |
| `src/App.tsx` | Shared layout and page outlet. |
| `src/routes.tsx` | Browser routes. |
| `src/main.tsx` | React entry point and query provider. |
| `src/index.css` | Tailwind entry point and global styles. |
| `src/formatting/formatNumbers.ts` | Number, percentage, and duration formatting. |
| `src/formatting/formatDates.ts` | UTC date and timestamp formatting. |
| `src/formatting/statusStyles.ts` | Status labels, colors, and icons. |
| `index.html` | Vite HTML entry point. |
| `vite.config.ts` | Vite and Tailwind configuration. |

## How to run

Requires Node.js 20.19 or newer.

```sh
npm install
npm run dev
```

The app starts in mock mode by default. To use factory_core, set `VITE_API_MODE=live` and `VITE_API_BASE_URL=http://localhost:8000` in a local `.env` file.

```sh
cp .env.example .env
```

The landing page is at `/` and the console starts at `/dashboard`. Add `?nobanna` to any URL to turn the cursor build off; it never runs for visitors who ask for reduced motion.

Open a model from the dashboard or inventory to use its Passport, Documentation, Redevelopment, Validation, Monitoring, Compliance, and Audit workspaces. The M001 fixtures demonstrate source evidence and result layouts; other models may intentionally show an unavailable-data state. In mock mode, runs pause at each human gate. Change the reviewer in the top bar before submitting a gate decision; the same reviewer cannot approve both redevelopment and validation.

## How to test

```sh
npm run build
```

The build runs the TypeScript project checks and creates the static site in `dist/`.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_MODE` | `mock` | Data source: `mock`, `live`, or `snapshot`. |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL for factory_core in live mode. |

## API

The browser calls factory_core only. `src/api/client.ts` switches among bundled JSON fixtures, factory_core, and files under `public/snapshot/`. No request is made directly to redev_engine or validation_lab.
