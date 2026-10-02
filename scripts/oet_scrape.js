// Scrape options + correct answers from the BAMF Online-Testcenter (oet.bamf.de).
//
// How it was run (2026-10-02): through the Playwright MCP server, not as a standalone Node script.
//   1. browser_navigate  https://oet.bamf.de/ords/oetut/f?p=514:1:0
//   2. select "Bayern" in the Bundesland dropdown (#P1_BUL_ID), click "Zum Fragenkatalog"
//   3. browser_run_code_unsafe with the function below, once per batch:
//      START/END = 1-105, 106-210, 211-310 (~2.5 min per batch, ~1.1 s per question;
//      a single 310-question run would exceed the MCP tool timeout)
//   4. after each batch: browser_evaluate `() => JSON.stringify(window.__oet)` with
//      filename .playwright-mcp/oet_<START>_<END>.json, then copy to data/raw/
//      (the sandbox only allows writes inside the repo; the result is a JSON string wrapped in JSON)
//
// Why it works: the question stem is served as an image, but every option is plain text and the
// correct option's radio button carries id="FARBE" (the page's JS paints that one green).
// The APEX session expires after a while; if the dropdown stops navigating, restart from step 1.
//
// Then run: python scripts/build_dataset.py

async (page) => {
  const START = 1, END = 105;
  const toDataUrl = `async (src) => { const b = await (await fetch(src)).blob(); return await new Promise(res => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(b); }); }`;
  const extract = async () => page.evaluate(async (toDataUrlSrc) => {
    const toDataUrl = eval(toDataUrlSrc);
    const hdr = [...document.querySelectorAll('td')].map(t => t.innerText.trim()).find(t => /^Aufgabe \d+ von \d+$/.test(t));
    const num = hdr ? parseInt(hdr.match(/Aufgabe (\d+)/)[1]) : null;
    const opts = [];
    for (const r of document.querySelectorAll('input[name=f20]')) {
      const td = r.closest('tr').querySelector('td[headers=ANTWORT]');
      const im = td.querySelector('img');
      opts.push({ value: r.value, text: td.innerText.trim(), correct: r.id === 'FARBE', img: im ? await toDataUrl(im.src) : null });
    }
    const img = document.querySelector('#P30_AUFGABENSTELLUNG_BILD img');
    return { num, opts, stem_img: img ? await toDataUrl(img.src) : null };
  }, toDataUrl);
  // jump to START via the "Gehe zu Aufgabe Nr." dropdown (option value is the row number)
  await Promise.all([page.waitForNavigation(), page.selectOption('#P30_ROWNUM', String(START))]);
  const data = [];
  const t0 = Date.now();
  for (let n = START; n <= END; n++) {
    const q = await extract();
    if (q.num !== n) throw new Error(`expected question ${n}, page shows ${q.num}`);
    if (q.opts.filter(o => o.correct).length !== 1) throw new Error(`question ${n}: correct count = ${q.opts.filter(o => o.correct).length}`);
    data.push(q);
    if (n < END) await Promise.all([page.waitForNavigation(), page.click('input[name=GET_NEXT_ID]')]);
  }
  await page.evaluate(d => { window.__oet = d; }, data);
  return { got: data.length, first: data[0].num, last: data[data.length - 1].num, seconds: (Date.now() - t0) / 1000 };
}
