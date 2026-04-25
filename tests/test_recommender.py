from src.recommender import Song, UserProfile, Recommender
from src.guardrails import validate_profile, detect_conflicts
from src.evaluator import run_evaluation, check_consistency


# ── Fixtures ───────────────────────────────────────────────────────────────

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1, title="Test Pop Track", artist="Test Artist",
            genre="pop", mood="happy", energy=0.8, tempo_bpm=120,
            valence=0.9, danceability=0.8, acousticness=0.2,
        ),
        Song(
            id=2, title="Chill Lofi Loop", artist="Test Artist",
            genre="lofi", mood="chill", energy=0.4, tempo_bpm=80,
            valence=0.6, danceability=0.5, acousticness=0.9,
        ),
    ]
    return Recommender(songs)


# ── Original recommender tests ─────────────────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)
    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── Guardrail tests ────────────────────────────────────────────────────────

def test_validate_profile_accepts_valid_input():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    is_valid, msgs = validate_profile(prefs)
    assert is_valid
    blocking = [m for m in msgs if not m.startswith("WARNING")]
    assert blocking == []


def test_validate_profile_rejects_missing_field():
    prefs = {"genre": "pop", "mood": "happy"}  # missing energy
    is_valid, msgs = validate_profile(prefs)
    assert not is_valid
    assert any("energy" in m for m in msgs)


def test_validate_profile_rejects_energy_out_of_range():
    prefs = {"genre": "pop", "mood": "happy", "energy": 1.5}
    is_valid, msgs = validate_profile(prefs)
    assert not is_valid
    assert any("energy" in m for m in msgs)


def test_detect_conflicts_flags_peaceful_high_energy():
    prefs = {"genre": "ambient", "mood": "peaceful", "energy": 0.95}
    conflicts = detect_conflicts(prefs)
    assert len(conflicts) > 0


def test_detect_conflicts_returns_empty_for_valid_profile():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    conflicts = detect_conflicts(prefs)
    assert conflicts == []


# ── Evaluator tests ────────────────────────────────────────────────────────

def test_evaluation_suite_runs_and_returns_results():
    results = run_evaluation("data/songs.csv")
    assert len(results) > 0
    for r in results:
        assert "pass" in r
        assert "top_song" in r


def test_consistency_check_is_stable_for_deterministic_scorer():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False}
    report = check_consistency("data/songs.csv", prefs, runs=3)
    assert report["consistent"] is True
    assert report["runs"] == 3
