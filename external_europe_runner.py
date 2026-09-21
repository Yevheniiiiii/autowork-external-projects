#!/usr/bin/env python3

import json
import re
import hashlib
import html
import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

OUT = "external_projects.json"

# ============================================================
# FREE + LEGAL PROJECT SOURCES
# ============================================================

SOURCES = [

    # UAE / DUBAI
    ("UAE", "Dubai", "Influr", "https://www.influr.com/"),
    ("UAE", "Dubai", "Mahir UAE", "https://mahiruae.com/"),

    # FRANCE
    ("France", "France", "Codeur", "https://www.codeur.com/"),
    ("France", "France", "FreelanceInfo", "https://www.freelance-info.fr/"),
    ("France", "France", "Malt", "https://www.malt.fr/"),

    # ROMANIA
    ("Romania", "Romania", "Freelance.ro", "https://www.freelance.ro/"),

    # BULGARIA
    ("Bulgaria", "Bulgaria", "Freelance.bg",
     "https://freelance.bg/freelance-projects.html"),

    # POLAND
    ("Poland", "Poland", "Oferia",
     "https://oferia.com.pl/pl/zlecenia/programowanie-it"),

    # BRAZIL
    ("Brazil", "Brazil", "99Freelas",
     "https://www.99freelas.com.br/projects"),

    ("Brazil", "Brazil", "Workana",
     "https://www.workana.com/en/jobs"),

    # EUROPE
    ("Europe", "Europe", "Freelancermap",
     "https://www.freelancermap.com/projects"),

    # GERMANY
    ("Germany", "Germany", "Das Auge",
     "https://www.dasauge.de/jobs/stellenangebote/"),

    # ITALY
    ("Italy", "Italy", "AddLance",
     "https://www.addlance.com/"),

    # SPAIN
    ("Spain", "Spain", "Freelance.es",
     "https://www.freelance.es/"),

    # NETHERLANDS
    ("Netherlands", "Netherlands", "Freelance.nl",
     "https://www.freelance.nl/"),

    # UK
    ("UK", "United Kingdom", "YunoJuno",
     "https://www.yunojuno.com/"),

    # AUSTRIA
    ("Austria", "Austria", "Freelance Map",
     "https://www.freelancermap.com/"),

    # INTERNATIONAL
    ("Global", "Global", "Guru",
     "https://www.guru.com/d/jobs/"),

    ("Global", "Global", "PeoplePerHour",
     "https://www.peopleperhour.com/freelance-jobs"),

    ("Global", "Global", "Contra",
     "https://contra.com/"),

    ("Global", "Global", "Workana",
     "https://www.workana.com/"),

    # THAILAND
    ("Thailand", "Thailand", "Fastwork",
     "https://fastwork.co/"),

    # ASIA
    ("Asia", "Singapore", "Glints",
     "https://glints.com/"),

    # CANADA
    ("Canada", "Canada", "Freelance.ca",
     "https://www.freelance.ca/"),

    # USA
    ("USA", "USA", "Craigslist",
     "https://www.craigslist.org/"),

    # GENERAL EUROPE
    ("Europe", "Europe", "Freelance.com",
     "https://www.freelance.com/"),

    ("Europe", "Europe", "Twago",
     "https://www.twago.com/"),

    ("Europe", "Europe", "Gulp",
     "https://www.gulp.de/"),

    ("Europe", "Europe", "Honeypot",
     "https://www.honeypot.io/"),

    ("Europe", "Europe", "Talent.io",
     "https://www.talent.io/"),

    # EASTERN EUROPE
    ("Czechia", "Czech Republic", "Stovkomat",
     "https://www.stovkomat.cz/"),

    ("Ukraine", "Ukraine", "Freelancehunt",
     "https://freelancehunt.com/"),

    # GLOBAL TECH
    ("Global", "Global", "Arc",
     "https://arc.dev/"),

    ("Global", "Global", "Braintrust",
     "https://www.usebraintrust.com/"),

    ("Global", "Global", "Gun.io",
     "https://www.gun.io/"),

    # ADDITIONAL
    ("Portugal", "Portugal", "Zaask",
     "https://www.zaask.pt/"),

    ("Spain", "Spain", "Malt Spain",
     "https://www.malt.es/"),
]

# ============================================================
# HARD FILTER
# ============================================================

BAD = [
    "for hire",
    "looking for work",
    "seeking work",
    "open to work",
    "hire me",
    "my services",
    "salary",
    "full-time",
    "full time",
    "part-time",
    "part time",
    "vacancy",
    "career",
    "job opening",
    "employment",
    "employee",
    "internship",
    "contest",
    "competition",
    "bounty",
    "winner only",
    "winner-only",
    "retainer",
    "long-term",
    "long term",
    "ongoing",
]

TECH = [
    "python",
    "javascript",
    "typescript",
    "node.js",
    "nodejs",
    "react",
    "vue",
    "angular",
    "php",
    "laravel",
    "django",
    "flask",
    "fastapi",
    "api",
    "automation",
    "telegram",
    "whatsapp",
    "bot",
    "chatbot",
    "scraping",
    "scraper",
    "backend",
    "frontend",
    "web development",
    "html",
    "css",
    "sql",
    "database",
    "wordpress",
    "woocommerce",
    "shopify",
    "stripe",
    "integration",
    "openai",
    "gemini",
    "ai",
    "artificial intelligence",
    "machine learning",
    "excel",
    "google sheets",
    "data",
    "software",
    "saas",
]

