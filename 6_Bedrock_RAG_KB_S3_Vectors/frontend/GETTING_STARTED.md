# Build this app from scratch

Start with an **empty folder**. You will scaffold the project, create each file and folder, and paste in the code we provide — same hands-on approach as creating IAM policies or the Lambda: you do the steps, we give you the content. By the end you’ll have the full RAG frontend running locally.

---

## What you’re building

A React app that sends a question to your API (API Gateway + Lambda), then shows the answer and source documents. You’ll use Vite, TypeScript, and Tailwind.

---

## Prerequisites

- **Node.js 18+** — [nodejs.org](https://nodejs.org) (LTS). Check with `node -v`.
- **npm** — comes with Node. Check with `npm -v`.
- **Your API URL** — backend must be deployed. You need the invoke URL (e.g. `https://…execute-api.us-east-1.amazonaws.com/chat`).

---

## Step 1 — Scaffold the project

**What you’ll do:** Create a new Vite + React + TypeScript app in your folder.

**Do it:** Open a terminal. Create an empty folder (e.g. `rag-frontend`) and go into it. Then run:

```bash
npm create vite@latest . -- --template react-ts
```

When prompted, confirm if the folder isn’t empty. Then install dependencies:

```bash
npm install
```

You now have `index.html`, `src/main.tsx`, `src/App.tsx`, `src/index.css`, and config files. Leave them in place; we’ll edit or replace content in the next steps.

---

## Step 2 — Install extra dependencies

**What you’ll do:** Add Tailwind, icons, and Markdown rendering.

**Do it:** In the same folder (project root), run:

```bash
npm install react-markdown lucide-react
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

We use **Tailwind v3** on purpose: v3 includes the CLI, so `npx tailwindcss init -p` works. If you install without a version you may get v4, which doesn’t ship the same CLI and that command can fail.

That should create `tailwind.config.js` and `postcss.config.js`.

**If `npx tailwindcss init -p` fails** (e.g. “could not determine executable to run”, common with some Tailwind versions): create the two files by hand. In the project root, create **`postcss.config.js`** with:

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

Create **`tailwind.config.js`** with a minimal placeholder for now (e.g. `export default { content: [] };`). You’ll replace its contents in Step 3.

---

## Step 3 — Configure Tailwind

**What you’ll do:** Point Tailwind at your source files and add the app’s color theme.

**Do it:** Open `tailwind.config.js`. Replace its entire contents with:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aws: {
          orange: '#ff9900',
          'orange-dark': '#e88a00',
          squid: '#0d1117',
          ink: '#1b2230',
          card: '#1f2937',
          border: '#374151',
          text: '#d4dae3',
          muted: '#9ca3af',
        },
      },
    },
  },
  plugins: [],
};
```

Save the file.

---

## Step 4 — Add global styles

**What you’ll do:** Replace the default Vite CSS with Tailwind and a dark theme.

**Do it:** Open `src/index.css`. Delete everything in the file and paste:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-aws-squid text-aws-text;
  }
}

@layer components {
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: #374151 transparent;
  }
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: #374151;
    border-radius: 3px;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: #4b5563;
  }
}
```

Save the file.

---

## Step 5 — Add TypeScript types for the API

**What you’ll do:** Create a small types file so the rest of the app is type-safe.

**Do it:** Create a new file `src/types.ts`. Paste:

```ts
export interface QueryResponse {
  query: string;
  generated_response: string;
  s3_locations: string[];
}
```

Save the file.

---

## Step 6 — Tell TypeScript about the API URL env variable

**What you’ll do:** Declare `VITE_API_URL` so TypeScript and your editor recognize it.

**Do it:** Create a new file `src/vite-env.d.ts`. Paste:

```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

Save the file.

---

## Step 7 — Create the API service

**What you’ll do:** Add a module that sends the question to your API and returns the response.

**Do it:** Create a folder `src/services`. Inside it, create a new file `src/services/api.ts`. Paste:

```ts
import type { QueryResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL;

export async function askQuestion(query: string): Promise<QueryResponse> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error ?? `HTTP ${response.status}`);
  }

  return data as QueryResponse;
}
```

Save the file.

---

## Step 8 — Create the SourcePill component

**What you’ll do:** Add a small component that shows one source document as a pill.

**Do it:** Create a folder `src/components`. Inside it, create a new file `src/components/SourcePill.tsx`. Paste:

