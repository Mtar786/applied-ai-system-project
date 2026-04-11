# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**What it is for:**
This model suggests up to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is designed for classroom exploration of how content-based recommendation systems work. It is transparent by design — every recommendation comes with a plain-language explanation — so students and learners can see exactly why each song ranked where it did.

**What it is NOT for:**
- Real product deployment. The catalog is 20 hand-authored songs; no real user would find this useful at scale.
- Personalization over time. The system has no memory — it does not learn from skips, replays, or past sessions.
- Representing diverse musical taste. The dataset skews heavily toward Western popular genres; listeners whose primary genres are underrepresented (classical, world music, regional folk) will receive poor results.
- High-stakes decisions. This system should never be used to decide what music gets promoted, monetized, or surfaced to real audiences, as its biases are known and unmitigated.

---

## 3. How the Model Works

VibeFinder looks at four things about each song and compares them to what the user says they like:

1. **Genre** — If the song's genre matches the user's favorite, it gets a big bonus (3 points). Genre is the strongest signal because it's the broadest description of musical style.
2. **Mood** — If the song's mood matches (e.g., both "happy" or both "chill"), it earns 2 more points.
3. **Energy closeness** — Instead of rewarding high or low energy songs, the system rewards songs that are *close* to the user's ideal. A user who wants medium energy (0.5) gets penalized for an intense track (0.95) just as much as for a sleepy one (0.1). This closeness is worth up to 2 points.
4. **Acoustic preference** — If the user likes acoustic music, songs with higher acousticness earn a small bonus (up to 1 point).

Every song in the catalog gets a total score (maximum 8.0). The top 5 highest-scoring songs are returned as recommendations, along with an explanation of why each one ranked where it did.

---

## 4. Data

- The catalog contains **20 songs** stored in `data/songs.csv`.
- Genres represented: pop, lofi, rock, ambient, jazz, synthwave, indie pop, country, electronic, classical, punk, folk, r&b, world music, metal.
- Moods represented: happy, chill, intense, focused, relaxed, moody, peaceful, romantic, energetic, angry.
- 10 songs were in the original starter file; 10 were added to improve genre diversity.
- The dataset skews toward Western popular music styles. Genres like world music, classical, and country have only one or two songs each, making it hard for users who prefer those styles to get good recommendations.
- No real user listening data was used. All songs were hand-authored for simulation purposes.

---

## 5. Strengths

- **Transparent and explainable** — every recommendation comes with a plain-language reason ("genre match +3.0; energy proximity +1.94"), making it easy to understand why a song ranked where it did.
- **Works well for mainstream taste profiles** — users who prefer pop, lofi, or rock get strong, intuitive results because those genres have more songs in the catalog.
- **Energy proximity is more nuanced than raw sorting** — by rewarding closeness rather than highest/lowest energy, the system avoids always recommending extreme tracks.
- **Chill Lofi profile** produced the most satisfying results: Library Rain and Midnight Coding both scored above 7.6, and both intuitively fit a study/background listening context.

---

## 6. Limitations and Bias

**Genre weight creates a filter bubble.** Genre carries 3 out of a maximum 8 points — more than any other single feature. A user who favors pop will almost always see pop songs at the top, even if a jazz track perfectly matches their energy and mood. This is the definition of a filter bubble: the system keeps confirming what you already said you like rather than surprising you with something new.

**Underrepresented genres hit a ceiling.** Classical, country, folk, r&b, world, and metal each have only one song in the catalog. A user with `favorite_genre = "classical"` can earn the genre bonus from at most one song. Their top 5 will quickly fill with songs from totally unrelated genres just based on energy proximity — which may feel completely off.

**Exact string matching is brittle.** Genre and mood comparisons are case-sensitive exact matches. A user profile with `genre = "Indie Pop"` gets zero genre bonus when comparing to a song tagged `"indie pop"`. Similarly, "happy" and "joyful" are treated as completely different moods even though they describe the same feeling.

**The edge-case profile revealed a fundamental flaw.** A user who wants `genre=ambient`, `mood=peaceful`, and `energy=0.95` is describing something that does not exist in music — ambient and peaceful tracks are inherently low energy. The system returned ambient songs (genre match) but penalized them heavily for energy mismatch, and surfaced high-energy non-ambient songs in the lower ranks. The recommendations were incoherent. A real system would flag conflicting preferences rather than silently produce bad results.

