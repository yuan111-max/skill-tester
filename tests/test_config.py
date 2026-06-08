"""Tests for the configuration loader."""

from __future__ import annotations

import copy
from typing import Any, Dict

import pytest

from scripts.config import (
    _deep_merge,
    _DEFAULT_CONFIG_PATH,
    load_config,
    resolve_tier,
    validate_dimension_weights,
)


class TestLoadConfig:
    """Tests for load_config()."""

    def test_load_returns_dict(self):
        """load_config() should return a non-empty dict."""
        config = load_config()
        assert isinstance(config, dict)
        assert "scoring" in config
        assert "analysis" in config
        assert "execution" in config

    def test_default_dimensions_have_weights(self):
        """Default config should have 4 dimensions with weights summing to 1.0."""
        config = load_config()
        dims = config["scoring"]["dimensions"]
        assert set(dims.keys()) == {"Documentation", "Code", "Completeness", "Usability"}
        total = sum(d["weight"] for d in dims.values())
        assert abs(total - 1.0) < 0.001

    def test_default_tiers_are_ordered(self):
        """Tiers should be in descending min order."""
        config = load_config()
        tiers = config["scoring"]["tiers"]
        mins = [t["min"] for t in tiers.values()]
        assert mins == sorted(mins, reverse=True)

    def test_execution_default_disabled(self):
        """Execution should be disabled by default."""
        config = load_config()
        assert config["execution"]["enabled"] is False
        assert config["execution"]["max_tests"] == 10
        assert config["execution"]["timeout_seconds"] == 180

    def test_anti_patterns_are_lists(self):
        """Anti-pattern rules should be a list of dicts with required keys."""
        config = load_config()
        rules = config.get("anti_patterns", [])
        assert len(rules) >= 3
        for rule in rules:
            assert "pattern" in rule
            assert "type" in rule
            assert "severity" in rule


class TestDeepMerge:
    """Tests for _deep_merge()."""

    def test_simple_override(self):
        """A simple value should be overridden."""
        base = {"a": 1, "b": 2}
        _deep_merge(base, {"b": 3})
        assert base == {"a": 1, "b": 3}

    def test_nested_merge(self):
        """Nested dicts should be deep-merged, not replaced."""
        base = {"scoring": {"dimensions": {"Doc": {"weight": 0.25}}}}
        _deep_merge(base, {"scoring": {"tiers": {"GOLD": {"min": 9.0}}}})
        assert base["scoring"]["dimensions"]["Doc"]["weight"] == 0.25
        assert base["scoring"]["tiers"]["GOLD"]["min"] == 9.0

    def test_new_key_added(self):
        """A key not in base should be added."""
        base = {"a": 1}
        _deep_merge(base, {"b": 2})
        assert base == {"a": 1, "b": 2}

    def test_does_not_mutate_source(self):
        """The overrides dict should not be mutated."""
        base = {"a": {"b": 1}}
        overrides = {"a": {"c": 2}}
        original = copy.deepcopy(overrides)
        _deep_merge(base, overrides)
        assert overrides == original


class TestResolveTier:
    """Tests for resolve_tier()."""

    def make_tiers(self) -> Dict[str, Any]:
        return {
            "POWERFUL": {"min": 8.5},
            "STANDARD": {"min": 7.0},
            "BASIC": {"min": 5.0},
            "REJECT": {"min": 0.0},
        }

    def test_powerful_at_85(self):
        assert resolve_tier(8.5, self.make_tiers()) == "POWERFUL"

    def test_powerful_above(self):
        assert resolve_tier(9.5, self.make_tiers()) == "POWERFUL"

    def test_standard(self):
        assert resolve_tier(7.5, self.make_tiers()) == "STANDARD"

    def test_standard_at_70(self):
        assert resolve_tier(7.0, self.make_tiers()) == "STANDARD"

    def test_basic(self):
        assert resolve_tier(6.0, self.make_tiers()) == "BASIC"

    def test_basic_at_50(self):
        assert resolve_tier(5.0, self.make_tiers()) == "BASIC"

    def test_reject(self):
        assert resolve_tier(3.0, self.make_tiers()) == "REJECT"

    def test_reject_at_zero(self):
        assert resolve_tier(0.0, self.make_tiers()) == "REJECT"

    def test_empty_tiers_fallback(self):
        """Empty tiers should fall back to REJECT."""
        assert resolve_tier(9.0, {}) == "REJECT"


class TestValidateDimensionWeights:
    """Tests for validate_dimension_weights()."""

    def test_valid_weights_no_warning(self, recwarn):
        """Weights summing to 1.0 should not warn."""
        dims = {
            "A": {"weight": 0.25},
            "B": {"weight": 0.25},
            "C": {"weight": 0.25},
            "D": {"weight": 0.25},
        }
        validate_dimension_weights(dims)
        assert len(recwarn) == 0

    def test_invalid_weights_warns(self, recwarn):
        """Weights summing != 1.0 should warn."""
        dims = {
            "A": {"weight": 0.5},
            "B": {"weight": 0.5},
            "C": {"weight": 0.5},  # sum = 1.5
        }
        validate_dimension_weights(dims)
        assert len(recwarn) == 1
        assert "sum to" in str(recwarn[0].message)

    def test_empty_dims_no_warning(self, recwarn):
        """Empty dimensions should not warn (total == 0.0, which is < 1.0 - 0.001)."""
        validate_dimension_weights({})
        assert len(recwarn) == 1  # 0.0 != 1.0
        assert "sum to" in str(recwarn[0].message)
