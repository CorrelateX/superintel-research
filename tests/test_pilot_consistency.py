from scripts.seed_pilot_data import _make_close_series
from scripts.timescale_demo import PAIRS
from superintel_research.backend.routes.research import DEFAULT_PAIRS


def test_default_pairs_are_available_in_public_seed() -> None:
    seeded_symbols = set(_make_close_series(periods=10))
    configured_symbols = {
        symbol
        for pairs in (PAIRS, DEFAULT_PAIRS)
        for pair in pairs
        for symbol in pair
    }

    assert configured_symbols <= seeded_symbols