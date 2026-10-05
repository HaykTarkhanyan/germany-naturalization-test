# Russian explainer videos - plan

Status 2026-10-05: plan and six pilot scripts written. Nothing is installed or rendered yet; the technology
choices below are open for Hayk to make (see "Decisions needed").

Contents: [Goal](#goal) · [Format](#format) · [Which topics first](#which-topics-first) ·
[Scripts](#scripts) · [Pipeline](#pipeline) · [Decisions needed](#decisions-needed) · [Cost](#cost) ·
[Compute](#compute) · [Milestones](#milestones) · [Risks](#risks)

## Goal

Short videos in Russian that teach the facts worth memorizing, topic by topic, so studying can happen by
watching (commute, phone) instead of reading. Same rule as the lessons: minimal time. A video covers only the
**memorize** questions of its topic (data/lessons.json, DECISIONS.md #13); common-sense questions get one line
in the recap at most.

## Format

- **Length:** about 1.5-2 minutes: 190-260 spoken words (1:20-1:50 at an assumed 140 words per minute for
  Russian TTS, to be measured in the pilot) plus short holds on the exam pictures. Short on purpose.
- **Narration:** Russian. German exam terms are spoken and shown in German (Bundestag, Landtag, Fraktion), because
  the exam sheet is German; the Russian narration explains them.
- **On screen:** a big German term card per fact (the exact wording that is on the exam sheet), the Russian
  meaning under it, and burned-in Russian subtitles.
- **Visuals per scene, in this order of preference:**
  1. the exam's own picture when the question has one (data/images: ballot, maps, coats of arms);
  2. real photos of the thing itself (Wikimedia Commons: Reichstag, Maximilianeum, Berlin Wall 1961/1989,
     Adenauer, Kohl, Berlin airlift);
  3. stock video B-roll (Pexels): Munich, Berlin, ballot boxes, flags;
  4. a generated text card (the fallback that always works).
- **End card:** the 4-6 German answers of the video in one list, and "Learn -> <topic>" in the app.

## Which topics first

Ranked by exam points that need memorizing (expected exam questions from the topic's memorize questions,
computed from data/lessons.json). The six pilot topics carry 7.7 of the 18.2 memorize points of the whole
catalog (42%):

| # | Lesson | Memorize questions | Memorize points | Why a video helps |
|---|---|---|---|---|
| 01 | bayern | 7 | 2.1 | Bayern questions are 3x as likely; picture questions (coat of arms, map) |
| 02 | mauer_einheit | 12 | 1.2 | Story with real footage; the five eastern states need a mnemonic |
| 03 | nachkriegszeit | 12 | 1.2 | Airlift and zones are visual; dates and names to anchor |
| 04 | wahlen_praxis | 11 | 1.1 | The ballot picture question; 5% and 4 years |
| 05 | regierung_praesident | 11 | 1.1 | Who elects whom: easy to mix up, easy to show |
| 06 | parlament | 10 | 1.0 | Bundestag vs Bundesrat, Fraktion, Abgeordnete |

Next in line if the pilot works: europa (0.9), nationalsozialismus, gerichte_recht, familie (0.8 each).

## Scripts

`videos/scripts/NN_<lesson>.md`, one per video, Markdown so they are easy to read and edit, with a fixed shape
so the pipeline can parse them:

```
## <n>. <scene title> (~<seconds> s)
- **Voice:** <Russian narration>
- **On screen:** <German term card> | <Russian meaning>
- **Visual:** exam:<image> | commons:"<search>" | pexels:"<search>" | card
- **Questions:** <ids>
```

Rules: facts come only from data/lessons.json (already fact-checked twice, see `_learnings/`), plain hyphens
instead of dashes, German terms in Latin letters in the narration (the TTS decides in the pilot whether they
need a Cyrillic pronunciation hint, kept in one `videos/pronunciation.json` if so). Every script lists the
questions it covers; a check in the pipeline will compare that list with the lesson's memorize questions.

## Pipeline

All local, scripted, rerunnable; outputs in `videos/build/` (gitignored: audio, downloaded media, renders).

1. **Parse** a script into scenes.
2. **Voice:** TTS per scene -> one audio file per scene + its duration (word timings if the engine gives them,
   for subtitles).
3. **Media:** fetch each scene's visual (exam image from data/images, Commons by search, Pexels by search), cache
   it with its source URL in `videos/build/media/sources.json` so a rebuild needs no new downloads.
4. **Cards:** render the German term cards and subtitles.
5. **Compose:** per scene, visual (video clip trimmed to the narration, or a photo with a slow zoom) + card +
   narration; concatenate; mux subtitles.
6. **Output:** MP4 + .srt per video, plus `videos/build/<NN>.json` with what went in (voice, media, durations).

## Decisions needed

### D1. Voice (TTS) - the big one

Prices checked 2026-10-05 on the official pricing pages (ElevenLabs, Azure) or the vendor's per-minute figure
(OpenAI).

| Option | Russian quality | German terms in Russian text | Cost for the 6 pilot videos (9.7k narration characters, measured; ~20k with every scene voiced twice) |
|---|---|---|---|
| **ElevenLabs** (Multilingual v2 / v3) | Most natural and expressive | Multilingual model can switch language inside one text; to test | Free plan 10k credits/month covers all 6 once, without retakes; Starter $6/month for 30k (first month $1 until Oct 18) |
| **Azure Speech** (ru-RU neural voices: Dmitry, Svetlana, Dariya) | Very good, a bit "newsreader" | SSML lets me fix pronunciation and stress word by word | 0.5M characters free per month, then $15 per 1M: effectively $0 |
| **OpenAI gpt-4o-mini-tts** | Good, sometimes an English-ish accent in Russian | Reads Latin German words, quality unknown | about $0.015 per minute: ~$0.30 for ~20 minutes of audio |
| **Silero v5 (local, no key)** | Good Russian, made for Russian, automatic stress | Latin words need a Cyrillic hint | $0, runs on the CPU in seconds |

**My pick: ElevenLabs** for the series, because engagement matters for videos you are supposed to actually watch,
and it is the most likely to pronounce German terms well inside Russian sentences. The pilot step makes this
cheap to check: the same 2 scenes rendered with ElevenLabs (free plan) and Silero (free, local) side by side,
you choose by ear. **What would flip it:** if Azure or Silero sound close enough, take them (free, and SSML gives
Azure exact control over German words); if ElevenLabs mangles German terms, Azure.
**Hard to reverse:** the voice. Switching later means re-voicing every video, so pick it on the pilot.

### D2. Video assembly

| Option | Pros | Cons |
|---|---|---|
| **Python + ffmpeg** (ffmpeg 5.1.2 is already installed; cards drawn with Pillow) | No new framework, fast renders, deterministic, fits the repo's Python tooling (uv) | Animations are basic (fades, slow zoom, slide-in cards) |
| **Remotion** (React to video; free license for individuals) | Same React/TypeScript as the app, polished animated cards and maps | Heavier: renders with headless Chrome (more CPU, slower), more setup |
| **MoviePy 2.2** (Python wrapper around ffmpeg; maintained, last release Feb 2026) | Simpler compositing code than raw ffmpeg | Slower renders; v2 broke the v1 API, so most examples online are outdated |

**My pick: Python + ffmpeg** for the pilot: fastest to a first watchable video and light on the laptop.
**What would flip it:** if the pilot looks too plain, Remotion is the upgrade (the scripts stay the same, only
the renderer changes, so this is easy to reverse).

### D3. Shape

16:9 landscape (PC and YouTube; on a phone you rotate) or 9:16 portrait (phone first, like Shorts).
**My pick: 16:9**, because the exam pictures (maps, ballots) are landscape. Easy to reverse per video (re-render).

### D4. Where the videos live

- local MP4 files only (simplest; you copy them to the phone),
- YouTube unlisted + a "Watch (2 min)" link in each lesson of the app,
- GitHub Release assets of this repo (public download links, nothing in git history).

Not in the repo itself: 6 videos at 1080p are roughly 100-200 MB (guess), and GitHub Pages deploys the repo.
**My pick: local first**, decide on sharing after the pilot.

### D5. Keys I need

- the TTS key for the option you pick (none for Silero);
- a Pexels API key (free; or say "no stock video" and I use Commons photos + cards only).
  Wikimedia Commons needs no key.

## Cost

Whole pilot (6 videos, every scene voiced twice): **$0-6** depending on D1 (free tiers cover it except
ElevenLabs beyond 10k characters a month). Media: $0 (Pexels and Commons are free). I will show the estimate again
before the first paid call and report actual spend afterwards (cost ledger in `videos/build/costs.json`).

## Compute

Rendering a 2 minute 1080p video with ffmpeg uses all CPU cores for roughly 1-3 minutes (guess, to be
measured on the first render). Per the house rules I will ask before the first render and render one video at
a time, in the background, with a 720p preview first.

## Milestones

1. **Voice test** (after D1 keys): 2 scenes of 01_bayern in the candidate voices, side by side. ~15 min work.
2. **Pilot video 01_bayern** end to end; measure render time and file size; Hayk watches and gives notes.
3. **Batch 02-06** with the pilot's fixes, one at a time.
4. Optional: links from the app's lessons (if D4 = YouTube or Release assets).

## Risks

- **German terms mispronounced or wrong stress** in Russian TTS: test in milestone 1; fallback is a Cyrillic hint
  per term in `videos/pronunciation.json`, or Azure SSML.
- **Generic stock footage** (a random Berlin street for "Bundesrat"): prefer the exam picture and Commons photos
  of the real building/person; stock only as background.
- **Accuracy:** the narration restates data/lessons.json only; no new claims. Facts that can change (chancellor,
  president, EU members) are dated in the script.
- **A fact that is right but primes a wrong option** (learned in the lesson review, `_learnings/2026-10-05-1545_*`):
  every script also says which believable wrong option to avoid.
