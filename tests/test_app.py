"""Run with: python -m unittest discover -s tests -p test_*.py."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def run_app(self, overrides=None):
        original = Path.read_text
        overrides = overrides or {}

        def read_text(path, *args, **kwargs):
            if path.resolve().parent == ROOT and path.name in overrides:
                return json.dumps(overrides[path.name])
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", read_text):
            return AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)

    def test_app_starts_with_local_assets(self):
        app = self.run_app()
        self.assertFalse(app.exception, list(app.exception))
        for name in ("character.svg", "money.svg", "earth.svg"):
            ET.parse(ROOT / "assets" / name)

    def test_duplicate_quote_is_rejected(self):
        quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
        quotes[1]["text"] = quotes[0]["text"].upper()
        app = self.run_app({"quotes.json": quotes})
        self.assertEqual(len(app.exception), 1)
        self.assertIn("unique across the entire round", app.exception[0].message)

    def test_insufficient_quotes_for_round_are_rejected(self):
        config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        config["max_bills"] += 1
        app = self.run_app({"config.json": config})
        self.assertEqual(len(app.exception), 1)
        self.assertIn("Not enough unique quotes", app.exception[0].message)


if __name__ == "__main__":
    unittest.main()
