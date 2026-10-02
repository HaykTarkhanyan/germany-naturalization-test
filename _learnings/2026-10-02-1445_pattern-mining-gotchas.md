# Pattern-mining gotchas: runtime, nondeterministic ties, plotly in a CSS grid

**1. Re-evaluating rules inside CV loops was 17x slower than needed.**
First full run of `scripts/mine_patterns.py` took 106 s: every rule recomputed word overlaps for the same
question thousands of times (5-fold CV x greedy decision list). Caching per question id (`memo_by_qid`) brought it
to 6 s with byte-identical output. Later the conditional-rule miner (1,456 word x selector combos) pushed it to
73 s; indexing questions by trigger word brought it back to 6.5 s, again identical output.

**2. Output differed between runs only in the order of tied weights.**
Sets of strings iterate in an order that depends on Python's per-process hash seed, so words with equal weights
came out in a different order. All metrics were identical. Fix: sort with an explicit tie-breaker
(`key=lambda r: (-r["weight"], r["word"])`). Verified by running twice and comparing the JSON.

**3. Plotly charts side by side in a CSS grid get clipped.**
Two `fig.to_html(full_html=False)` divs inside `display:grid; grid-template-columns: repeat(auto-fit,
minmax(420px, 1fr))` - the first chart was laid out wider than its column and only 2 of its 4 bars were visible
(seen in a headless Edge screenshot). Stacking the charts fixed it. Tables in the same grid are fine.

**4. Checking a local HTML report without Playwright.**
Playwright MCP was disconnected; headless Edge works for a quick visual check:
`msedge --headless=new --disable-gpu --hide-scrollbars --window-size=1200,9000 --virtual-time-budget=10000
--screenshot=<png> file:///<path>.html`, then crop with Pillow to read sections at full resolution.
