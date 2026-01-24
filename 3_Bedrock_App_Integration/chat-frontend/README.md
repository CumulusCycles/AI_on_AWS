# Damage Assessment Frontend

React UI for automobile damage assessment: initial form (description + 3 photos) and follow-up chat. Connects to the backend at `http://localhost:8000`. The Admin Dashboard is a separate app in `admin-frontend/`.

## Features

- **Initial form**: Accident description and exactly 3 photos (wide-angle, straight-on, closeup); markdown-formatted assessment.
- **Follow-up chat**: Text-only (images optional); context from the initial assessment.
- **Conversations**: View and switch between conversations; new conversation clears the form.
- **Responsive** UI with Tailwind; validation before submit.

## Tech Stack

React 19, TypeScript, Vite, Tailwind CSS, Axios, React Markdown, Lucide.

## Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8000` ([../backend/README.md](../backend/README.md))

## Installation

```bash
cd chat-frontend
npm install
cp .env.example .env
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `http://localhost:8000` | Backend URL |

## Running

- **Dev**: `npm run dev` → http://localhost:3000
- **Build**: `npm run build` → `dist/`
- **Preview**: `npm run preview`

## Usage

### Initial assessment

1. Describe the accident in the text area.
2. Click **Select 3 images** and choose 3 photos: wide-angle, straight-on, closeup (JPEG, PNG, GIF, WebP; ≤ 3.75 MB each).
3. Click **Submit Assessment**. The response is shown with markdown formatting.

### Follow-up

After an assessment, type a question and click **Send**. Images are optional. Context is kept.

### Conversations

Use the conversations control (document icon) in the header to open the sidebar: **New Conversation** or select an existing one to load its history.

### Validation

- **Initial**: Non‑empty description and exactly 3 images required. Errors mention the missing part (e.g. "Please upload exactly 3 photos. You have 2.").
- **Follow-up**: Non‑empty text required.
- **Submit Assessment** / **Send** are disabled until the minimum input is present.

## Project Structure

```
chat-frontend/
├── src/
│   ├── components/     # ChatInterface, MessageList, ConversationSidebar
│   ├── services/       # api.ts
│   ├── types.ts, App.tsx, main.tsx, index.css
│   └── vite-env.d.ts
├── index.html, package.json, vite.config.ts, tailwind.config.js, ...
├── .env.example
└── README.md
```

## Development

- TypeScript strict; ESLint for React. Add API methods in `services/api.ts`, components in `components/`, types in `types.ts`.

## Troubleshooting

- **Connection / CORS**: Backend on 8000; check `VITE_API_URL` and [../backend/README.md](../backend/README.md).
- **Upload errors**: ≤ 3.75 MB, images only (JPEG, PNG, GIF, WebP); initial needs exactly 3.
- **Build**: `rm -rf node_modules && npm install`; Node 18+.
