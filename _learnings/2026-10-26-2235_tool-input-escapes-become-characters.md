# Backslash escapes in Claude's tool inputs arrive as real characters

**Symptom:** Twice in one session code came out different from what was written. `app/src/lib/search.ts` got the
regex `/[̀-ͯ]/` with two invisible combining characters instead of the escape range for U+0300 to U+036F (it still
worked, unreadably). `app/vite.config.ts` got a string literal split over two lines by a real carriage return and
line break where the escaped CR LF pair was meant, found only because a grep printed the line broken:

```
b"replaceAll('\r\r\n', '\r\n'), 'latin1')"     # bytes in the file
```

**Cause:** Tool inputs (file contents for Write and Edit, heredocs for Bash) travel as JSON strings, so JSON escapes
in them are decoded before the file is written: backslash-u plus four hex digits, backslash-r, backslash-n,
backslash-t, backslash-b, backslash-f. Escapes that are not JSON escapes (backslash-d, backslash-s, backslash-S,
backslash-dot) pass through unchanged, which is why most regexes were fine. Separately, Python's `Path.write_text`
on Windows writes CRLF for every newline unless `newline="\n"` is passed (3.10 supports it for `write_text`, not for
`read_text`).

**Fix used:** rebuild the text from character codes (`chr(92)` for the backslash) or bytes, then verify the bytes
(`repr` of the slice) and scan all touched files for lone or doubled CRs and literal combining characters.

**Consequences:** When code needs a literal backslash-u, -r, -n, -t, -b or -f escape, check the written bytes right
after writing; prefer writing such lines via a short script that builds them from character codes.
