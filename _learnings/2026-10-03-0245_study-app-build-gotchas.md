# Study app build gotchas: JSON import attributes, Playwright dialogs, orphaned dev server

**1. `tsc -b` failed on the JSON imports, Vite and Vitest did not.**
`src/lib/data.ts` imports `../../../data/*.json`. The test files are also checked by `tsconfig.node.json`
(`module: nodenext`), which requires an import attribute:
```
src/lib/data.ts(4,27): error TS1543: Importing a JSON file into an ECMAScript module requires a 'type: "json"' import attribute when 'module' is set to 'NodeNext'.
```
Fix: `import questionsJson from '../../../data/questions_bayern.json' with { type: 'json' }`. Vite 8 accepts it,
tests and build pass. Vitest alone passed before the fix, so run `npm run build` (tsc + vite), not only `npm test`.

**2. Playwright MCP intercepts `window.confirm`.**
`page.once('dialog', d => d.accept())` inside `browser_run_code_unsafe` raced with the MCP's own modal handling:
the code's return value was lost ("Modal state ... can be handled by browser_handle_dialog") although the
dialog was accepted and the page moved on. Re-read the state afterwards instead of trusting the run's output, or
avoid confirm dialogs in scripted flows.

**3. TaskStop does not kill the Windows child processes of `npm run dev`.**
After stopping the background task, `npm run dev` (node npm-cli.js) and `vite.js` were still running and holding
port 5174. Found with `Get-CimInstance Win32_Process -Filter "Name='node.exe'"`, stopped by exact PID after
checking their command lines. Other node processes (nemeceren's check-content, MCP servers) belong to other
sessions - never kill by name.
