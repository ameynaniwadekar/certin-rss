
#!/usr/bin/env python3
"""
generate_feed.py
CERT-In Vulnerability Notes RSS Generator

NOTE:
This is a production-oriented skeleton based on the uploaded CERT-In HTML
structure. Replace LIST_URL if CERT-In changes the endpoint.
"""

import csv
import json
import logging
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

BASE_URL = "https://www.cert-in.org.in"
LIST_URL = BASE_URL + "/s2cMainServlet?pageid=PUBVLNLIST"

OUT_DIR = Path("docs")
OUT_DIR.mkdir(exist_ok=True)

RSS_FILE = OUT_DIR / "feed.xml"
JSON_FILE = OUT_DIR / "advisories.json"
CSV_FILE = OUT_DIR / "advisories.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def parse_list(html):
    soup = BeautifulSoup(html, "html.parser")

    advisories = []
    current_date = None

    for tr in soup.find_all("tr"):
        date_span = tr.find("span", class_="DateContent")
        if date_span:
            current_date = date_span.get_text(strip=True).strip("()")
            continue

        a = tr.find("a", href=lambda h: h and "PUBVLNOTES01" in h)
        if not a:
            continue

        href = a["href"]
        if href.startswith("/"):
            href = BASE_URL + href

        civn = href.split("VLCODE=")[-1]

        title = a.get_text(" ", strip=True)

        advisories.append({
            "id": civn,
            "title": title,
            "date": current_date,
            "url": href,
        })

    return advisories


def parse_detail(item):
    try:
        html = get(item["url"])
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(soup.stripped_strings)
        item["description"] = text[:4000]
    except Exception as exc:
        logging.warning("Failed %s: %s", item["id"], exc)
        item["description"] = ""

    return item


def write_json(items):
    JSON_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def write_csv(items):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "date", "title", "url", "description"],
        )
        w.writeheader()
        w.writerows(items)


def write_rss(items):
    fg = FeedGenerator()
    fg.title("CERT-In Vulnerability Notes")
    fg.link(href=LIST_URL)
    fg.description("Generated CERT-In RSS Feed")

    for item in items:
        fe = fg.add_entry()
        fe.guid(item["url"], permalink=True)
        fe.id(item["url"])
        fe.title(item["title"])
        fe.link(href=item["url"])
        fe.description(item["description"])

        try:
            dt = datetime.strptime(item["date"], "%B %d, %Y")
        except Exception:
            dt = datetime.utcnow()

        fe.pubDate(format_datetime(dt))

    fg.rss_file(str(RSS_FILE))


def main():
    logging.info("Downloading list...")
    html = get(LIST_URL)

    items = parse_list(html)
    logging.info("Found %d advisories", len(items))

    items = [parse_detail(x) for x in items]

    write_json(items)
    write_csv(items)
    write_rss(items)

    logging.info("Done.")


if __name__ == "__main__":
    main()
