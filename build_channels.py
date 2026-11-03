#!/usr/bin/env python3
"""Extrae las emisiones deportivas de la guía de TV de España y genera channels.json para la app Onscreen Sports.

Fuente: guía XMLTV de EPG_dobleM (https://github.com/davidmuma/EPG_dobleM), con la programación
de los canales españoles (Movistar Plus+, DAZN, Eurosport, Teledeporte, Red Bull TV...).

Uso:
    python3 build_channels.py public/channels.json            # descarga la guía
    python3 build_channels.py public/channels.json guia.xml   # usa un archivo local
"""

import gzip
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

GUIDE_URL = "https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml.gz"

# Canales sin categoría en la guía que también nos interesan, con el deporte que detectamos por el título.
UNCATEGORIZED = {"Red Bull TV": [(re.compile(r"p[aá]del", re.I), "Pádel")]}

SEASON = re.compile(r"\s+T\d{2,4}(?:/\d{2})?(?:\s+E\d+)?\s*$")
# "Jornada 11: RC Deportivo - CA Osasuna", "Noviembre: Thunder @ Cavaliers", "Final: Coello/Tapia - Tello/Arce"
MATCHUP = re.compile(r"^(?:(?P<prefix>.*?):\s*)?(?P<a>[^:]+?)\s+(?P<sep>-|–|@|vs\.?)\s+(?P<b>[^:]+?)$")


def load_guide(path):
    if path:
        with open(path, "rb") as f:
            data = f.read()
    else:
        with urllib.request.urlopen(GUIDE_URL, timeout=120) as response:
            data = response.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return ET.fromstring(data)


def text(programme, tag):
    """Texto en inglés (sin las marcas de color de la versión en español)."""
    for element in programme.findall(tag):
        if element.get("lang") == "en":
            return (element.text or "").strip()
    element = programme.find(tag)
    return (element.text or "").strip() if element is not None else ""


def parse_time(value):
    return datetime.strptime(value, "%Y%m%d%H%M%S %z").astimezone(timezone.utc)


def clean_channel(name):
    return re.sub(r"\s+HD$", "", name)


def sport_of(channel, title, subtitle):
    """Deporte según la categoría ("Deportes,Fútbol | 2026 | TP"), o None si no es una emisión deportiva."""
    if subtitle:
        categories = [c.strip() for c in subtitle.split("|")[0].split(",")]
        if categories[0] != "Deportes" or any(c.startswith("Programa") for c in categories):
            return None  # previas, magacines y programas de tertulia
        return categories[1] if len(categories) > 1 else "Deportes"
    for pattern, sport in UNCATEGORIZED.get(channel, []):
        if pattern.search(title):
            return sport
    return None


def parse_title(title):
    """Separa competición y enfrentamiento. Devuelve (competición, local, visitante, detalle)."""
    parts = [SEASON.sub("", p).strip() for p in title.split(" · ", 1)]
    for index, part in enumerate(parts):
        match = MATCHUP.match(part)
        if not match:
            continue
        home, away = match.group("a").strip(), match.group("b").strip()
        if match.group("sep") == "@":  # formato NBA: visitante @ local
            home, away = away, home
        others = [p for i, p in enumerate(parts) if i != index]
        competition = others[0] if others else (match.group("prefix") or "")
        return competition, home, away, match.group("prefix")
    return parts[0], None, None, parts[1] if len(parts) > 1 else None


def build(root, now):
    broadcasts = []
    since = now - timedelta(hours=24)
    for programme in root.iter("programme"):
        channel = programme.get("channel", "")
        if " · " in channel:  # canales de otros países ("FR · Eurosport 1")
            continue
        title = text(programme, "title")
        sport = sport_of(channel, title, text(programme, "sub-title"))
        if not sport:
            continue
        end = parse_time(programme.get("stop"))
        if end < since:
            continue

        live = title.startswith("DIRECTO ")
        if live:
            title = title[len("DIRECTO "):]
        competition, home, away, detail = parse_title(title)

        entry = {
            "ch": clean_channel(channel),
            "start": parse_time(programme.get("start")).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "live": live,
            "sport": sport,
            "comp": competition,
        }
        if home and away:
            entry["home"], entry["away"] = home, away
        if detail:
            entry["detail"] = detail
        broadcasts.append(entry)

    broadcasts.sort(key=lambda b: (b["start"], b["ch"]))
    return broadcasts


def main():
    output = sys.argv[1]
    root = load_guide(sys.argv[2] if len(sys.argv) > 2 else None)
    now = datetime.now(timezone.utc)
    broadcasts = build(root, now)
    with open(output, "w", encoding="utf-8") as f:
        json.dump({"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": GUIDE_URL, "broadcasts": broadcasts},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(broadcasts)} emisiones deportivas -> {output}")


if __name__ == "__main__":
    main()
