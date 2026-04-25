# VibeFinder — AI-Powered Music Recommender

An applied AI system that extends a content-based music recommender with a
**Retrieval-Augmented Generation (RAG)** pipeline, **input guardrails**, and a
**reliability evaluation suite**. Built on top of the Module 3 music recommender
as a final capstone project.

---

## System Architecture

```
User Profile (genre, mood, energy, likes_acoustic)
        |
        v
[Guardrails] ---------- invalid/conflicting? --> warn or reject
        |
        v
[Retriever] -- score_song() on all 20 songs --> top-10 candidates
        |
        v
[Claude API] -- curates top-5, writes narrative + per-song explanations
        |
        v
[Output] -- ranked playlist with vibe summary
        |
        v
[Evaluator] -- runs profile suite, checks consistency, writes JSON report to logs/
```

**AI Feature implemented: Retrieval-Augmented Generation (RAG)**
The retriever (weighted scorer) narrows 20 songs to the 10 best candidates.
Claude then reads those candidates as context and generates a curated playlist
with a narrative explanation. Neither component alone is as good: the scorer
provides structured ranking; Claude provides natural-language reasoning and
holistic curation.

---

## Project Structure

```
applied-ai-system-project/
├── src/
│   ├── recommender.py    # Song, UserProfile, Recommender, load_songs, recommend_songs
│   ├── guardrails.py     # Input validation + conflict detection
│   ├── rag_engine.py     # RAG pipeline: retrieval + Claude generation
│   ├── evaluator.py      # Reliability test suite + JSON report writer
│   └── main.py           # CLI entry point (recommend / evaluate / consistency)
├── data/
│   └── songs.csv         # 20 songs across 14 genres
├── tests/
│   └── test_recommender.py  # 9 tests covering all modules
├── logs/                 # Auto-created; stores evaluation JSON reports
├── assets/               # System diagrams and screenshots
├── model_card.md         # Full model card for VibeFinder
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and enter the repo

```bash
git clone https://github.com/Mtar786/applied-ai-system-project.git
cd applied-ai-system-project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key (optional)

Without a key the system runs in **retriever-only fallback mode** — all features
work except the Claude curation step.

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Run a recommendation (RAG pipeline)

```bash
python -m src.main recommend                    # default: pop profile
python -m src.main recommend --profile lofi
python -m src.main recommend --profile rock
python -m src.main recommend --profile edge     # adversarial / conflicting prefs
```

### Run the reliability evaluation suite

```bash
python -m src.main evaluate
```

Runs 5 preset profiles, checks whether top results match expected genres/moods,
runs a 3-run consistency check, and saves a JSON report to `logs/`.

### Check recommendation stability

```bash
python -m src.main consistency                  # default: pop profile
python -m src.main consistency --profile lofi
```

Runs the same profile 5 times and confirms all outputs are identical
(the scorer is deterministic, so this should always be STABLE).

### Run tests

```bash
pytest
```

9 tests covering: recommender sorting, explanation generation, guardrail
validation, conflict detection, evaluator suite, and consistency check.

---

## AI Features

### Retrieval-Augmented Generation (RAG)

| Step | Component | What it does |
|------|-----------|--------------|
| Retrieve | `recommend_songs()` | Scores all 20 songs, returns top-10 candidates |
| Augment | `_format_candidates()` | Formats candidates as structured context |
| Generate | Claude (`claude-haiku-4-5`) | Curates top-5, writes vibe narrative + explanations |
| Fallback | `_fallback()` | Returns scorer output if no API key is set |

### Guardrails

- **Field validation** — rejects profiles missing `genre`, `mood`, or `energy`
- **Range validation** — rejects energy values outside 0.0–1.0
- **Unknown value warnings** — warns if genre/mood are not in the known catalog
- **Conflict detection** — flags contradictory preference pairs before running
  (e.g., ambient genre + energy=0.95, peaceful mood + high energy)

### Reliability Testing

- **Profile suite** — 5 profiles with expected outcomes; each PASS/FAIL is logged
- **Consistency check** — reruns the same profile N times; confirms output is stable
- **JSON report** — timestamped report written to `logs/evaluation_<ts>.json`
- **Logging** — all runs append to `logs/vibefinder.log`

---

## Evaluation Results (Retriever Layer)

| Profile | Top Song | Score | Pass |
|---------|----------|-------|------|
| High-Energy Pop | Sunrise City | 6.94 | PASS |
| Chill Lofi | Library Rain | 7.80 | PASS |
| Deep Intense Rock | Storm Runner | 6.98 | PASS |
| Jazz Relaxed | Sunday Brunch | 7.87 | PASS |
| Edge Case (conflicting) | Soft Thunder | 3.76 | PASS (conflicts flagged) |

Consistency check (pop, 3 runs): **STABLE**

---

## Limitations

- Catalog is 20 hand-authored songs — niche genre users hit a score ceiling quickly
- Genre and mood matching is exact string comparison; "indie pop" != "pop"
- High genre weight (3.0 pts) creates filter bubbles
- Claude curation requires an API key; fallback mode skips the generation step
- No listening history — preferences are static per session

See [model_card.md](model_card.md) for the full bias and limitations analysis.

---

## Design and Architecture Notes

**Why RAG over a pure LLM approach?**
Sending all 20 songs to Claude every time would work, but the retrieval step does
meaningful work: it prunes candidates based on quantitative scoring so Claude
receives a focused, ranked shortlist rather than an unordered dump. This mirrors
how production RAG systems use dense retrieval to pre-filter before generation.

**Why include guardrails?**
Phase 4 testing revealed that contradictory preferences (ambient + high energy)
caused the system to silently return incoherent results. Guardrails surface that
problem before it reaches the recommender or Claude.

**Why a reliability evaluator?**
A deterministic scorer should always produce the same output for the same input.
The consistency check enforces that. The profile suite checks directional
correctness — that a "pop user" gets a pop song at the top, not just any song.