```tsx
interface SourcePillProps {
  uri: string;
}

export default function SourcePill({ uri }: SourcePillProps) {
  const filename = uri.split('/').pop()?.replace(/_/g, ' ').replace(/\.md$/, '') ?? uri;
  return (
    <span className="inline-block bg-[#2a2000] text-aws-orange border border-aws-orange rounded px-2.5 py-0.5 text-xs font-mono mr-1.5 mb-1.5">
      {filename}
    </span>
  );
}
```

Save the file.

---

## Step 9 — Create the ExamplePrompts component

**What you’ll do:** Add a component that shows clickable example questions.

**Do it:** In the same `src/components` folder, create a new file `src/components/ExamplePrompts.tsx`. Paste:

```tsx
const EXAMPLES = [
  'What products does AI Agent Insure offer?',
  'What does Agentic AI Liability Insurance cover?',
  'How does the claims process work?',
  'What is the coverage limit for AI Infrastructure Operations Protection?',
  'Does AI Agent Insure cover regulatory fines?',
  'What incidents are covered under Autonomous Systems & Robotics Coverage?',
];

interface ExamplePromptsProps {
  onSelect: (prompt: string) => void;
}

export default function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="mt-6">
      <p className="text-xs uppercase tracking-widest text-aws-muted font-semibold mb-3">
        Try asking…
      </p>
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => onSelect(ex)}
            className="text-sm bg-aws-card border border-aws-border text-aws-text rounded-md px-3 py-1.5 hover:border-aws-orange hover:text-aws-orange transition-colors text-left"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
```

Save the file.

---

## Step 10 — Build the main App

**What you’ll do:** Replace the default Vite App with the full UI: header, question input, submit, loading/error/success, answer (Markdown), and source pills.

**Do it:** Open `src/App.tsx`. Select all and delete. Paste:

```tsx
import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, Shield, BookOpen, AlertCircle, Loader2 } from 'lucide-react';
import { askQuestion } from './services/api';
import type { QueryResponse } from './types';
import SourcePill from './components/SourcePill';
import ExamplePrompts from './components/ExamplePrompts';

type Status = 'idle' | 'loading' | 'success' | 'error';

export default function App() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  async function handleSubmit(q: string = query) {
    const trimmed = q.trim();
    if (!trimmed) return;

    setStatus('loading');
    setResult(null);
    setErrorMsg('');

    try {
      const data = await askQuestion(trimmed);
      setResult(data);
      setStatus('success');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'An unexpected error occurred.');
      setStatus('error');
    }
  }

  function handleExampleSelect(prompt: string) {
    setQuery(prompt);
    textareaRef.current?.focus();
    handleSubmit(prompt);
  }

  return (
    <div className="min-h-screen bg-aws-squid">
      <header className="border-b border-aws-border bg-[#161b22]">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <Shield className="text-aws-orange" size={28} />
          <div>
            <h1 className="text-lg font-bold text-aws-text leading-tight">AI Agent Insure</h1>
            <p className="text-xs text-aws-muted">Knowledge Assistant · Amazon Bedrock RAG + S3 Vectors</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="mb-8 flex items-start gap-3">
          <BookOpen className="text-aws-orange mt-0.5 shrink-0" size={20} />
          <p className="text-aws-muted text-sm leading-relaxed">
            Ask any question about AI Agent Insure products, coverage, or policies. Answers are
            generated by <strong className="text-aws-text">Amazon Bedrock</strong> using
            Retrieval-Augmented Generation (RAG) backed by an{' '}
            <strong className="text-aws-text">S3 Vectors</strong> knowledge base.
          </p>
        </div>

        <div className="bg-aws-ink border border-aws-border rounded-lg p-5">
          <label htmlFor="query" className="block text-xs uppercase tracking-widest text-aws-muted font-semibold mb-2">
            Your question
          </label>
          <textarea
            id="query"
            ref={textareaRef}
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit();
            }}
            placeholder="e.g. What does Agentic AI Liability Insurance cover?"
            className="w-full bg-aws-squid border border-aws-border rounded-md px-4 py-3 text-aws-text placeholder-aws-muted text-sm resize-none focus:outline-none focus:border-aws-orange transition-colors"
          />
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-aws-muted">⌘ + Enter to submit</span>
            <button
              onClick={() => handleSubmit()}
              disabled={status === 'loading' || !query.trim()}
              className="flex items-center gap-2 bg-aws-orange hover:bg-aws-orange-dark disabled:opacity-40 disabled:cursor-not-allowed text-[#0d1117] font-bold text-sm px-5 py-2 rounded-md transition-colors"
            >
              {status === 'loading' ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Search size={16} />
              )}
              {status === 'loading' ? 'Searching…' : 'Ask'}
            </button>
          </div>
        </div>

        {status === 'idle' && (
          <ExamplePrompts onSelect={handleExampleSelect} />
        )}

        {status === 'error' && (
          <div className="mt-6 flex items-start gap-3 bg-red-950 border border-red-800 rounded-lg px-5 py-4">
            <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={18} />
            <div>
              <p className="text-red-300 font-semibold text-sm">Request failed</p>
              <p className="text-red-400 text-sm mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        {status === 'success' && result && (
          <div className="mt-6 space-y-4">
            <div className="bg-aws-ink border-l-4 border-aws-orange rounded-lg px-6 py-5">
              <p className="text-xs uppercase tracking-widest text-aws-orange font-semibold mb-3">
                Answer
              </p>
              <div className="prose prose-invert prose-sm max-w-none text-aws-text leading-relaxed">
                <ReactMarkdown>{result.generated_response}</ReactMarkdown>
              </div>
            </div>

            {result.s3_locations.length > 0 && (
              <div className="bg-aws-card border border-aws-border rounded-lg px-6 py-4">
                <p className="text-xs uppercase tracking-widest text-aws-muted font-semibold mb-3">
                  Sources retrieved from knowledge base
                </p>
                <div className="flex flex-wrap">
                  {result.s3_locations.map((uri) => (
                    <SourcePill key={uri} uri={uri} />
                  ))}
                </div>
              </div>
            )}

            <ExamplePrompts onSelect={handleExampleSelect} />
          </div>
        )}
      </main>
    </div>
  );
}
```

