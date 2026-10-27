"""Maximum Motivation — finite rounds, escalating coach and planetary finale."""

import json
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st
from streamlit.components.v1 import declare_component

ROOT = Path(__file__).resolve().parent


def load_config():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config.json must contain an object")
    for key in ("max_bills", "max_visible_flights"):
        if type(config.get(key)) is not int or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    levels = config.get("levels")
    if not isinstance(levels, list) or len(levels) != 4:
        raise ValueError("Provide the four character levels")
    for index, (level, key) in enumerate(zip(levels, ("believer", "hustler", "maniac", "maximum"))):
        if (not isinstance(level, dict) or level.get("id") != index + 1
                or level.get("key") != key
                or type(level.get("from_hit")) is not int
                or not 1 <= level["from_hit"] <= config["max_bills"]
                or not isinstance(level.get("label"), str) or not level["label"].strip()
                or not isinstance(level.get("status"), str) or not level["status"].strip()
                or type(level.get("duration_seconds")) not in (int, float)
                or not 0 < level["duration_seconds"] <= 10):
            raise ValueError("Invalid character level configuration")
    starts = [level["from_hit"] for level in levels]
    if starts[0] != 1 or starts != sorted(set(starts)):
        raise ValueError("Level boundaries must start at 1 and increase strictly")
    return config


def load_quotes(config):
    """Validate local content before handing it to the game component."""
    quotes = json.loads((ROOT / "quotes.json").read_text(encoding="utf-8"))
    identifiers = set()
    texts = set()
    counts = {level: 0 for level in range(1, 5)}
    if not isinstance(quotes, list):
        raise ValueError("quotes.json must contain a list")
    for quote in quotes:
        if (not isinstance(quote, dict)
                or not isinstance(quote.get("id"), str) or not quote["id"]
                or quote["id"] in identifiers
                or type(quote.get("level")) is not int or quote["level"] not in counts
                or not isinstance(quote.get("text"), str) or not quote["text"].strip()
                or not isinstance(quote.get("author"), str) or not quote["author"].strip()
                or not isinstance(quote.get("source_url"), str)):
            raise ValueError("Each quote needs a unique id, text, author, source_url and integer level 1–4")
        source = urlsplit(quote["source_url"])
        if source.scheme != "https" or not source.netloc:
            raise ValueError("Quote source_url must be an absolute HTTPS URL")
        identifiers.add(quote["id"])
        normalized_text = " ".join(quote["text"].casefold().split())
        if normalized_text in texts:
            raise ValueError("Quote texts must be unique across the entire round")
        texts.add(normalized_text)
        counts[quote["level"]] += 1
    for index, level in enumerate(config["levels"]):
        end = (config["levels"][index + 1]["from_hit"] - 1
               if index + 1 < len(config["levels"]) else config["max_bills"])
        if counts[level["id"]] < end - level["from_hit"] + 1:
            raise ValueError(f"Not enough unique quotes for level {level['id']}")
    return quotes

st.set_page_config(page_title="Maximum Motivation", page_icon="⚡", layout="wide")

# Keep the host out of the stage. The component owns all visible controls.
st.html("""<style>
html, body, [data-testid="stAppViewContainer"] { background: #f2eedf; }
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer { display: none; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none; }
[data-testid="stMain"] { overflow: hidden; }
[data-testid="stElementContainer"]:has(iframe) { height: 100dvh; }
[data-testid="stMain"] iframe {
    display: block; width: 100%; height: 100dvh !important; border: 0;
}
</style>
""")

coach = declare_component("coach", path=str(ROOT / "frontend"))
config = load_config()
coach(character_svg=(ROOT / "assets" / "character.svg").read_text(encoding="utf-8"),
      money_svg=(ROOT / "assets" / "money.svg").read_text(encoding="utf-8"),
      earth_svg=(ROOT / "assets" / "earth.svg").read_text(encoding="utf-8"),
      quotes=load_quotes(config), config=config, key="visual-prototype", default=None)
