# WebFetch summaries of official pages introduced errors - recheck facts verbatim

A review pass that re-read the official pages verbatim with Playwright found 4 errors in the README,
all from trusting a summarizer or a third-party copy instead of the source:

| README said | Source actually says | Origin of the error |
|---|---|---|
| Test exemption: "mittlerer Schulabschluss or higher" | "einen erfolgreichen Mittelschulabschluss oder einen vergleichbaren oder höheren Schulabschluss" (Mittelschule = lower secondary, a lower bar) | WebFetch said "Middle school diploma", I translated it wrong |
| 18+ months "plus 4-6 months for security checks" | security checks "die momentan vier bis sechs Monate in Anspruch nehmen" are one of the *reasons* for the 18+ months | WebFetch summary ("Security checks add 4-6 months") |
| MVHS sends exact time by post | page says "per E-Mail" in the title and "mit der Post" in the body | WebFetch picked one |
| 119 test centers in Bayern | official xlsx: 116 | count taken from the third-party leben-in-deutschland JSON |

Rule going forward: for fees, dates, deadlines, legal requirements, grab the exact sentence from the
page (Playwright `document.body.textContent` + regex) before writing it down. WebFetch is fine for
finding where things are, not for the wording.
