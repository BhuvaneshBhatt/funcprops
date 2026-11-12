"""Classify every field so added range-certificate payloads require review."""

from dataclasses import fields

import funcprops as fp
from funcprops.real_images.interior import InteriorCriticalCover
from funcprops.real_images.tails import BoundedTailImage
from funcprops.real_images.transfers import (
    ComponentImage,
    MonotoneTail,
    RealFormulaImage,
    ReflectedImage,
)

# Replay checks these fields. Status and diagnostics are listed separately:
# changing them cannot establish or enlarge a mathematical image.
FIELDS = {
    RealFormulaImage: {"premises": {"formula", "analysis"}, "metadata": set()},
    ComponentImage: {"premises": {"analyses"}, "metadata": set()},
    fp.OscillatoryEscape: {
        "premises": {
            "expression",
            "variable",
            "domain",
            "amplitude",
            "offset",
            "oscillator",
            "direction",
            "sequences",
        },
        "metadata": set(),
    },
    fp.DenseTrigImage: {
        "premises": {
            "expression",
            "variable",
            "domain",
            "terms",
            "offset",
            "frequency_polynomial",
            "image",
        },
        "metadata": set(),
    },
    fp.FiniteTailBound: {
        "premises": {"expression", "variable", "domain", "limit", "lower", "upper"},
        "metadata": {"certified"},
    },
    fp.InteriorRootCover: {
        "premises": {
            "source",
            "expression",
            "variable",
            "domain",
            "equation",
            "denominator",
            "proof",
        },
        "metadata": set(),
    },
    fp.ConvexLevelWitness: {
        "premises": {
            "base",
            "center",
            "minimum",
            "left_value",
            "right_value",
            "curvature",
        },
        "metadata": set(),
    },
    ReflectedImage: {"premises": {"analysis"}, "metadata": set()},
    BoundedTailImage: {"premises": {"core", "tails"}, "metadata": set()},
    InteriorCriticalCover: {
        "premises": {"source", "expression", "variable", "domain", "roots", "sign"},
        "metadata": set(),
    },
    fp.TailValueBound: {
        "premises": {
            "expression",
            "variable",
            "domain",
            "trend",
            "remainder",
            "remainder_bounds",
            "limit",
            "bound",
        },
        "metadata": {"certified"},
    },
    fp.RangeAnalysis: {
        "premises": {
            "expression",
            "variable",
            "requested",
            "domain_record",
            "cells",
            "image",
            "inner",
            "outer",
            "unresolved",
            "transfer",
        },
        "metadata": {"reason", "certified"},
    },
    fp.CriticalValueCover: {
        "premises": {
            "expression",
            "variable",
            "domain",
            "critical_cover",
            "sites",
            "samples",
            "search_state",
        },
        "metadata": set(),
    },
    fp.CriticalValueEnclosure: {
        "premises": {"value", "root_cover", "enclosure"},
        "metadata": set(),
    },
    MonotoneTail: {
        "premises": {
            "expression",
            "variable",
            "domain",
            "sign_proof",
            "limit",
            "image",
        },
        "metadata": set(),
    },
    fp.ParameterRangeAnalysis: {
        "premises": {
            "expression",
            "variable",
            "parameters",
            "domain",
            "parameter_domain",
            "value",
            "condition",
            "transitions",
            "complete",
        },
        "metadata": {"certified", "reason"},
    },
}


def test_field_classification():
    for record, roles in FIELDS.items():
        assert roles["premises"].isdisjoint(roles["metadata"])
        assert {f.name for f in fields(record)} == roles["premises"] | roles["metadata"]
