#!/usr/bin/env python3

import json
import sqlite3
import hashlib
from datetime import datetime, timezone

DB = "autowork.db"
FILE = "external_projects.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def main():

    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])

    con = sqlite3.connect(DB)

    cols = {
        r[1]
        for r in con.execute(
            "PRAGMA table_info(tasks)"
        ).fetchall()
    }

    inserted = 0

    for j in jobs:

        source = "external_" + str(j["source"]).lower()
        task_id = j["id"]

        values = {
            "source": source,
            "task_id": task_id,
            "title": j["title"][:500],
            "reward": 0,
            "status": "discovered",
            "task_type": "regional_project",
            "region": j["region"],
            "listing_url": j["url"],
            "raw_json": json.dumps(
                j,
                ensure_ascii=False,
            )[:15000],
            "contact_status": "ready",
            "application_status": "not_contacted",
            "discovered_at": j.get(
                "discovered_at",
                now(),
            ),
            "created_at": now(),
            "updated_at": now(),
        }

        values = {
            k: v
            for k, v in values.items()
            if k in cols
        }

        fields = ",".join(values)
        marks = ",".join(["?"] * len(values))

        before = con.total_changes

        con.execute(
            f"""
            INSERT OR IGNORE INTO tasks
            ({fields})
            VALUES ({marks})
            """,
            list(values.values()),
        )

        if con.total_changes > before:
            inserted += 1

    con.commit()

    queue = con.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='discovered'
          AND application_status='not_contacted'
    """).fetchone()[0]

    print("=" * 60)
    print("EXTERNAL PROJECT IMPORT")
    print("=" * 60)
    print("DOWNLOADED :", len(jobs))
    print("INSERTED   :", inserted)
    print("QUEUE      :", queue)

    con.close()

if __name__ == "__main__":
    main()
