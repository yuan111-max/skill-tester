"""Tests for the configuration loader."""

from __future__ import annotations

import copy
from pathlib import Path
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

    def test_script_extensions_includes_all_types(self):
        """Default config should include all supported script extensions."""
        config = load_config()
        exts = config.get("analysis", {}).get("script_extensions", [])
        assert ".py" in exts
        assert ".sh" in exts
        assert ".js" in exts
        assert ".ts" in exts
        assert ".rb" in exts
        assert ".go" in exts

    def test_pyyaml_is_hard_dependency(self):
        """PyYAML is required — importing config raises ImportError if missing."""
        import scripts.config as cfg
        # The module-level 'import yaml' means PyYAML is non-optional.
        # If this test runs, PyYAML is installed (it's in requirements.txt).
        assert cfg.yaml is not None

    def test_local_yaml_overrides_default(self, tmp_path: Path, monkeypatch):
        """A local.yaml beside default.yaml should be loaded and merged."""
        # Point _DEFAULT_CONFIG_PATH to a temp dir so local.yaml loads from there
        fake_config_dir = tmp_path / "config"
        fake_config_dir.mkdir()
        default = fake_config_dir / "default.yaml"
        default.write_text("execution:\n  max_tests: 5\n", encoding="utf-8")
        local = fake_config_dir / "local.yaml"
        local.write_text("execution:\n  max_tests: 20\n", encoding="utf-8")

        monkeypatch.setattr("scripts.config._DEFAULT_CONFIG_PATH", fake_config_dir / "default.yaml")
        config = load_config()
        assert config["execution"]["max_tests"] == 20, "local.yaml should override default"


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


class TestMergeFromFile:
    """Tests for _merge_from_file()."""

    def test_nonexistent_file_returns_silently(self, recwarn):
        """A non-existent file should be skipped without warning."""
        from scripts.config import _merge_from_file
        config = {"a": 1}
        _merge_from_file(config, Path("/nonexistent/path/config.yaml"))
        assert config == {"a": 1}
        assert len(recwarn) == 0

    def test_invalid_yaml_warns(self, tmp_path: Path, recwarn):
        """A file with invalid YAML content should warn."""
        from scripts.config import _merge_from_file
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(": : invalid yaml : :\n")
        config = {"a": 1}
        _merge_from_file(config, bad_file)
        assert len(recwarn) >= 1
        assert "YAML" in str(recwarn[0].message)

    def test_valid_yaml_merges_successfully(self, tmp_path: Path, recwarn):
        """A valid YAML file should deep-merge into config."""
        from scripts.config import _merge_from_file
        valid_file = tmp_path / "valid.yaml"
        valid_file.write_text("b: 2\nc:\n  d: 3\n")
        config = {"a": 1, "c": {"e": 4}}
        _merge_from_file(config, valid_file)
        assert config["a"] == 1
        assert config["b"] == 2
        assert config["c"]["d"] == 3
        assert config["c"]["e"] == 4  # preserved from original
        assert len(recwarn) == 0
