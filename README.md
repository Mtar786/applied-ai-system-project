# VibeFinder — AI-Powered Music Recommender

## Video Walkthrough

[![VibeFinder Demo](https://img.shields.io/badge/Loom-Watch%20Demo-blue?logo=loom)](YOUR_LOOM_LINK_HERE)

> **[Watch the end-to-end demo on Loom](YOUR_LOOM_LINK_HERE)**
> Covers: RAG pipeline, guardrail conflict detection, reliability evaluation suite, and consistency check.

---

## Portfolio

**GitHub:** https://github.com/Mtar786/applied-ai-system-project

**What this project says about me as an AI engineer:**
VibeFinder reflects how I approach AI development: build something transparent first, then make it smarter responsibly. I started with a simple weighted scorer where every decision was visible and explainable, then layered Claude on top only after the retrieval logic was solid and tested. Adding guardrails before the model call — not after — shows that I think about failure modes during design, not as an afterthought. The reliability evaluator exists because I wanted to make a concrete, repeatable claim about the system's behavior rather than just asserting it worked. I am most interested in AI systems where the reasoning is auditable, the limitations are documented, and a human reviewer can understand exactly why a given output was produced. VibeFinder is a small system, but it was built with that standard in mind.

> A content-based music recommender extended with Retrieval-Augmented Generation (RAG),
> input guardrails, and an automated reliability evaluation suite.

---

## Original Project

This system is built on top of the **Music Recommender Simulation** from Module 3
(CodePath AI110). The original project implemented a pure content-based recommender
in Python: it loaded a CSV catalog of 20 songs, scored each song against a user
taste profile using weighted rules (genre match = +3.0, mood match = +2.0, energy
proximity = 0–2.0), and returned a ranked list of top-k recommendations. While
functional, the original system had no natural-language explanations, no way to
detect bad inputs, and no way to verify that its outputs were reliable or consistent.

This capstone extends that foundation into a complete applied AI system.

---

## What This Project Does and Why It Matters

VibeFinder takes a user's music preferences (genre, mood, energy level, acoustic
preference) and returns a curated playlist — complete with a plain-English narrative
and per-song justifications. It matters because it demonstrates the full lifecycle
of a responsible AI feature: structured retrieval, language model generation,
input validation, and automated reliability testing. Every design decision is
visible and explainable, which is increasingly expected in production AI systems.

---

## System Architecture

```
+---------------------------+
|  User Input               |
|  genre, mood, energy,     |
|  likes_acoustic           |
+---------------------------+
            |
            v
+---------------------------+     invalid or missing field?
|  Guardrails               | --> reject with error message
|  guardrails.py            |
|                           |     conflicting prefs?
|                           | --> warn user, still proceed
+---------------------------+
            |
            v
+---------------------------+
|  Retriever                |
|  recommender.py           |
|  score_song() x 20 songs  |
|  returns top-10 candidates|
+---------------------------+
            |
            v
+---------------------------+
|  Generator (Claude API)   |
|  rag_engine.py            |
|  curates top-5, writes    |
|  playlist narrative +     |
|  per-song explanations    |
|                           |
|  [fallback if no API key] |
|  returns scorer output    |
+---------------------------+
            |
            v
+---------------------------+
|  Output                   |
|  ranked playlist with     |
|  vibe summary and reasons |
+---------------------------+
            |
            v
+---------------------------+
|  Evaluator (optional)     |
|  evaluator.py             |
|  runs 5 test profiles,    |
|  consistency check,       |
|  writes JSON report to    |
|  logs/                    |
+---------------------------+
```

**Data flows left to right through the pipeline.** The guardrail layer runs first
so invalid inputs never reach the expensive steps. The retriever handles structured
ranking; Claude handles natural-language curation. The evaluator sits outside the
main pipeline and runs on demand to verify system health.

---

## Project Structure

```
applied-ai-system-project/
├── src/
│   ├── recommender.py       # Core: Song, UserProfile, load_songs, score_song, recommend_songs
│   ├── guardrails.py        # Input validation and conflict detection
│   ├── rag_engine.py        # RAG pipeline: retrieve -> augment -> generate
│   ├── evaluator.py         # Reliability test suite, consistency checker, report writer
│   └── main.py              # CLI entry point with three modes
├── data/
│   └── songs.csv            # 20 songs across 14 genres and 10 moods
├── tests/
│   └── test_recommender.py  # 9 automated tests covering all modules
├── logs/                    # Auto-created; stores vibefinder.log and JSON reports
├── assets/                  # System diagrams and screenshots
├── model_card.md            # Full model card: bias analysis, evaluation, reflection
├── requirements.txt
└── .env.example
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Mtar786/applied-ai-system-project.git
cd applied-ai-system-project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Add your Anthropic API key

Without a key, the system runs in **retriever-only fallback mode**. All CLI modes
work, but the Claude curation step is skipped and the playlist narrative will note
that the API is unavailable.

```bash
cp .env.example .env
# Open .env and set:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Verify the setup

```bash
pytest
# Expected: 9 passed
```

---

## Usage

### Mode 1 — Get a recommendation

```bash
python -m src.main recommend                    # pop profile (default)
python -m src.main recommend --profile lofi
python -m src.main recommend --profile rock
python -m src.main recommend --profile edge     # adversarial / conflicting prefs
```

### Mode 2 — Run the reliability evaluation suite

```bash
python -m src.main evaluate
```

### Mode 3 — Check recommendation stability

```bash
python -m src.main consistency                  # pop (default)
python -m src.main consistency --profile lofi
```

---

## Sample Interactions

### Example 1 — Chill Lofi profile (retriever-only fallback)

**Input:**
```
genre=lofi  mood=chill  energy=0.38  likes_acoustic=True
```

**Output:**
```
============================================================
  VibeFinder -- lofi / chill / energy=0.38
============================================================

  Playlist vibe:
  Recommendations generated by scoring algorithm only
  (no API key configured -- Claude curation unavailable).

  #1  Library Rain -- Paper Lanterns
       Score : 7.8
       Why   : genre match (+3.0); mood match (+2.0); energy proximity (+1.94); acoustic bonus (+0.86)

  #2  Midnight Coding -- LoRoom
       Score : 7.63
       Why   : genre match (+3.0); mood match (+2.0); energy proximity (+1.92); acoustic bonus (+0.71)

  #3  Focus Flow -- LoRoom
       Score : 5.74
       Why   : genre match (+3.0); energy proximity (+1.96); acoustic bonus (+0.78)

  #4  Spacewalk Thoughts -- Orbit Bloom
       Score : 4.72
       Why   : mood match (+2.0); energy proximity (+1.80); acoustic bonus (+0.92)

  #5  Coffee Shop Stories -- Slow Stereo
       Score : 2.87
       Why   : energy proximity (+1.98); acoustic bonus (+0.89)
```

**Why this makes sense:** Library Rain and Midnight Coding are both lofi + chill
with low energy, matching all three primary signals. Focus Flow hits genre and
energy but not mood. Spacewalk Thoughts earns mood and acoustic points despite
being ambient, not lofi — it leaked in because the catalog is small.

---

### Example 2 — Edge case with conflicting preferences

**Input:**
```
genre=ambient  mood=peaceful  energy=0.95  likes_acoustic=False
```

**Output:**
```
  [!] mood 'peaceful' is typically low-energy but target_energy=0.95 is high
      -- results may be incoherent
  [!] genre 'ambient' is inherently low-energy but target_energy=0.95 is very high
      -- few matches will exist

  Running RAG pipeline for profile: ambient / peaceful / energy=0.95

  #1  Soft Thunder -- Cloudbreak
       Score : 3.76
       Why   : genre match (+3.0); energy proximity (+0.76)

  #2  Spacewalk Thoughts -- Orbit Bloom
       Score : 3.66
       Why   : genre match (+3.0); energy proximity (+0.66)
```

**What this demonstrates:** The guardrail layer detected that ambient + energy=0.95
is contradictory and surfaced two warnings before running. The recommender still
ran (warnings are non-blocking), but the low scores (3.76 vs. a max of 8.0)
confirm that the preferences were self-defeating. A future version would prompt
the user to clarify rather than proceeding silently.

---

### Example 3 — Reliability evaluation suite

**Input:**
```bash
python -m src.main evaluate
```

**Output:**
```
============================================================
  Evaluation Results  (5/5 passed)
============================================================

  [PASS]  High-Energy Pop
          top: Sunrise City (score 6.94)

  [PASS]  Chill Lofi
          top: Library Rain (score 7.8)

  [PASS]  Deep Intense Rock
          top: Storm Runner (score 6.98)

  [PASS]  Jazz Relaxed
          top: Sunday Brunch (score 7.87)

  [PASS]  Edge Case -- Conflicting [conflicts detected]
          top: Soft Thunder (score 3.76)
          [!] mood 'peaceful' is typically low-energy but target_energy=0.95 is high
          [!] genre 'ambient' is inherently low-energy but target_energy=0.95 is very high

  Consistency check (pop profile, 3 runs): STABLE [OK]
  Full report saved to: logs/evaluation_20260425_224820.json
```

**What this demonstrates:** All five profiles returned the expected top song for
their genre, and the consistency check confirmed identical output across three
runs — as expected for a deterministic scorer.

---

## Design Decisions and Trade-offs

**Why RAG instead of sending all songs directly to Claude?**
The retrieval step does meaningful work before Claude is ever involved. By scoring
all 20 songs and passing only the top 10, the model receives a focused, ranked
shortlist instead of an unordered dump. This mirrors production RAG systems where
a dense retriever pre-filters a large corpus before generation. It also makes the
system work at any catalog size — swapping in 10,000 songs would not require
changing the Claude prompt.

**Why keep the weighted scorer at all?**
The scorer is fully transparent: every score is explained in plain English
(genre match +3.0, energy proximity +1.94). This interpretability is lost if you
hand raw preferences to Claude and ask it to decide. The hybrid approach gets
quantitative ranking from the scorer and natural-language explanation from Claude.

**Why are guardrails non-blocking (warnings, not hard errors) for conflicting prefs?**
Rejecting the request entirely would frustrate users whose preferences are unusual
but valid (for example, someone who genuinely wants to explore high-energy ambient).
Warnings surface the problem without removing user agency. Hard errors are reserved
for structurally invalid inputs (missing fields, energy outside 0–1).

**Trade-off: exact string matching for genre and mood**
The simplest implementation. The cost is brittleness: "indie pop" scores zero genre
match when the user wants "pop." A production system would use embeddings or a
genre similarity graph. The trade-off was chosen deliberately to keep the scorer
transparent and free of additional dependencies.

---

## Testing Summary

**What was tested:**

| Test | Result |
|------|--------|
| Recommender sorts songs by score correctly | Pass |
| Explanation is a non-empty string | Pass |
| Valid profile passes guardrail validation | Pass |
| Profile missing required field is rejected | Pass |
| Energy outside 0–1 is rejected | Pass |
| Conflicting prefs (peaceful + high energy) are flagged | Pass |
| Valid profile generates no conflicts | Pass |
| Evaluation suite runs and returns results for all profiles | Pass |
| Consistency check confirms identical output across 3 runs | Pass |

**9 / 9 tests pass.**

**What worked well:**
The evaluator was the most useful addition. Running five profiles automatically
and checking each against an expected outcome caught a bug early: the Jazz Relaxed
profile was initially returning a pop song at the top because the genre weight
was overwhelming the energy proximity score. Adjusting the catalog (adding a second
jazz track — Sunday Brunch) fixed it without changing the algorithm.

**What did not work as expected:**
The edge-case profile (ambient + peaceful + energy=0.95) technically passes all
five tests because the test only checks that results exist, not that they are
coherent. A future test should assert that a conflicting profile's max score stays
below a threshold, signaling that no strong match was found.

**What I learned:**
A deterministic system with a structured test suite is easier to trust than one
without. The consistency check in particular made it immediately obvious that the
scorer was stable — something that would have required manual verification otherwise.

---

## Reflection

Building this system taught me that the most important decisions in an AI pipeline
are made before the model is ever called. Choosing what features to weight, what
inputs to validate, and what outputs to test shapes who the system serves well and
where it fails quietly. The Claude integration was straightforward once the retrieval
layer was solid — but getting the retrieval layer right took most of the work.

The guardrail module changed how I think about user input. In the original Module 3
recommender, contradictory preferences silently produced bad results — the code ran
fine, the output looked normal, and there was no indication anything was wrong. Adding
explicit conflict detection meant the system now communicates its own uncertainty to
the user, which is a more honest and useful design.

The reliability evaluator reinforced that trust in AI outputs comes from evidence,
not intuition. Running the same profile five times and confirming identical output is
a simple test, but it produces a concrete, repeatable claim: this system is
deterministic. That kind of claim matters in a portfolio because it demonstrates
engineering discipline, not just the ability to get something to run once.

If I extended this further, I would add soft genre matching (embeddings instead of
exact strings), a diversity pass that caps one song per artist in the final output,
and a streaming interface so users could refine their profile interactively rather
than committing to a single static query.

---

---

## Reliability and Evaluation

### Automated Tests

```bash
pytest tests/
# 9 passed in 0.17s
```

| Test | Module | Result |
|------|--------|--------|
| Recommender sorts songs by score descending | `recommender.py` | Pass |
| `explain_recommendation` returns a non-empty string | `recommender.py` | Pass |
| Valid profile passes guardrail validation | `guardrails.py` | Pass |
| Profile missing a required field is rejected | `guardrails.py` | Pass |
| Energy value outside 0–1 is rejected | `guardrails.py` | Pass |
| Peaceful mood + high energy is flagged as conflict | `guardrails.py` | Pass |
| Valid profile generates zero conflict warnings | `guardrails.py` | Pass |
| Evaluation suite runs and returns results for all 5 profiles | `evaluator.py` | Pass |
| Consistency check confirms identical output across 3 runs | `evaluator.py` | Pass |

**9 out of 9 tests passed.** The system is fully deterministic: the same input always
produces the same ranked output. The one area where results felt "off" was the
edge-case profile — the evaluator marked it PASS because a result was returned, but
a human reviewer would flag the low max score (3.76 out of 8.0) as a sign the
preferences were contradictory. A future test should assert a minimum quality
threshold, not just that output exists.

### Confidence Scoring

The scoring algorithm produces an inherent confidence signal: the raw score (max 8.0).
A song scoring above 6.0 matched genre, mood, and energy closely — high confidence.
A song scoring below 3.0 only matched energy proximity — low confidence. This signal
is already displayed in the CLI output and included in every JSON evaluation report.

### Logging and Error Handling

Every run writes to `logs/vibefinder.log` in this format:

```
2026-04-25 15:46:38  INFO   src.evaluator   [PASS] High-Energy Pop -- top: Sunrise City (6.94)
2026-04-25 15:46:38  WARNING src.guardrails  Conflicts detected: ["mood 'peaceful' is low-energy but energy=0.95"]
2026-04-25 15:47:35  INFO   src.rag_engine  Sending 10 candidates to Claude for curation
2026-04-25 15:47:35  INFO   src.rag_engine  Claude returned playlist with 5 tracks
```

The RAG engine catches both `json.JSONDecodeError` (Claude returning malformed output)
and `anthropic.APIError` (network or quota failures) and falls back to the retriever
output rather than crashing. This means the CLI never exits with an unhandled exception
during normal use.

### Human Evaluation Summary

Four profiles were tested manually and compared against personal musical intuition:

- **Chill Lofi** — results felt correct immediately. Library Rain at #1 is exactly
  what a study playlist should start with.
- **High-Energy Pop** — Sunrise City at #1 was intuitive. Gym Hero at #2 was
  accurate but repetitive if played back-to-back.
- **Deep Intense Rock** — Storm Runner was the only rock track in the catalog, so
  #1 was automatic. The #2 result (Gym Hero, a pop track) felt like a category error
  to a human listener even though the math was correct.
- **Edge Case** — results were numerically consistent but musically nonsensical, which
  is exactly what the conflict warnings are designed to communicate.

---

## Reflection and Ethics

### Limitations and Biases

**Filter bubble by design.** Genre carries the highest weight (3.0 out of 8.0 max
points). A user who says they like pop will almost always see pop songs at the top,
even if a jazz track is a better match for their mood and energy. The system
reinforces stated preferences rather than helping users discover new genres.

**Catalog underrepresentation.** Classical, country, folk, r&b, and metal each have
only one song in the dataset. Users who prefer these genres hit a hard ceiling: they
earn the genre bonus once, then fill the rest of their top-5 with unrelated songs
selected only by energy proximity. This makes the system significantly less useful
for listeners outside pop, lofi, and rock.

**Exact string matching is brittle.** The genre "indie pop" scores zero genre match
when a user wants "pop." A user who types "Chill" instead of "chill" gets no mood
match. These are silent failures — the system produces output without indicating that
the comparison failed.

**No temporal context.** The system treats every session as identical. A user who
wants energetic music at 7am and chill music at 11pm would give the same profile
both times. Real recommender systems use time-of-day, activity context, and listening
history to adapt.

### Could This AI Be Misused?

In its current form, VibeFinder is low-risk. The catalog is small and hand-authored,
and the system makes no claims about users beyond what they explicitly provide.

However, patterns in this design could cause harm if scaled:

- **Catalog bias at scale.** If a platform used this algorithm with a real catalog,
  genres with fewer tracks would be systematically under-recommended — disadvantaging
  independent artists and non-Western music regardless of listener preference.
- **Filter bubbles at scale.** High genre weight would create listeners who only ever
  hear one genre, reducing exposure to diverse music and concentrating streaming
  revenue on already-popular styles.

Mitigations: add a diversity pass that enforces genre variety in the top-5, reduce
genre weight relative to energy and mood, and audit catalog representation before
deployment.

### What Surprised Me During Testing

The consistency check result was the biggest surprise — not because it passed, but
because I expected to have to think about it. A deterministic scorer with no
randomness should always be consistent, and it was. What surprised me was how
reassuring that confirmation felt. Having a test that says "this output is stable"
turned out to be more useful than I expected, because it meant any future change
that broke consistency would be immediately detectable.

The second surprise was Gym Hero appearing in the Deep Intense Rock recommendations
at #2. Gym Hero is tagged pop/intense with energy=0.93. It earned its slot through
mood and energy proximity — which is mathematically correct — but a human listener
wanting rock would be confused to see a pop gym track. That gap between "correct
by the algorithm" and "correct by human judgment" was the clearest demonstration
of why human evaluation can't be replaced by automated tests alone.

### AI Collaboration in This Project

**Helpful instance:** When designing the RAG prompt sent to Claude, I was going to
write a long free-form instruction. The AI suggested structuring the system prompt
to specify an exact JSON schema and explicitly prohibit markdown fences in the
response. That suggestion was directly responsible for the JSON parsing working
reliably — without it, Claude would occasionally wrap its output in triple backticks,
causing a `json.JSONDecodeError` on every other run.

**Flawed instance:** When first implementing the `score_song` function, the AI
generated a version that rewarded songs with higher energy values rather than songs
*closer* to the user's target energy. A user who wanted energy=0.4 would receive
the same high-energy songs as someone who wanted energy=0.9, because the code was
doing `song["energy"] * weight` instead of
`(1 - abs(song["energy"] - target)) * weight`. The output looked plausible — it
returned songs with scores — and I had to manually trace the logic to catch the
error. This is a good example of why AI-generated code requires verification against
the intended behavior, not just against "does it run without errors."

---

## Model Card

See [model_card.md](model_card.md) for the full documentation of VibeFinder's
intended use, known biases, evaluation methodology, and non-intended uses.
