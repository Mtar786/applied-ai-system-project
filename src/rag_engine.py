"""
RAG engine for VibeFinder.

Pipeline:
  1. Retrieve  — score all songs with the existing weighted scorer, return top-k candidates
  2. Augment   — format candidates as structured context for Claude
  3. Generate  — Claude curates a final playlist with narrative and per-song explanations
  4. Fallback  — if no API key is set, return the retriever output with a note
"""

import json
import logging
import os
from typing import Dict, List, Optional

import anthropic

from src.recommender import load_songs, recommend_songs

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are VibeFinder, an expert music curator. You receive a user's taste profile and a \
shortlist of candidate songs pre-ranked by a scoring algorithm. Your job is to:
1. Select the best 5 songs from the candidates for this specific user.
2. Write a 2-sentence playlist narrative describing the overall vibe.
3. Write one sentence per song explaining why it fits this user.
4. If the user's preferences seem contradictory, note it briefly.

Respond ONLY with valid JSON matching this exact schema (no markdown fences):
{
  "playlist_narrative": "string",
  "conflict_note": "string or null",
  "recommendations": [
    {
      "title": "string",
      "artist": "string",
      "score": number,
      "explanation": "string"
    }
  ]
}
"""


def _format_candidates(candidates: List) -> str:
    lines = []
    for rank, (song, score, reasons) in enumerate(candidates, 1):
        lines.append(
            f"{rank}. \"{song['title']}\" by {song['artist']} "
            f"[genre={song['genre']}, mood={song['mood']}, energy={song['energy']:.2f}] "
            f"— score {score:.2f} ({reasons})"
        )
    return "\n".join(lines)


def _format_profile(user_prefs: Dict) -> str:
    parts = [f"genre={user_prefs.get('genre')}",
             f"mood={user_prefs.get('mood')}",
             f"energy={user_prefs.get('energy')}",
             f"likes_acoustic={user_prefs.get('likes_acoustic', False)}"]
    return ", ".join(parts)


class RAGRecommender:
    """Full RAG pipeline: retrieval via scoring algorithm + generation via Claude."""

    def __init__(self, csv_path: str, api_key: Optional[str] = None):
        self.songs = load_songs(csv_path)
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = anthropic.Anthropic(api_key=self._api_key) if self._api_key else None
        if not self._client:
            logger.warning("No ANTHROPIC_API_KEY found — RAG will use retriever-only fallback")

    def retrieve(self, user_prefs: Dict, k: int = 10) -> List:
        """Return top-k scored candidates from the catalog."""
        return recommend_songs(user_prefs, self.songs, k=k)

    def generate(self, user_prefs: Dict, candidates: List) -> Dict:
        """Send candidates to Claude and return a structured playlist dict."""
        if not self._client:
            return self._fallback(candidates)

        user_message = (
            f"User taste profile: {_format_profile(user_prefs)}\n\n"
            f"Candidate songs (pre-ranked by scoring algorithm):\n"
            f"{_format_candidates(candidates)}"
        )

        logger.info("Sending %d candidates to Claude for curation", len(candidates))
        try:
            response = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text.strip()
            result = json.loads(raw)
            logger.info("Claude returned playlist with %d tracks", len(result.get("recommendations", [])))
            return result
        except json.JSONDecodeError as e:
            logger.error("Claude returned invalid JSON: %s", e)
            return self._fallback(candidates)
        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            return self._fallback(candidates)

    def recommend(self, user_prefs: Dict, retrieve_k: int = 10, final_k: int = 5) -> Dict:
        """Full pipeline: retrieve → augment → generate."""
        candidates = self.retrieve(user_prefs, k=retrieve_k)
        result = self.generate(user_prefs, candidates)
        # Trim to final_k in case Claude returned more
        if "recommendations" in result:
            result["recommendations"] = result["recommendations"][:final_k]
        return result

    def _fallback(self, candidates: List) -> Dict:
        """Return top-5 candidates formatted as a playlist dict, no Claude call."""
        recs = []
        for song, score, reasons in candidates[:5]:
            recs.append({
                "title": song["title"],
                "artist": song["artist"],
                "score": round(score, 2),
                "explanation": reasons,
            })
        return {
            "playlist_narrative": (
                "Recommendations generated by scoring algorithm only "
                "(no API key configured — Claude curation unavailable)."
            ),
            "conflict_note": None,
            "recommendations": recs,
        }
