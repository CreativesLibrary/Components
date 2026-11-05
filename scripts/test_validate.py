#!/usr/bin/env python3
"""Tests for validate.py. Run from the repo root:

    python3 -m unittest discover -s scripts -p "test_*.py"

Each test starts from the real components.json and breaks one thing, so the
assertions also prove the shipped registry is valid to begin with.
"""

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _registry import COMPONENTS_JSON, load  # noqa: E402
from validate import validate  # noqa: E402


def registry():
    return copy.deepcopy(load())


class ValidateTests(unittest.TestCase):
    def test_shipped_registry_is_valid(self):
        with open(COMPONENTS_JSON, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(validate(load(), text), [])

    def test_duplicate_showpiece_name_reports_both_lines(self):
        data = registry()
        dup = copy.deepcopy(data["showpiece"][0])
        data["showpiece"].append(dup)
        text = json.dumps(data, indent=2)

        errors = validate(data, text)
        name = dup["name"]
        hits = [e for e in errors if e.startswith(f"duplicate showpiece name: {name}")]
        self.assertEqual(len(hits), 1, errors)

        expected = [i + 1 for i, line in enumerate(text.splitlines()) if f'"name": "{name}"' in line]
        self.assertEqual(len(expected), 2)
        self.assertIn(f"(lines {expected[0]}, {expected[1]})", hits[0])

    def test_duplicate_name_without_text_still_fails(self):
        data = registry()
        data["showpiece"].append(copy.deepcopy(data["showpiece"][0]))
        errors = validate(data)
        self.assertTrue(any(e.startswith("duplicate showpiece name:") for e in errors), errors)

    def test_three_copies_report_once(self):
        data = registry()
        for _ in range(2):
            data["showpiece"].append(copy.deepcopy(data["showpiece"][0]))
        text = json.dumps(data, indent=2)
        hits = [e for e in validate(data, text) if e.startswith("duplicate showpiece name:")]
        self.assertEqual(len(hits), 1, hits)
        self.assertEqual(hits[0].count(","), 2, hits[0])

    def test_missing_license_fails(self):
        data = registry()
        del data["showpiece"][0]["license"]
        name = data["showpiece"][0]["name"]
        self.assertIn(f"{name}: license missing", validate(data))

    def test_missing_license_on_fallback_fails(self):
        data = registry()
        del data["fallback_basic"]["components"][0]["license"]
        name = data["fallback_basic"]["components"][0]["name"]
        self.assertIn(f"{name}: license missing", validate(data))

    def test_missing_license_on_framework_variant_fails(self):
        data = registry()
        entry = next(e for e in data["showpiece"] if e.get("frameworks"))
        fw, variant = next(iter(entry["frameworks"].items()))
        del variant["license"]
        self.assertIn(f"{entry['name']}.frameworks.{fw}: license missing", validate(data))

    def _svelte_variant(self, data):
        entry = next(e for e in data["showpiece"] if (e.get("frameworks") or {}).get("svelte"))
        return entry, entry["frameworks"]["svelte"]

    def test_svelte_variants_use_registry_item(self):
        data = registry()
        variants = [e["frameworks"]["svelte"] for e in data["showpiece"] if (e.get("frameworks") or {}).get("svelte")]
        self.assertTrue(variants)
        self.assertTrue(all(v["fetch"]["method"] == "registry_item" for v in variants))

    def test_registry_item_ref_must_match_fetch(self):
        data = registry()
        entry, variant = self._svelte_variant(data)
        variant["ref"] = 'npx shadcn@latest add "%s"' % variant["fetch"]["url"]
        errors = validate(data)
        self.assertTrue(
            any(e.startswith(f"{entry['name']}.frameworks.svelte: ref does not match fetch") for e in errors), errors
        )

    def test_registry_item_rejects_cli(self):
        data = registry()
        entry, variant = self._svelte_variant(data)
        variant["fetch"]["cli"] = "shadcn"
        self.assertIn(
            f"{entry['name']}.frameworks.svelte: fetch.cli is only meaningful for method 'registry_cli'",
            validate(data),
        )

    def test_placeholder_license_fails(self):
        data = registry()
        data["showpiece"][0]["license"] = "TBD"
        name = data["showpiece"][0]["name"]
        self.assertTrue(any(e.startswith(f"{name}: license is a placeholder") for e in validate(data)))


if __name__ == "__main__":
    unittest.main()
