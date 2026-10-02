"""Build the HTML report on the answer patterns from results/patterns.json (written by mine_patterns.py).

Run:      uv run python scripts/build_pattern_report.py
Output:   reports/patterns_report.html (single offline file, plotly.js inlined, ~5 MB)
Runtime:  ~2 s (measured on this laptop)
"""

import html
import json
import logging
import statistics
import time
from pathlib import Path

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "patterns.json"
SHEET_ORDER = ROOT / "results" / "sheet_order_check.json"   # from scripts/check_sheet_order.py
QUESTIONS = ROOT / "data" / "questions_bayern.json"
OUT = ROOT / "reports" / "patterns_report.html"

RED, BLUE, ORANGE, GREY = "#D90012", "#0033A0", "#F2A800", "#9aa0a6"

(ROOT / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(ROOT / "logs" / "build_pattern_report.log", encoding="utf-8")],
)
log = logging.getLogger("build_pattern_report")

_first_figure = True


def fig_html(fig: go.Figure, height: int = 420) -> str:
    """Inline plotly.js with the first figure only, so the file works offline without duplicating it."""
    global _first_figure
    fig.update_layout(height=height, margin=dict(l=10, r=40, t=50, b=40), template="plotly_white",
                      font=dict(family="Segoe UI, Arial, sans-serif", size=13))
    out = fig.to_html(full_html=False, include_plotlyjs=_first_figure, config={"displaylogo": False})
    _first_figure = False
    return out


def esc(s) -> str:
    return html.escape(str(s))


def pct(x, digits=0) -> str:
    return "-" if x is None else f"{x * 100:.{digits}f}%"


def heat(value: float, pivot: float, lo: float, hi: float) -> str:
    """Diverging green-white-red background, white at the median, alpha capped at 0.4."""
    if value is None:
        return ""
    if value >= pivot:
        a = 0.4 * min(1.0, (value - pivot) / (hi - pivot)) if hi > pivot else 0
        return f"background: rgba(0,150,60,{a:.2f})"
    a = 0.4 * min(1.0, (pivot - value) / (pivot - lo)) if pivot > lo else 0
    return f"background: rgba(217,0,18,{a:.2f})"


