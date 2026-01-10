# Frontend Scaffolding Guide

This guide will help you scaffold a React application with TypeScript, Tailwind CSS, form handling, and validation.

## Prerequisites

- Node.js 20.x or higher
- npm or yarn

## Step-by-Step Scaffolding

### Step 1: Create React App with Vite

```bash
cd 1_Purpose_Built_AI_Services_Demo_Apps/AWS_App_Deployment
npm create vite@latest frontend -- --template react-ts
```

**Note:** When prompted:
- **"Use rolldown-vite (Experimental)?"** → Answer **No** (press Enter or type `n`) to use the stable Vite bundler
- **"Install with npm and start now?"** → Answer **No** (press Enter or type `n`) - we'll install dependencies manually in the next steps to have more control

### Step 2: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 3: Install Base Dependencies

Install the default dependencies for the new Vite project:

```bash
npm install
```

### Step 4: Install Additional Dependencies

Install dependencies needed for form handling and validation:

```bash
npm install react-hook-form @hookform/resolvers zod
```

**What these do:**
- `react-hook-form` - Form state management and validation
- `@hookform/resolvers` - Integration between react-hook-form and validation libraries
- `zod` - TypeScript-first schema validation

### Step 5: Install Tailwind CSS

Install Tailwind CSS v4+ and its dependencies for utility-first styling:

```bash
npm install -D tailwindcss @tailwindcss/postcss autoprefixer
```

**What these do:**
- `tailwindcss` - Utility-first CSS framework
- `@tailwindcss/postcss` - Tailwind CSS v4+ PostCSS plugin
- `autoprefixer` - Automatically adds vendor prefixes to CSS

**Note:** Tailwind CSS v4+ requires `@tailwindcss/postcss` instead of the standalone `postcss` package. The configuration below is for v4+.

### Step 6: Create Tailwind Configuration Files

Tailwind CSS requires configuration files. Since `npx tailwindcss init -p` may fail on some systems, manually create the configuration files:

**Create `tailwind.config.js` in the `frontend` directory:**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Create `postcss.config.js` in the `frontend` directory:**

```js
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

### Step 7: Configure Tailwind CSS in index.css

Update `src/index.css` to include Tailwind CSS. Replace the entire contents with:

```css
@import "tailwindcss";

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
```

**Note:** Tailwind CSS v4+ uses `@import "tailwindcss";` instead of the old `@tailwind` directives. This single import statement replaces the previous `@tailwind base`, `@tailwind components`, and `@tailwind utilities` directives.

### Step 8: Install ESLint (Optional but Recommended)

Install ESLint and TypeScript plugins for code linting and quality checks:

```bash
npm install -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-plugin-react-hooks eslint-plugin-react-refresh
```

**What these do:**
- `eslint` - JavaScript/TypeScript linter
- `@typescript-eslint/*` - TypeScript-specific ESLint rules
- `eslint-plugin-react-hooks` - React Hooks linting rules
- `eslint-plugin-react-refresh` - React Fast Refresh linting rules


### Step 9: Run the App

Start the development server:

```bash
npm run dev
```

The app will start and Vite will display the local URL (typically `http://localhost:5173`). Open this URL in your browser to view the application.

**What you should see:**
- The default Vite + React welcome page
- Tailwind CSS styles should be working (you'll see styled content)
- The development server will automatically reload when you make changes to your code

**To stop the server:**
Press `Ctrl+C` (or `Cmd+C` on Mac) in the terminal where the server is running.