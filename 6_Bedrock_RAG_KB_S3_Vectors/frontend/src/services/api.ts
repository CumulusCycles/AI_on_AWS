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
