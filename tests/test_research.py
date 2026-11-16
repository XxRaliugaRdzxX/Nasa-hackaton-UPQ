"""Pruebas del módulo de investigación (D19) y de la preparación de datos de la Historia."""

import math
import sys
from pathlib import Path

import numpy as np

from mece.research.fetch import research_config
from mece.research.pipeline import sen_con_ic

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))


def test_research_config_consistente():
    cfg = research_config()
    regions, basins = set(cfg["regions"]), set(cfg["basins"])
    assert len(regions) == 7 and len(basins) == 5
    for basin, region in cfg["pairs"]:
        assert basin in basins and region in regions
    for region, (basin, lag) in cfg["models"].items():
        assert region in regions
        assert basin is None or (basin in basins and 0 <= lag <= 4)
    for r in cfg["regions"].values():
        for lang in ("es", "en", "pt"):
            assert r[f"name_{lang}"]


def test_sen_con_ic_recupera_pendiente():
    rng = np.random.default_rng(0)
    t = np.arange(120, dtype=float)
    y = 0.5 * t + rng.normal(0, 2, t.size)
    var_s = t.size * (t.size - 1) * (2 * t.size + 5) / 18  # varianza de S sin autocorrelación
    sen, lo, hi = sen_con_ic(t, y, var_s)
    assert abs(sen - 0.5) < 0.02
    assert lo < 0.5 < hi


def test_sen_con_ic_varianza_degenerada():
    t = np.arange(10, dtype=float)
    sen, lo, hi = sen_con_ic(t, 2 * t, float("nan"))
    assert sen == 2 and math.isnan(lo) and math.isnan(hi)
    _, lo, hi = sen_con_ic(t, 2 * t, -5.0)
    assert math.isnan(lo) and math.isnan(hi)


def test_json_safe_sin_nan():
    from story import json_safe

    src = {"a": np.float32(1.5), "b": [float("nan"), np.int64(3)], "c": {"d": float("inf")}}
    out = json_safe(src)
    assert out == {"a": 1.5, "b": [None, 3], "c": {"d": None}}
