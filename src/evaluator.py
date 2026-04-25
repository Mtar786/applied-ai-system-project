"""
Reliability evaluator for VibeFinder.

Runs a suite of user profiles through the recommender, checks whether results
match expectations, measures consistency across repeated runs, and writes a
structured log to logs/evaluation.log.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from src.recommender import load_songs, recommend_songs
from src.guardrails import validate_profile, detect_conflicts

logger = logging.getLogger(__name__)

# Standard test suite used for automated evaluation
EVAL_PROFILES = [
    {
        "name": "High-Energy Pop",
        "prefs": {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False},
        "expect_top_genre": "pop",
        "expect_top_mood": "happy",
    },
    {
        "name": "Chill Lofi",
        "prefs": {"genre": "lofi", "mood": "chill", "energy": 0.38, "likes_acoustic": True},
        "expect_top_genre": "lofi",
        "expect_top_mood": "chill",
    },
    {
        "name": "Deep Intense Rock",
        "prefs": {"genre": "rock", "mood": "intense", "energy": 0.92, "likes_acoustic": False},
        "expect_top_genre": "rock",
        "expect_top_mood": "intense",
    },
    {
        "name": "Jazz Relaxed",
        "prefs": {"genre": "jazz", "mood": "relaxed", "energy": 0.34, "likes_acoustic": True},
        "expect_top_genre": "jazz",
        "expect_top_mood": "relaxed",
    },
    {
        "name": "Edge Case — Conflicting",
        "prefs": {"genre": "ambient", "mood": "peaceful", "energy": 0.95, "likes_acoustic": False},
        "expect_top_genre": "ambient",
        "expect_top_mood": None,  # conflict expected; no mood assertion
    },
]


def _setup_log_dir() -> str:
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def run_evaluation(csv_path: str, profiles: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Run each profile through the recommender and check basic expectations.
    Returns a list of result dicts with pass/fail fields.
    """
    songs = load_songs(csv_path)
    profiles = profiles or EVAL_PROFILES
    results = []

    for profile in profiles:
        name = profile["name"]
        prefs = profile["prefs"]

        # Guardrail checks
        is_valid, validation_msgs = validate_profile(prefs)
        conflicts = detect_conflicts(prefs)

        recs = recommend_songs(prefs, songs, k=5)
        top_song, top_score, top_reasons = recs[0] if recs else ({}, 0.0, "")

        genre_pass = (
            top_song.get("genre") == profile.get("expect_top_genre")
            if profile.get("expect_top_genre") else None
        )
        mood_pass = (
            top_song.get("mood") == profile.get("expect_top_mood")
            if profile.get("expect_top_mood") else None
        )
        overall_pass = all(v is not False for v in [genre_pass, mood_pass])

        result = {
            "profile": name,
            "valid_input": is_valid,
            "conflicts": conflicts,
            "top_song": top_song.get("title", "N/A"),
            "top_artist": top_song.get("artist", "N/A"),
            "top_score": round(top_score, 2),
            "genre_check": genre_pass,
            "mood_check": mood_pass,
            "pass": overall_pass,
            "timestamp": datetime.utcnow().isoformat(),
        }
        results.append(result)
        status = "PASS" if overall_pass else "FAIL"
        logger.info("[%s] %s — top: %s (%.2f)", status, name, top_song.get("title"), top_score)

    return results


def check_consistency(csv_path: str, prefs: Dict, runs: int = 3) -> Dict:
    """
    Run the same profile multiple times and check that results are identical.
    Returns a consistency report dict.
    """
    songs = load_songs(csv_path)
    all_top_titles = []

    for _ in range(runs):
        recs = recommend_songs(prefs, songs, k=5)
        titles = [s["title"] for s, _, _ in recs]
        all_top_titles.append(titles)

    consistent = all(t == all_top_titles[0] for t in all_top_titles)
    report = {
        "runs": runs,
        "consistent": consistent,
        "top_5_each_run": all_top_titles,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info("Consistency check (%d runs): %s", runs, "PASS" if consistent else "FAIL")
    return report


def write_report(results: List[Dict], consistency: Optional[Dict] = None) -> str:
    """Write a JSON evaluation report to logs/evaluation_<timestamp>.json and return the path."""
    log_dir = _setup_log_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"evaluation_{timestamp}.json")

    passed = sum(1 for r in results if r["pass"])
    report = {
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": f"{passed / len(results) * 100:.0f}%",
        },
        "profile_results": results,
        "consistency": consistency,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Evaluation report written to %s", path)
    return path
