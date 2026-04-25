"""
VibeFinder CLI — AI-powered music recommender with RAG + reliability testing.

Modes:
  recommend   Run the full RAG pipeline for a single user profile
  evaluate    Run the automated reliability test suite
  consistency Check whether recommendations are stable across repeated runs

Usage:
  python -m src.main recommend
  python -m src.main recommend --profile lofi
  python -m src.main evaluate
  python -m src.main consistency --profile rock
"""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ──────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("logs/vibefinder.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("vibefinder.main")

# ── Imports after logging setup ────────────────────────────────────────────
from src.guardrails import validate_profile, detect_conflicts
from src.rag_engine import RAGRecommender
from src.evaluator import run_evaluation, check_consistency, write_report

CSV_PATH = "data/songs.csv"

DEMO_PROFILES = {
    "pop":  {"genre": "pop",     "mood": "happy",   "energy": 0.85, "likes_acoustic": False},
    "lofi": {"genre": "lofi",    "mood": "chill",   "energy": 0.38, "likes_acoustic": True},
    "rock": {"genre": "rock",    "mood": "intense", "energy": 0.92, "likes_acoustic": False},
    "edge": {"genre": "ambient", "mood": "peaceful","energy": 0.95, "likes_acoustic": False},
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _print_divider(char: str = "-", width: int = 60) -> None:
    print(char * width)


def _print_rag_result(result: dict, profile_label: str) -> None:
    _print_divider("=")
    print(f"  VibeFinder -- {profile_label}")
    _print_divider("=")
    print(f"\n  Playlist vibe:\n  {result.get('playlist_narrative', '')}\n")

    if result.get("conflict_note"):
        print(f"  [!] Conflict note: {result['conflict_note']}\n")

    for i, rec in enumerate(result.get("recommendations", []), 1):
        print(f"  #{i}  {rec['title']} -- {rec['artist']}")
        print(f"       Score : {rec.get('score', '-')}")
        print(f"       Why   : {rec.get('explanation', '')}")
        print()
    _print_divider()


# ── Modes ──────────────────────────────────────────────────────────────────

def mode_recommend(profile_key: str) -> None:
    prefs = DEMO_PROFILES.get(profile_key, DEMO_PROFILES["pop"])
    label = f"{prefs['genre']} / {prefs['mood']} / energy={prefs['energy']}"

    is_valid, msgs = validate_profile(prefs)
    conflicts = detect_conflicts(prefs)

    if not is_valid:
        print("\n  ERROR: invalid profile —", "; ".join(msgs))
        sys.exit(1)

    for m in msgs:
        print(f"  WARNING: {m}")

    if conflicts:
        print()
        for c in conflicts:
            print(f"  [!] {c}")

    print(f"\n  Running RAG pipeline for profile: {label}")
    logger.info("recommend mode — profile: %s", label)

    engine = RAGRecommender(CSV_PATH)
    result = engine.recommend(prefs)
    _print_rag_result(result, label)


def mode_evaluate() -> None:
    print("\n  Running reliability evaluation suite...\n")
    logger.info("evaluate mode started")

    results = run_evaluation(CSV_PATH)
    passed = sum(1 for r in results if r["pass"])

    _print_divider("=")
    print(f"  Evaluation Results  ({passed}/{len(results)} passed)")
    _print_divider("=")
    print()

    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        conflict_flag = " [conflicts detected]" if r["conflicts"] else ""
        print(f"  [{status}]  {r['profile']}{conflict_flag}")
        print(f"          top: {r['top_song']} (score {r['top_score']})")
        for c in r["conflicts"]:
            print(f"          [!] {c}")
        print()

    consistency = check_consistency(CSV_PATH, DEMO_PROFILES["pop"], runs=3)
    stable = "STABLE [OK]" if consistency["consistent"] else "UNSTABLE [FAIL]"
    print(f"  Consistency check (pop profile, 3 runs): {stable}")

    path = write_report(results, consistency)
    _print_divider()
    print(f"\n  Full report saved to: {path}\n")


def mode_consistency(profile_key: str) -> None:
    prefs = DEMO_PROFILES.get(profile_key, DEMO_PROFILES["pop"])
    label = f"{prefs['genre']} / {prefs['mood']}"
    print(f"\n  Consistency check — {label} (5 runs)\n")
    logger.info("consistency mode — profile: %s", label)

    report = check_consistency(CSV_PATH, prefs, runs=5)
    _print_divider()
    for i, run in enumerate(report["top_5_each_run"], 1):
        print(f"  Run {i}: {', '.join(run)}")
    _print_divider()
    status = "STABLE [OK]" if report["consistent"] else "UNSTABLE [FAIL]"
    print(f"\n  Result: {status}\n")


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="VibeFinder: AI music recommender with RAG + reliability testing",
    )
    sub = parser.add_subparsers(dest="mode")

    rec_p = sub.add_parser("recommend", help="Run the RAG recommendation pipeline")
    rec_p.add_argument(
        "--profile", choices=list(DEMO_PROFILES.keys()), default="pop",
        help="Demo profile to use (default: pop)",
    )

    sub.add_parser("evaluate", help="Run the full reliability evaluation suite")

    con_p = sub.add_parser("consistency", help="Check recommendation stability across runs")
    con_p.add_argument(
        "--profile", choices=list(DEMO_PROFILES.keys()), default="pop",
        help="Profile to test (default: pop)",
    )

    args = parser.parse_args()

    if args.mode == "recommend":
        mode_recommend(args.profile)
    elif args.mode == "evaluate":
        mode_evaluate()
    elif args.mode == "consistency":
        mode_consistency(args.profile)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
