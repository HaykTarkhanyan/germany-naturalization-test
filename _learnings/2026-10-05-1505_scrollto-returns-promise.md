# window.scrollTo returns a Promise in current Chromium - never return it from useEffect

**Symptom:** Every lesson page (`#/learn/<topic>`) rendered nothing: React unmounted the whole app. The browser console showed React's warning "useEffect must not return anything besides a function, which is used for clean-up" and then `TypeError: destroy is not a function` (twice, StrictMode).

**Cause:** The effect was written as an expression arrow, so it returned the call's value:

```tsx
useEffect(() => window.scrollTo(0, 0), [])
```

In current Chromium/Edge, scroll methods return a Promise (measured 2026-10-05 in headless Edge 154.0.4258.53: `String(window.scrollTo(0, 0))` -> `[object Promise]`). React takes any non-undefined return value as the cleanup function and calls it on unmount -> crash. In older browsers `scrollTo` returned `undefined`, so the same line used to be harmless; `tsc` did not flag it either.

**Fix:** block body, no return value:

```tsx
useEffect(() => {
  window.scrollTo(0, 0)
}, [])
```

**Consequences:** Unit tests (Vitest, no DOM scroll) could not catch this; only the browser check did. Any effect whose single statement is a DOM call should use a block body.
