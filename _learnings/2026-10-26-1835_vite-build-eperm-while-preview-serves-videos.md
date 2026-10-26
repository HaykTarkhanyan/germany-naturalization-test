# `npm run build` fails with EPERM on Windows while `vite preview` is serving the videos

**Symptom:** Rebuilding while the preview server was still running failed with

```
[plugin vite:prepare-out-dir]
Error: EPERM: operation not permitted, lstat '...\app\dist\videos\02_mauer_einheit.ru.mp4'
```

**Cause:** Since the videos are part of the build (DECISIONS.md #23), `vite preview` holds the MP4s in `dist/videos/`
open after a browser has played or seeked in them, and Windows does not let Vite empty `dist/` while a file in it is
open.

**Fix:** Stop the preview server before rebuilding (find it by port:
`Get-NetTCPConnection -LocalPort 4179 -State Listen`, then `Stop-Process` its `OwningProcess`), build, start the
preview again. Not a code problem: the build passed right after the server was stopped.
