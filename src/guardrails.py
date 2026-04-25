"""
Guardrails for VibeFinder: validate user profiles before they reach the recommender or Claude.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

KNOWN_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave", "indie pop",
    "country", "electronic", "classical", "punk", "folk", "r&b", "world", "metal",
}

KNOWN_MOODS = {
    "happy", "chill", "intense", "focused", "relaxed", "moody",
    "peaceful", "romantic", "energetic", "angry",
}

# Pairs that are physically contradictory in music
_CONFLICT_RULES = [
    (
        lambda p: p.get("mood") in {"peaceful", "chill", "relaxed"} and p.get("energy", 0.5) > 0.75,
        "mood '{mood}' is typically low-energy but target_energy={energy:.2f} is high — results may be incoherent",
    ),
    (
        lambda p: p.get("genre") in {"ambient", "classical", "lofi"} and p.get("energy", 0.5) > 0.80,
        "genre '{genre}' is inherently low-energy but target_energy={energy:.2f} is very high — few matches will exist",
    ),
    (
        lambda p: p.get("mood") in {"angry", "intense"} and p.get("energy", 0.5) < 0.30,
        "mood '{mood}' is typically high-energy but target_energy={energy:.2f} is very low — results may conflict",
    ),
]


def validate_profile(user_prefs: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a user preference dict. Returns (is_valid, list_of_error_strings).
    Errors are blocking; warnings are non-blocking and returned as prefixed strings.
    """
    errors: List[str] = []

    # Required fields
    for field in ("genre", "mood", "energy"):
        if field not in user_prefs:
            errors.append(f"missing required field: '{field}'")

    if errors:
        logger.warning("Profile validation failed: %s", errors)
        return False, errors

    # Energy range
    energy = user_prefs["energy"]
    if not isinstance(energy, (int, float)) or not (0.0 <= energy <= 1.0):
        errors.append(f"energy must be a float between 0.0 and 1.0, got {energy!r}")

    # Known genre / mood (warn, don't block — user may have added new songs)
    genre = user_prefs["genre"]
    mood = user_prefs["mood"]
    if genre not in KNOWN_GENRES:
        errors.append(f"WARNING: genre '{genre}' is not in the known catalog — expect few or no genre matches")
    if mood not in KNOWN_MOODS:
        errors.append(f"WARNING: mood '{mood}' is not in the known catalog — expect few or no mood matches")

    is_valid = not any(not e.startswith("WARNING") for e in errors)
    if errors:
        logger.info("Profile warnings: %s", [e for e in errors if e.startswith("WARNING")])
    return is_valid, errors


def detect_conflicts(user_prefs: Dict) -> List[str]:
    """Return a list of human-readable conflict descriptions for contradictory preferences."""
    conflicts = []
    for rule_fn, template in _CONFLICT_RULES:
        try:
            if rule_fn(user_prefs):
                msg = template.format(
                    genre=user_prefs.get("genre", ""),
                    mood=user_prefs.get("mood", ""),
                    energy=user_prefs.get("energy", 0.5),
                )
                conflicts.append(msg)
        except Exception:
            pass
    if conflicts:
        logger.warning("Conflicts detected in profile: %s", conflicts)
    return conflicts
