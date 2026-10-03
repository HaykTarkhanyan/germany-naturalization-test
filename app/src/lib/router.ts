// Minimal hash router (same as nemeceren's): "#/practice/bayern/all" -> ["practice", "bayern", "all"].
// Hash routes work on GitHub Pages without server rewrites.
import { useSyncExternalStore } from 'react'

function subscribe(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

export function useRoute(): string[] {
  return parseRoute(useSyncExternalStore(subscribe, () => window.location.hash))
}

export function parseRoute(hash: string): string[] {
  return hash
    .replace(/^#\/?/, '')
    .split('/')
    .filter(Boolean)
    .map((p) => decodeURIComponent(p))
}

export function link(...parts: string[]): string {
  return '#/' + parts.map((p) => encodeURIComponent(p)).join('/')
}

export function go(...parts: string[]): void {
  window.location.hash = link(...parts)
}
