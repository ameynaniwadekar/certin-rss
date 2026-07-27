#!/usr/bin/env python3
import csv,json,logging,re
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

BASE="https://www.cert-in.org.in"
LIST_URL=BASE+"/s2cMainServlet?pageid=VLNLIST"
OUT=Path("docs"); OUT.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)

def fetch(url):
    r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    return r.text

def parse_list(html):
    soup=BeautifulSoup(html,"html.parser")
    items=[]
    for tbl in soup.find_all("table",class_="content"):
        a=tbl.find("a",href=lambda h:h and "PUBVLNOTES01" in h)
        if not a:
            continue
        href=a["href"].replace("&amp;","&")
        if href.startswith("/"): href=BASE+href
        date=""
        ds=tbl.find("span",class_="DateContent")
        if ds:
            date=" ".join(ds.get_text(" ",strip=True).replace("(","").replace(")","").split())
        title=""
        for sp in tbl.find_all("span"):
            txt=" ".join(sp.get_text(" ",strip=True).split())
            if txt and "CERT-In Vulnerability Note" not in txt and "DateContent" not in " ".join(sp.get("class",[])):
                if len(txt)>5:
                    title=txt
        if not title:
            div=tbl.find("div")
            if div: title=" ".join(div.get_text(" ",strip=True).split())
        m=re.search(r'VLCODE=([^&]+)',href)
        cid=m.group(1) if m else href
        items.append({"id":cid,"title":title,"date":date,"url":href})
    return items

def parse_detail(item):
    try:
        s=BeautifulSoup(fetch(item["url"]),"html.parser")
        body=" ".join(s.stripped_strings)
        item["description"]=body[:5000]
    except Exception as e:
        item["description"]=str(e)
    return item

def write(items):
    (OUT/"advisories.json").write_text(json.dumps(items,indent=2),encoding="utf-8")
    with open(OUT/"advisories.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["id","date","title","url","description"])
        w.writeheader();w.writerows(items)
    fg=FeedGenerator()
    fg.title("CERT-In Vulnerability Notes")
    fg.link(href=LIST_URL)
    fg.description("CERT-In Vulnerability Notes RSS")
    for it in items:
        e=fg.add_entry()
        e.guid(it["url"],permalink=True)
        e.id(it["url"])
        e.title(f'{it["id"]} - {it["title"]}')
        e.link(href=it["url"])
        e.description(it["description"])
        try:
            d=datetime.strptime(it["date"],"%B %d, %Y")
            e.pubDate(d)
        except: pass
    fg.rss_file(str(OUT/"feed.xml"))

def main():
    html=fetch(LIST_URL)
    items=parse_list(html)
    logging.info("Found %d advisories",len(items))
    items=[parse_detail(i) for i in items]
    write(items)

if __name__=="__main__":
    main()