Save the file.

---

## Step 11 — Wire up the entry point

**What you’ll do:** Ensure the app loads global CSS and renders `App`.

**Do it:** Open `src/main.tsx`. If it doesn’t already match, replace its contents with:

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

Save the file.

---

## Step 12 — Set the page title

**What you’ll do:** Give the browser tab a proper title.

**Do it:** Open `index.html`. Find the `<title>` tag and set it to:

```html
<title>AI Agent Insure — Knowledge Assistant</title>
```

Save the file.

---

## Step 13 — Set your API URL

**What you’ll do:** Create a `.env` file so the app knows where to send requests.

**Do it:** In the project root (same folder as `package.json`), create a new file named `.env`. Paste this line, then replace the URL with your real API Gateway invoke URL:

```env
VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/chat
```

Use the URL from your AWS Console (HTTP API, no stage in the path — e.g. `/chat` not `/prod/chat`). Save the file.

---

## Step 14 — (Optional) Set the dev server port

**What you’ll do:** Force the dev server to use port 3000.

**Do it:** Open `vite.config.ts`. Replace its contents with:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
});
```

Save the file. (If you skip this, Vite will use its default port, often 5173.)

---

## Step 15 — Run the app

**What you’ll do:** Start the dev server and open the app in the browser.

**Do it:** In the project root, run:

```bash
npm run dev
```

Open the URL shown in the terminal (e.g. **http://localhost:3000**). You should see the AI Agent Insure header, question box, and example prompts. Type a question and click **Ask** (or use ⌘+Enter). If your API is deployed and `VITE_API_URL` is correct, you’ll get an answer and source pills.

If you see a network or CORS error, double-check `.env` and that your API Gateway and Lambda allow requests from your origin (e.g. `http://localhost:3000`).

---

## What you did

You started from an empty folder and:

1. Scaffolded a Vite + React + TypeScript project  
2. Installed Tailwind, PostCSS, and extra npm packages  
3. Created and edited config and style files  
4. Created `src/types.ts`, `src/vite-env.d.ts`, and `src/services/api.ts`  
5. Created `src/components/SourcePill.tsx` and `src/components/ExamplePrompts.tsx`  
6. Replaced `src/App.tsx` with the full UI  
7. Set `main.tsx`, `index.html`, and `.env`  
8. Ran the app with `npm run dev`  
