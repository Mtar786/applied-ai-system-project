# VibeFinder — AI-Powered Music Recommender

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

## Model Card

See [model_card.md](model_card.md) for the full documentation of VibeFinder's
intended use, known biases, evaluation methodology, and non-intended uses.