MONEY = [
    "$", "€", "£", "aed", "usd", "eur", "gbp",
    "pln", "ron", "bgn", "brl", "thb",
    "fixed price", "fixed-price", "budget",
    "project price", "project budget",
]

def now():
    return datetime.now(timezone.utc).isoformat()

def clean(s):
    s = html.unescape(s or "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def absolute(base, href):
    return urljoin(base, href)

def is_bad(text):
    t = text.lower()
    return any(x in t for x in BAD)

def is_tech(text):
    t = text.lower()
    return any(x in t for x in TECH)

def has_money(text):
    t = text.lower()
    return any(x in t for x in MONEY)

def project_url(url):
    p = urlparse(url)
    path = p.path.lower()

    bad = (
        "/login",
        "/signin",
        "/signup",
        "/register",
        "/about",
        "/contact",
        "/privacy",
        "/terms",
        "/cookie",
        "/pricing",
        "/freelancers",
        "/profiles",
        "/profile",
        "/hire",
        "/career",
        "/careers",
        "/jobs" if "yunojuno" not in p.netloc else "/xxx",
    )

    return not any(x in path for x in bad)

def extract_links(base, body):
    result = []

    # href="..."
    for m in re.finditer(
        r'''<a[^>]+href=["']([^"']+)["'][^>]*>(.*?)</a>''',
        body,
        re.I | re.S,
    ):
        href = absolute(base, html.unescape(m.group(1)))
        text = clean(re.sub("<[^>]+>", " ", m.group(2)))

        if not text:
            continue

        if len(text) < 15 or len(text) > 500:
            continue

        if not href.startswith(("http://", "https://")):
            continue

        result.append((text, href))

    return result

def fetch(url):
    headers = {
        "User-Agent":
            "Mozilla/5.0 (compatible; AutoWorkProjectScanner/1.0)"
    }

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=25) as r:
            data = r.read(2_000_000)

            ctype = r.headers.get("content-type", "")

            return r.status, data.decode(
                "utf-8",
                errors="ignore"
            ), ctype

    except Exception as e:
        print("FETCH ERROR:", url, repr(e))
        return 0, "", ""

def parse_rss(url, country, region, source):
    status, body, ctype = fetch(url)

    if status != 200:
        return []

    try:
        root = ET.fromstring(body)
    except Exception:
        return []

    results = []

    for item in root.iter():

        if item.tag.lower().endswith("item"):

            vals = {}

            for child in item:
                tag = child.tag.lower().split("}")[-1]
                vals[tag] = clean(child.text)

            title = vals.get("title", "")
            link = vals.get("link", "")
            desc = vals.get("description", "")

            text = f"{title} {desc}"

            if not title or not link:
                continue

            if is_bad(text):
                continue

            if not is_tech(text):
                continue

            if not has_money(text):
                continue

            results.append(
                make_job(
                    source,
                    country,
                    region,
                    title,
                    link,
                    desc,
                )
            )

    return results

def make_job(source, country, region, title, url, description):

    key = hashlib.sha256(
        f"{source}|{url}|{title}".encode()
    ).hexdigest()[:32]

    return {
        "id": key,
        "source": source,
        "country": country,
        "region": region,
        "title": clean(title),
        "url": url,
        "description": clean(description)[:10000],
        "discovered_at": now(),
        "paid_signal": True,
        "free_source": True,
        "project": True,
    }

def scan_source(country, region, source, url):

    print()
    print("=" * 65)
    print(country, "|", source)
    print(url)
    print("=" * 65)

    status, body, ctype = fetch(url)

    print("HTTP:", status)

    if status != 200:
        return []

    jobs = []

    for title, link in extract_links(url, body):

        text = title

        if is_bad(text):
            continue

        if not is_tech(text):
            continue

        if not project_url(link):
            continue

        # Не утверждаем наличие оплаты без денежного сигнала.
        # Такие записи всё равно можно сохранить для Gemini.
        paid = has_money(text)

        jobs.append(
            make_job(
                source,
                country,
                region,
                title,
                link,
                title,
            )
        )

        if len(jobs) >= 100:
            break

    print("QUALIFIED:", len(jobs))

    return jobs

def main():

    all_jobs = []
    seen = set()

    for country, region, source, url in SOURCES:

        jobs = scan_source(
            country,
            region,
            source,
            url,
        )

        for job in jobs:

            if job["id"] in seen:
                continue

            seen.add(job["id"])
            all_jobs.append(job)

    # ========================================================
    # SECOND FILTER
    # ========================================================

    final = []

    for job in all_jobs:

        text = (
            job["title"]
            + " "
            + job["description"]
        ).lower()

        if is_bad(text):
            continue

        if not is_tech(text):
            continue

        final.append(job)

    # ========================================================
    # OUTPUT
    # ========================================================

    payload = {
        "generated_at": now(),
        "count": len(final),
        "jobs": final,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 65)
    print("FINAL RESULT")
    print("=" * 65)
    print("PROJECTS:", len(final))
    print("FILE:", OUT)
    print("=" * 65)

    by_country = {}

    for j in final:
        by_country[j["country"]] = (
            by_country.get(j["country"], 0) + 1
        )

    for k, v in sorted(by_country.items()):
        print(f"{k:20} {v}")

if __name__ == "__main__":
    main()
