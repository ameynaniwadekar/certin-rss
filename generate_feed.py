import os
import json
import pandas as pd
import requests

from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

URL = "https://www.cert-in.org.in/s2cMainServlet?pageid=VLNLIST02&year=2026"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_DIR = "docs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Downloading CERT-In page...")

response = requests.get(URL, headers=HEADERS, timeout=30)
response.raise_for_status()

print("Status:", response.status_code)

soup = BeautifulSoup(response.text, "lxml")

records = []

#########################################################################
# Parse all table rows
#########################################################################

tables = soup.find_all("table")

for table in tables:

    rows = table.find_all("tr")

    for row in rows:

        cols = row.find_all("td")

        if len(cols) < 3:
            continue

        try:

            date = cols[0].get_text(" ", strip=True)

            anchor = cols[1].find("a")

            if anchor:

                title = anchor.get_text(" ", strip=True)

                href = anchor.get("href", "")

                if href.startswith("http"):
                    link = href
                else:
                    link = requests.compat.urljoin(URL, href)

            else:
                title = cols[1].get_text(" ", strip=True)
                link = URL

            civn = cols[2].get_text(" ", strip=True)

            if not civn:
                continue

            records.append({
                "CIVN": civn,
                "Date": date,
                "Title": title,
                "URL": link
            })

        except Exception:
            pass

#########################################################################
# Remove duplicates
#########################################################################

unique = []

seen = set()

for r in records:

    if r["CIVN"] in seen:
        continue

    seen.add(r["CIVN"])

    unique.append(r)

records = unique

print("Advisories found:", len(records))

#########################################################################
# JSON
#########################################################################

json_file = os.path.join(OUTPUT_DIR, "advisories.json")

with open(json_file, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=4)

#########################################################################
# CSV
#########################################################################

csv_file = os.path.join(OUTPUT_DIR, "advisories.csv")

pd.DataFrame(records).to_csv(csv_file, index=False)

#########################################################################
# RSS
#########################################################################

fg = FeedGenerator()

fg.id(URL)

fg.title("CERT-In Vulnerability Feed")

fg.link(href=URL)

fg.description("Unofficial CERT-In Vulnerability RSS Feed")

fg.language("en")

for item in records:

    fe = fg.add_entry()

    fe.id(item["CIVN"])

    fe.title(f"{item['CIVN']} - {item['Title']}")

    fe.link(href=item["URL"])

    fe.description(
        f"""
CIVN: {item['CIVN']}

Date: {item['Date']}

Title: {item['Title']}

Reference:
{item['URL']}
"""
    )

rss_file = os.path.join(OUTPUT_DIR, "feed.xml")

fg.rss_file(rss_file)

#########################################################################
# previous.json
#########################################################################

with open("previous.json", "w") as f:
    json.dump([x["CIVN"] for x in records], f, indent=4)

#########################################################################

print()

print("RSS Generated :", rss_file)

print("JSON Generated:", json_file)

print("CSV Generated :", csv_file)

print("Done.")
