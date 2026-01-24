# Admin Dashboard Frontend

React UI for monitoring and managing the Bedrock App Integration: analytics, conversations, model usage, system info. Connects to the backend at `http://localhost:8000`. The Damage Assessment UI is in `chat-frontend/`.

## Features

- **Analytics**: Stats and timeline charts; filter by 7, 30, or 90 days.
- **Conversations**: List, search, sort, view, delete.
- **Models**: Usage and token stats per model.
- **System info**: Totals and default config.
- **Auto-refresh**: Polling interval configurable via `VITE_POLLING_INTERVAL` (default 15s).

## Tech Stack

React 19, TypeScript, Vite, Tailwind CSS, Axios, Recharts, Lucide.

## Prerequisites

- Node.js 18+
- Backend on `http://localhost:8000` ([../backend/README.md](../backend/README.md))

## Installation

```bash
cd admin-frontend
npm install
cp .env.example .env
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `http://localhost:8000` | Backend URL |
| `VITE_POLLING_INTERVAL` | `15000` | Polling interval (ms) |

## Running

- **Dev**: `npm run dev` → http://localhost:3001
- **Build**: `npm run build` → `dist/`
- **Preview**: `npm run preview`

## Usage

Tabs: **Analytics**, **Conversations**, **Models**, **System Info**. Data refreshes automatically. In Conversations you can search by conversation or user ID, sort, open a conversation to see messages and images, and delete.

## Project Structure

```
admin-frontend/
├── src/
│   ├── components/   # Analytics, Conversations, Models, SystemInfo
│   ├── services/     # api.ts
│   ├── config.ts, types.ts, App.tsx, main.tsx, index.css
│   └── vite-env.d.ts
├── index.html, package.json, vite.config.ts, tailwind.config.js, ...
├── .env.example
└── README.md
```

## Development

- TypeScript strict; ESLint. Add API methods in `services/api.ts`, components in `components/`, types in `types.ts`, views in `App.tsx`.

## Troubleshooting

- **Connection / CORS**: Backend on 8000; check `VITE_API_URL` and [../backend/README.md](../backend/README.md).
- **Build**: `rm -rf node_modules && npm install`; Node 18+.
- **Charts**: `npm install recharts` if missing; check console for errors.
