"""CivicLens — Seed demo data for seminar presentation.
Run: python seed_demo.py
Adds 6 realistic issues across Pune so Grid + Map + Stats look alive.
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DB = str(BASE_DIR / "civiclens.db")

DEMO = [
    ("Massive pothole near MG Road signal", "Deep pothole, 2ft wide near the signal. Two bikers skidded yesterday. Needs urgent filling before rains.", "pothole", 18.5196, 73.8550, "MG Road Signal, Pune", "Open", 24, 0),
    ("Garbage overflowing behind market", "Dustbins overflowing for 3 days, foul smell spreading. Stray dogs scattering waste on road.", "garbage", 18.5235, 73.8610, "Tulshibaug Market Lane, Pune", "In-Progress", 18, 1),
    ("Streetlights dead on FC Road stretch", "Entire 200m stretch dark after 7pm. Students feel unsafe walking back from classes.", "streetlight", 18.5260, 73.8415, "FC Road, Near College Gate, Pune", "Open", 31, 0),
    ("Water leakage near society tank", "Clean water leaking from main pipeline joint for 2 days. Thousands of litres wasted daily.", "water", 18.5150, 73.8490, "Kothrud Depot Corner, Pune", "In-Progress", 12, 2),
    ("Blocked drain flooding footpath", "Drain choked with plastic, footpath floods even in light rain. Mosquito breeding risk.", "drainage", 18.5310, 73.8665, "Station Road Underpass, Pune", "Resolved", 9, 5),
    ("Broken bench + litter in garden", "Park bench broken, litter scattered around swings. Kids play area needs cleanup.", "other", 18.5105, 73.8575, "Sarasbaug Garden Entry, Pune", "Resolved", 6, 6),
]

conn = sqlite3.connect(DB)
conn.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
        category TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
        address TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open',
        upvotes INTEGER NOT NULL DEFAULT 0, image_path TEXT,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    )
""")

existing = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
if existing > 0:
    print(f"DB already has {existing} issue(s). Skipping seed (delete civiclens.db to reseed).")
else:
    now = datetime.utcnow()
    for i, (title, desc, cat, lat, lng, addr, status, votes, days_ago) in enumerate(DEMO):
        ts = (now - timedelta(days=days_ago, hours=i)).isoformat()
        conn.execute(
            "INSERT INTO issues VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex[:8], title, desc, cat, lat, lng, addr, status, votes, None, ts, ts),
        )
    conn.commit()
    print(f"Seeded {len(DEMO)} demo issues into {DB}")

conn.close()