def table(headers: list[str], widths: list[str], rows: list[list[str]], numeric_cols: set[int] = frozenset(),
          raw: bool = False) -> str:
    cols = "".join(f'<col style="width:{w}">' for w in widths)
    head = "".join(f'<th class="{"num" if i in numeric_cols else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    body = ""
    for row in rows:
        cells = ""
        for i, c in enumerate(row):
            style = ""
            if isinstance(c, tuple):  # (text, style)
                c, style = c
            cells += f'<td class="{"num" if i in numeric_cols else ""}" style="{style}">{c if raw else esc(c)}</td>'
        body += f"<tr>{cells}</tr>"
    return f'<table><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def hbar(labels, values, texts, colors, title, x_title, baseline=None, x_max=None) -> go.Figure:
    fig = go.Figure(go.Bar(y=labels, x=values, orientation="h", text=texts, textposition="outside",
                           marker_color=colors, cliponaxis=False, hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    if baseline is not None:
        fig.add_vline(x=baseline, line_dash="dash", line_color="black",
                      annotation_text=f"blind guess {baseline:.0%}", annotation_position="top")
    fig.update_layout(title=dict(text=title), xaxis=dict(title=x_title, tickformat=".0%",
                                                         range=[0, x_max or max(values) * 1.25]),
                      yaxis=dict(autorange="reversed"))
    return fig


def main() -> None:
    t0 = time.perf_counter()
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    sheet_order = json.loads(SHEET_ORDER.read_text(encoding="utf-8"))
    qmap = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    meta, exam, mem = r["meta"], r["exam"], r["memorization"]
    pick = {p["id"]: p for p in r["picker_rules"]}
    feat = {f["feature"]: f for f in r["option_features"]}
    dl = r["decision_list"]
    words = r["word_rules"]
    cond = r["conditional_rules"]
    cv = r["cv"]
    sections = []

    # ---------------------------------------------------------------- headline
    best_cv_name = max((k for k in exam if "cross-validated" in k), key=lambda k: exam[k]["p_pass"])
    cards = [
        ("Pass by blind guessing", pct(exam["blind guessing"]["p_pass"], 1),
         f"expected {exam['blind guessing']['expected_score']:.1f} of 33"),
        ("Best 'know nothing' strategy", pct(exam[best_cv_name]["p_pass"], 1),
         f"{best_cv_name}; expected {exam[best_cv_name]['expected_score']:.1f} of 33"),
        ("Questions to memorize for 95% pass, no tricks", str(mem["blind guessing"]["memorize_for"]["0.95"]),
         "guess the rest"),
        ("... with the rules below", str(mem["decision list (in-sample)"]["memorize_for"]["0.95"]),
         "memorize only where the rules fail, Bayern first"),
        ("... if the exam shuffles the options", str(mem["decision list, options shuffled"]["memorize_for"]["0.95"]),
         "content rules still work, the 'default to B' part does not"),
    ]
    cards_html = "".join(f'<div class="card"><div class="big">{esc(v)}</div><div class="lbl">{esc(t)}</div>'
                         f'<div class="sub">{esc(s)}</div></div>' for t, v, s in cards)
    sections.append(f"""
<h2>Bottom line</h2>
<div class="cards">{cards_html}</div>
<p><b>No trick passes the test on its own.</b> The best combination of patterns, scored honestly on questions it
had not seen, gets about {cv['words_and_features']['test_accuracy']:.0%} of answers right (blind guessing: 25%),
which is a {pct(exam[best_cv_name]['p_pass'], 1)} chance of reaching 17/33. What the patterns <i>do</i> buy you is
less memorizing: learn a handful of rules plus the questions where they fail, and
{mem['decision list (in-sample)']['memorize_for']['0.95']} memorized answers give a 95% pass chance instead of
{mem['blind guessing']['memorize_for']['0.95']}.</p>
<p>The popular tips are mostly myths here: "the longest answer" is right {pct(pick['longest']['precision'])} of the
time, and for numbers the <b>lowest</b> option is almost never right ({pick['num_lowest']['hits']} of
{pick['num_lowest']['support']}).</p>""")

    # ---------------------------------------------------------------- cheat sheet
    steps = "".join(
        f"<li><b>{esc(s['name'])}</b> - right {s['hits']} of {s['fired']} times ({pct(s['precision'])})</li>"
        for s in dl["steps"])
    cross = "".join(
        f"<li>{esc(feat[c]['label'])}: correct {feat[c]['correct']} of {feat[c]['options']} "
        f"({pct(feat[c]['p_correct'])})</li>" for c in meta["cross_out"] if c in feat)
    neg_words = [w for w in words["rules"] if w["direction"] == "negative" and w["folds_qualified"] >= 3]
    neg_list = ", ".join(f"<b>{esc(w['word'])}</b> (0/{w['options']})" for w in neg_words)
    pref = "".join("ABCD"[k] for k in dl["fallback_preference"])
    nr = r["numeric"]["rank_counts"]
    sections.append(f"""
<h2>Cheat sheet</h2>
<p>Use these in order; the first one that applies decides. Precision is measured on all 310 questions, which is
exactly the pool your test is drawn from.</p>
<ol>{steps}</ol>
<p><b>Then cross out</b> options that are almost never right:</p>
<ul>{cross}<li>options with the words {neg_list} - never right in the whole pool, and the pattern held on
held-out questions too</li></ul>
<p><b>Numbers:</b> sorted from low to high, the right answer was the lowest {nr[0]}x, second-lowest {nr[1]}x,
second-highest {nr[2]}x, highest {nr[3]}x (of {r['numeric']['n']}). Key numbers worth knowing:
{', '.join(str(int(v)) for v in meta['key_numbers'])}.</p>
<p><b>Still unsure?</b> Pick the first option not crossed out in the order <b>{pref}</b>
(B is the most common correct position: {r['position_counts']['B']} of 310). This last step only helps if the printed
sheet keeps the catalog's option order - see "Does the real exam keep the option order?" below. If it does not,
just guess among the options you have not crossed out.</p>
<p>This list answers {dl['accuracy']:.0%} of the 310 questions correctly. That is in-sample: the same list fitted on
4/5 of the questions scores {dl['cv_accuracy']:.0%} on the other 1/5, so treat it as a memory aid for this pool,
not as a general law.</p>""")

    # ---------------------------------------------------------------- popular tricks vs reality
    myth_ids = ["longest", "longest_words", "shortest", "convergence", "odd_length", "pos_A", "pos_B", "pos_C",
                "pos_D", "num_lowest", "num_highest", "num_2nd_highest", "echo", "lex_values", "lex_legal_remedy"]
    myths = [pick[i] for i in myth_ids]
    fig = hbar([m["name"] for m in myths], [m["precision"] for m in myths],
               [f"{m['precision']:.0%}  ({m['hits']}/{m['support']})" for m in myths],
               [BLUE if m["precision"] > 0.3 else RED if m["precision"] < 0.2 else GREY for m in myths],
               "How often common shortcuts pick the right answer", "precision (when the rule applies)",
               baseline=0.25, x_max=0.85)
    sections.append(f"<h2>Popular tricks vs. reality</h2>{fig_html(fig, 560)}"
                    "<p class='note'>Bar = share of questions where the rule applied and picked the right option; "
                    "(hits/support). Blue: clearly above guessing, red: clearly below, grey: about the same.</p>")

    # ---------------------------------------------------------------- all picker rules table
    precs = [p["precision"] for p in r["picker_rules"] if p["precision"] is not None]
    med, lo, hi = statistics.median(precs), min(precs), max(precs)
    rows = []
    for p in r["picker_rules"]:
        if not p["support"]:
            continue
        rows.append([p["name"], p["source"], str(p["support"]), str(p["hits"]),
                     (pct(p["precision"]), heat(p["precision"], med, lo, hi)),
                     f"{pct(p['ci_low'])}-{pct(p['ci_high'])}", str(p["net_gain"]), p["verdict"]])
    sections.append(f"""
<h2>All {meta['n_picker_rules']} picker rules</h2>
<p>Support = questions where the rule applies (it abstains on ties). Net gain = hits - misses, i.e. how many
answers the rule saves you if you also have to remember its exceptions. "Better/worse" means significant after
Bonferroni correction for {meta['n_picker_rules']} tests (p &lt; {meta['bonferroni_alpha']:.4f}); source: web =
tip found online, user = your idea, own = my hypothesis, knowledge = small fact list, mined = derived from the
answers themselves.</p>
{table(["rule", "source", "support", "hits", "precision", "95% CI", "net gain", "verdict"],
       ["38%", "8%", "8%", "7%", "9%", "11%", "8%", "11%"], rows, numeric_cols={2, 3, 4, 5, 6})}""")

    # ---------------------------------------------------------------- option features
    fs = [f for f in r["option_features"] if f["options"] >= 8]
    fig = hbar([f["label"] for f in fs], [f["p_correct"] for f in fs],
               [f"{f['p_correct']:.0%}  ({f['correct']}/{f['options']})" for f in fs],
               [BLUE if f["p_correct"] > 0.3 else RED if f["p_correct"] < 0.2 else GREY for f in fs],
               "P(option is correct | option has this feature)", "share correct", baseline=0.25, x_max=0.8)
    sections.append(f"<h2>Which options to trust and which to cross out</h2>{fig_html(fig, 760)}"
                    "<p class='note'>Every option of every question counts once; a random option is correct 25% "
                    "of the time. Red bars are crossing-out signals.</p>")

    # ---------------------------------------------------------------- numeric + positions
    fig = go.Figure(go.Bar(x=["lowest", "2nd lowest", "2nd highest", "highest"], y=nr, text=nr,
                           textposition="outside", marker_color=[RED, ORANGE, BLUE, ORANGE], cliponaxis=False))
    fig.update_layout(title=dict(text=f"Numeric questions (n={r['numeric']['n']}): rank of the right answer"),
                      yaxis=dict(title="questions", range=[0, max(nr) * 1.25]))
    pc = r["position_counts"]
    fig2 = go.Figure(go.Bar(x=list("ABCD"), y=[pc[p] for p in "ABCD"], text=[pc[p] for p in "ABCD"],
                            textposition="outside", marker_color=[GREY, BLUE, GREY, GREY], cliponaxis=False))
    fig2.add_hline(y=310 / 4, line_dash="dash", annotation_text="expected if random (77.5)",
                   annotation_position="bottom left")
    fig2.update_layout(title=dict(text="Position of the right answer (all 310)"),
                       yaxis=dict(title="questions", range=[0, max(pc.values()) * 1.25]))
    pb = r["position_p_values"]["B"]["more"]
    # stacked, not side by side: in a two-column grid plotly sized the first chart wider than its column
    sections.append(f"""<h2>Numbers and positions</h2>{fig_html(fig, 360)}{fig_html(fig2, 360)}
<p class="note">Position B: {pc['B']} of 310 (one-sided binomial p = {pb:.3f}; not significant once you correct for
testing all four positions and the other rules). Whether position habits carry over to the paper exam depends on
the printed option order - next section.</p>""")

    # ---------------------------------------------------------------- option order on real sheets
    srows = [[s["file"], f"{s['bundesland']} (Prüfungsnr. {s['pruefungsnr']})", str(s["questions"]),
              str(s["informative_matched"]), str(s["same_order"]), str(s["different_order"]),
              str(s["ambiguous"] + s["unmatched"])] for s in sheet_order["sheets"]]
    sf = r["shuffled_fallback"]
    m_keep = mem["decision list (in-sample)"]["memorize_for"]["0.95"]
    m_shuf = mem["decision list, options shuffled"]["memorize_for"]["0.95"]
    sections.append(f"""
<h2>Does the real exam keep the option order?</h2>
<p>Every rule above except the final "default to {pref[0]}" step looks at the <i>content</i> of the options, so it
works whatever the order. Only the position fallback needs the printed sheet to list options in catalog order.
Evidence gathered on 2026-10-02:</p>
<ul>
<li><b>Both official BAMF sample sheets keep catalog order:</b> {sheet_order['total_same_order']} of
{sheet_order['total_informative_matched']} questions that could be matched to the current catalog. If BAMF shuffled
options, each question would keep the order with probability 1/24; all of them doing so by chance is about
10^{sheet_order['log10_p_all_same_if_shuffled']:.0f}. The 2008 sheet still matching the 2025 catalog also means the
catalog order itself has been stable for 17 years.</li>
<li><b>But the real sheets are secret.</b> EinbTestV § 1 (2): "Die aus dem Fragenkatalog in Anlage 1 erstellten
100 Fragebögen enthalten 33 Fragen ... Die Fragebögen werden nicht veröffentlicht." Neither the regulation nor
the BAMF Prüfungsordnung says anything about the order of the answer options, and sample sheets could be
hand-made.</li>
<li>The one claim of "answers sorted differently on each run" found online comes from the App Store description of a
third-party practice app, not about the exam. No test-taker report on Reddit or in German forums mentions the
option order either way.</li>
</ul>
{table(["sheet", "state", "questions", "checkable", "same order", "different order", "not matched"],
       ["30%", "22%", "9%", "10%", "10%", "10%", "9%"], srows, numeric_cols={2, 3, 4, 5, 6})}
<p><b>What it costs if they do shuffle:</b> the rules still need only {m_shuf} memorized answers for a 95% pass chance
(vs {mem['blind guessing']['memorize_for']['0.95']} without rules); the position fallback is worth another
{m_shuf - m_keep} (down to {m_keep}) only if the order is kept. Crossing out options barely helps a blind guess
({pct(sf['mean_p_guess_after_cross_out'], 1)} vs 25% on the {sf['questions']} fallback questions), so it is left out
of the shuffled scenario.</p>
<p class="note">"Checkable" excludes questions whose options are only picture labels or that match several catalog
questions with identical options; "not matched" are 2008/2021 questions that have since been reworded or removed.
Raw data: <code>results/sheet_order_check.json</code> from <code>scripts/check_sheet_order.py</code>.</p>""")

    # ---------------------------------------------------------------- word rules
    def word_rows(direction):
        return [[w["word"], f"{w['correct']}/{w['options']}", pct(w["p_correct"]), f"{w['folds_qualified']}/5",
                 f"{w['heldout_correct']}/{w['heldout_options']}"]
                for w in words["rules"] if w["direction"] == direction]
    hs = words["heldout_summary"]
    sections.append(f"""
<h2>Single words that give the answer away</h2>
<p>An option containing the word is right this often. "Folds" = in how many of the 5 training splits the word
would have been picked up; "held out" = how those words then did on the questions left out. Negative words held
up perfectly ({hs['negative']['heldout_options']} held-out options, {pct(hs['negative']['heldout_p_correct'])}
correct); positive words were right {pct(hs['positive']['heldout_p_correct'])} of the time on held-out options
(vs 25% for a random option).</p>
<div class="two"><div><h3>Cross out</h3>{table(["word", "correct", "share", "folds", "held out"],
                                                 ["34%", "17%", "15%", "15%", "19%"], word_rows("negative"),
                                                 numeric_cols={1, 2, 3, 4})}</div>
<div><h3>Trust</h3>{table(["word", "correct", "share", "folds", "held out"], ["34%", "17%", "15%", "15%", "19%"],
                         word_rows("positive"), numeric_cols={1, 2, 3, 4})}</div></div>""")

    # ---------------------------------------------------------------- conditional rules
    crow = [[f"question has '{c['trigger']}'", c["selector"], f"{c['hits']}/{c['fired']}", pct(c["precision"]),
             f"{c['p_better']:.4f}", f"{c['folds_qualified']}/5"] for c in cond["rules"][:20]]
    sections.append(f"""
<h2>"If the question contains X, then Y" rules</h2>
<p>Tested {cond['n_tests']} combinations of a question word with an answer selector (longest, shortest, a
position, ...). {len(cond['rules'])} reach {pct(cond['min_precision'])} or more on at least
{cond['min_questions']} questions, but <b>none survives the multiple-testing correction</b> (needs p &lt; {cond['bonferroni_alpha']:.6f}),
and rules mined the same way on training splits were right only {pct(cond['heldout_precision'])} of the time on the
held-out questions ({cond['heldout_hits']}/{cond['heldout_fired']}). With 1,456 tries, a few 4-out-of-5 rules are
expected by pure chance. Top 20 for curiosity:</p>
{table(["trigger", "then pick", "hits", "precision", "p (uncorrected)", "folds"],
       ["30%", "20%", "11%", "12%", "15%", "12%"], crow, numeric_cols={2, 3, 4, 5})}""")

    # ---------------------------------------------------------------- CV
    models = [("hand-made features", cv["hand_features"]), ("words", cv["words"]),
              ("words + features", cv["words_and_features"])]
    fig = go.Figure()
    fig.add_bar(name="questions it learned from", x=[m[0] for m in models],
                y=[m[1]["train_accuracy"] for m in models], marker_color=ORANGE,
                text=[f"{m[1]['train_accuracy']:.0%}" for m in models], textposition="outside")
    fig.add_bar(name="held-out questions", x=[m[0] for m in models], y=[m[1]["test_accuracy"] for m in models],
                marker_color=BLUE, text=[f"{m[1]['test_accuracy']:.0%}" for m in models], textposition="outside")
    fig.add_hline(y=0.25, line_dash="dash", annotation_text="blind guess 25%", annotation_position="bottom left")
    fig.update_layout(title=dict(text="Learned pattern models: memorized vs real signal (5-fold CV)"),
                      yaxis=dict(tickformat=".0%", range=[0, 0.7]), barmode="group")
    sections.append(f"<h2>How much of it is real?</h2>{fig_html(fig, 400)}"
                    "<p class='note'>A naive-Bayes scorer over option features and/or words. The gap between the "
                    "orange and blue bars is memorization; the blue bar above 25% is the real, transferable "
                    "signal.</p>")

    # ---------------------------------------------------------------- exam
    names = list(exam)
    fig = hbar(names, [exam[n]["p_pass"] for n in names],
               [f"{exam[n]['p_pass']:.1%}  (exp. {exam[n]['expected_score']:.1f}/33)" for n in names],
               [GREY if n == "blind guessing" else BLUE if "cross" in n else ORANGE for n in names],
               "Chance to pass (17 of 33) without memorizing anything", "P(pass)", x_max=0.3)
    xs = list(range(311))
    fig2 = go.Figure()
    for name, color in [("blind guessing", GREY), ("always B", ORANGE), ("decision list, options shuffled", RED),
                        ("decision list (in-sample)", BLUE)]:
        c = mem[name]
        label = {"blind guessing": "memorize, guess the rest",
                 "always B": "memorize, answer B for the rest (catalog order kept)",
                 "decision list, options shuffled": "memorize, rules for the rest, IF options are shuffled",
                 "decision list (in-sample)": "memorize, rules for the rest (catalog order kept)"}[name]
        textpos = {"blind guessing": "bottom right", "always B": "top left",
                   "decision list, options shuffled": "bottom right", "decision list (in-sample)": "top left"}[name]
        fig2.add_scatter(x=xs, y=c["p_pass_by_memorized"], mode="lines", name=label, line=dict(color=color, width=3))
        fig2.add_scatter(x=[c["memorize_for"]["0.95"]], y=[c["p_pass_by_memorized"][c["memorize_for"]["0.95"]]],
                         mode="markers+text", text=[f"{c['memorize_for']['0.95']}"], textposition=textpos,
                         textfont=dict(color=color, size=14), marker=dict(color=color, size=10), showlegend=False)
    fig2.add_hline(y=0.95, line_dash="dash", annotation_text="95%")
    fig2.update_layout(title=dict(text="Pass probability vs. number of answers memorized"),
                       xaxis=dict(title="answers memorized (best order: Bayern first, then where the strategy fails)"),
                       yaxis=dict(title="P(pass)", tickformat=".0%"), legend=dict(orientation="h", y=-0.25))
    targets = meta["pass_targets"]
    curve_labels = [("blind guessing", "no rules, guess the rest"),
                    ("decision list, options shuffled", "rules, IF the exam shuffles the options"),
                    ("always B", "answer B for the rest (order kept)"),
                    ("decision list (in-sample)", "rules + default B (order kept)")]
    tgt_rows = [[label, str(mem[k]["memorize_for_expected_pass_mark"]),
                 *[str(mem[k]["memorize_for"][str(t)]) for t in targets]] for k, label in curve_labels]
    tgt_table = table(["strategy for the questions you did not memorize", "avg. 17/33",
                       *[f"{t:.0%} pass" for t in targets]],
                      ["31%", "9%"] + ["8.5%"] * len(targets), tgt_rows,
                      numeric_cols=set(range(1, len(targets) + 2)))
    sections.append(f"""<h2>What it means for the exam</h2>{fig_html(fig, 420)}{fig_html(fig2, 480)}
<h3>How many answers to memorize for a given pass chance</h3>
{tgt_table}
<p class="note">"avg. 17/33" = the point where your expected score reaches the pass mark (a 'minimal pass' on
average); the 50% column is the coin-flip point and comes slightly earlier because the score only needs to reach
17. Going from 50% to 90% costs 6-16 extra answers per 10 points; going from 95% to 99% alone costs 16-23. The
shuffled-options rules sit exactly {mem['blind guessing']['memorize_for']['0.5'] - mem['decision list, options shuffled']['memorize_for']['0.5']}
answers below "no rules" at every level: that is the number of questions the content rules answer correctly, i.e.
answers you get for free (the questions the rules get wrong you have to memorize anyway).</p>
<p class="note">Exact calculation (not simulation): 30 of the 300 general and 3 of the 10 Bayern questions are drawn,
17 correct pass. Cross-checked against a 20,000-draw simulation (0.0071 vs 0.0069). A Bayern question is 3x as likely
to be on your sheet as a general one (3/10 vs 30/300), so the memorizing order puts the 10 Bayern questions first.
Orange "in-sample" strategies use rules fitted on all 310 questions - fine here, because the exam uses exactly
these questions; blue ones are scored on questions they did not see.</p>""")

    # ---------------------------------------------------------------- study list
    order = mem["decision list (in-sample)"]["order"]
    dlq = {row["id"]: row for row in dl["questions"]}
    must = [i for i in order if not dlq[i]["hit"]]
    free = [i for i in order if dlq[i]["hit"]]
    rows_must = [[str(i), qmap[i]["section"], qmap[i]["question"], dlq[i]["picked"], qmap[i]["answer"]] for i in must]
    rows_free = [[str(i), qmap[i]["section"], qmap[i]["question"], dlq[i]["rule"], qmap[i]["answer"]] for i in free]
    sections.append(f"""
<h2>Your study list</h2>
<p>The rules get {len(free)} questions right and {len(must)} wrong. Memorize the wrong ones, in this order
(Bayern first); the curve above shows how far each step takes you.</p>
<details><summary>{len(must)} questions to memorize (rules would get these wrong)</summary>
{table(["#", "part", "question", "rules would pick", "correct answer"], ["6%", "8%", "46%", "20%", "20%"], rows_must)}
</details>
<details><summary>{len(free)} questions the rules already get right</summary>
{table(["#", "part", "question", "rule used", "correct answer"], ["6%", "8%", "46%", "20%", "20%"], rows_free)}
</details>""")

    # ---------------------------------------------------------------- method
    sections.append(f"""
<h2>Method and caveats</h2>
<ul>
<li>Data: the 310 Bayern questions with official answers (<code>data/questions_bayern.json</code>). Raw results:
<code>results/patterns.json</code>, generated {esc(meta['generated'])} by <code>scripts/mine_patterns.py</code>.</li>
<li>Your test is drawn from exactly these 310 questions, so a rule only has to work on them. In-sample numbers are
what you would get on the exam if you apply the rules exactly. Cross-validated numbers (5 folds, seed {meta['seed']})
tell you whether a pattern is a real property of how BAMF writes questions or just luck in this pool.</li>
<li>{meta['n_picker_rules']} picker rules, {cond['n_tests']} conditional rules and every word with at least
{meta['min_word_support']} occurrences were tested, so some good-looking numbers are expected by chance. The
verdicts use Bonferroni correction; small-support rules (5 questions) are flagged by their wide CIs.</li>
<li>Knowledge rules (DDR states, neighbour countries) and mined rules (key numbers, word lists) are really facts
in compressed form - legitimate memory aids, not test-taking tricks.</li>
<li>Sources for the "popular tricks": web searches for Einbürgerungstest tips (eliminate absurd answers, longest
answer, chancellor mnemonics). Online guides consistently advise studying over tricks; the national pass rate
is about 96-98%.</li>
</ul>""")

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Einbürgerungstest answer patterns</title>
<style>
body {{ font-family: "Segoe UI", Arial, sans-serif; max-width: 1100px; margin: 0 auto; padding: 16px 20px 60px;
       color: #1f2328; background: #fff; line-height: 1.5; }}
h1 {{ margin-bottom: 0; }} h2 {{ margin-top: 2.2em; border-bottom: 2px solid #eee; padding-bottom: 4px; }}
.sub, .note {{ color: #57606a; font-size: 0.92em; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px 14px; }}
.card .big {{ font-size: 2em; font-weight: 700; color: {BLUE}; }}
.card .lbl {{ font-weight: 600; }}
.two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; }}
table {{ table-layout: fixed; width: 100%; border-collapse: collapse; font-size: 0.9em; margin: 8px 0 16px; }}
th, td {{ border-bottom: 1px solid #e5e5e5; padding: 4px 6px; text-align: left; vertical-align: top;
          overflow-wrap: anywhere; }}
th {{ background: #f6f8fa; }} .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
details {{ margin: 10px 0; }} summary {{ cursor: pointer; font-weight: 600; }}
code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
</style></head><body>
<h1>Einbürgerungstest: are there answer patterns?</h1>
<p class="sub">310 Bayern questions (300 general + 10 Bayern), official answers. Generated {esc(meta['generated'])}.</p>
{''.join(sections)}
</body></html>"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    log.info(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB) in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
