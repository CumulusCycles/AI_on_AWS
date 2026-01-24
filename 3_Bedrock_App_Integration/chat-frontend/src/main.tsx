/**
 * Damage Assessment UI entry. Mounts App into #root with StrictMode.
 * index.css (Tailwind + scrollbar-thin) is imported here.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