**No diversity enforcement.** The system can return the same artist multiple times (e.g., LoRoom at #2 and #3 for the Chill Lofi profile). Real platforms deliberately inject variety to prevent repetition.

---

## 7. Evaluation

**Profiles tested and findings:**

| Profile | Top Result | Score | Intuition Check |
|---------|-----------|-------|-----------------|
| High-Energy Pop | Sunrise City (Neon Echo) | 6.94 | ✅ Perfect match — pop, happy, high energy |
| Chill Lofi | Library Rain (Paper Lanterns) | 7.80 | ✅ Correct — low energy lofi with high acousticness |
| Deep Intense Rock | Storm Runner (Voltline) | 6.98 | ✅ Only rock song in catalog, clearly #1 |
| Edge Case (conflicting) | Soft Thunder (Cloudbreak) | 3.76 | ⚠️ Genre matched but energy was totally wrong |

**Surprising finding — Gym Hero keeps appearing:**  
Gym Hero (pop, intense, energy=0.93) showed up in both the High-Energy Pop list (#2) and the Deep Intense Rock list (#2). This makes sense mathematically — it scores genre points for the pop user and mood+energy points for the rock user — but it is not a rock song at all. A real listener wanting intense rock would be annoyed to see a pop gym track. This reveals that mood and energy alone are not sufficient to substitute for genre when the catalog is small.

**Weight-shift experiment:**  
When genre weight was halved (3.0 → 1.5) and energy weight was doubled (2.0 → 4.0), the top result for the pop/happy profile stayed the same (Sunrise City), but Rooftop Lights jumped from #3 to #2, displacing Gym Hero. This shows that Rooftop Lights is a better energy match than Gym Hero — it just lost out under the original weights because Gym Hero shares the same genre. Doubling energy weight produced a more "vibe-accurate" ranking at the cost of de-emphasizing genre loyalty.

**Tests run:**  
Both automated tests in `tests/test_recommender.py` pass. The pop/happy user correctly receives the pop/happy song as the #1 recommendation, confirming the scoring logic is directionally correct.

---

## 8. Future Work

- **Soft genre matching** — use a genre similarity map so that "indie pop" scores partial genre points when the user wants "pop," rather than zero.
- **Diversity enforcement** — cap recommendations at one song per artist so the same artist cannot appear twice in the top 5.
- **Conflict detection** — warn the user if their profile contains contradictory preferences (e.g., very high energy + very peaceful mood) before running the recommender.
- **Mood clustering** — group similar moods (happy/joyful, chill/relaxed/peaceful) so string mismatches do not cause large score drops.
- **Collaborative layer** — track which songs users skip or replay and use that signal to adjust weights over time, moving from pure content-based to a hybrid system.
- **Larger catalog** — 20 songs is too small for meaningful diversity. A real system needs thousands of tracks to avoid the ceiling effect on niche genres.

---

## 9. Personal Reflection

**Biggest learning moment:**
The edge-case experiment was the clearest "aha" of the project. I fed the system a profile that asked for ambient genre + peaceful mood + energy=0.95. The system ran without any errors, returned five songs, and looked totally normal — but the recommendations were useless. Ambient music is inherently low-energy, so the profile was self-contradictory. The algorithm had no way to detect that and silently failed. That moment made it concrete: a system can be technically correct and practically worthless at the same time. That gap is exactly where real AI failures happen.

**How AI tools helped — and when to double-check:**
AI tools were most useful for generating boilerplate quickly (CSV loading, dataclass setup, sorted() usage) and for suggesting structural patterns like returning `(song, score, reasons)` tuples. Where I needed to slow down was anywhere the AI made a design choice without explaining it — for example, it defaulted to simple greater-than comparisons for energy rather than proximity scoring, which would have produced wrong behavior. The rule I settled on: accept AI output for *how* to write something, but always verify *what* it is actually doing against the intended algorithm before moving on.

**What surprised me about simple algorithms "feeling" like recommendations:**
I expected the output to feel mechanical and obviously wrong. Instead, the Chill Lofi results (Library Rain at #1, Midnight Coding at #2) felt genuinely right — the kind of playlist a study app might actually surface. What made the difference was the energy proximity scoring. By rewarding closeness rather than just high or low energy, the algorithm captured something real about musical "vibe" even though it had no understanding of music at all. It was just arithmetic, but the output was surprisingly intuitive. That made me realize why content-based systems were the first commercial recommenders — they do not need user data, and they already produce plausible results with very simple math.

**What I would try next:**
The limitation I most want to fix is the filter bubble. I would add a diversity pass after scoring: once the top results are ranked, replace any second occurrence of the same artist with the next-highest song from a different genre. That single rule would not change the core scoring at all but would make the output feel much more like a real playlist. After that, I would experiment with soft genre matching — building a small similarity table so that "indie pop" and "pop" share partial credit — to make the string-matching less brittle without changing the rest of the algorithm.
