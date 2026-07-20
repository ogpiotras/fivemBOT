import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "magazyn.db"

ITEMY = [
    ("Gotówka", "💵"),
    ("Proch", "🧨"),
    ("HK P7 M10", "🔫"),
    ("Ghost Gun", "🔫"),
    ("Heckler & Koch P7", "🔫"),
    ("Beretta M9", "🔫"),
    ("Beretta M92FS", "🔫"),
    ("Glock 17", "🔫"),
    ("Colt M1911A1", "🔫"),
    ("Desert Eagle .50AE", "🔫"),
    ("Smith & Wesson 629", "🔫"),
    ("Smith & Wesson 686", "🔫"),
    ("Glock 19C (switch)", "🔫"),
    ("VZ.61 Scorpion", "🔫"),
    ("Tec-9", "🔫"),
    ("IMI Uzi", "🔫"),
    ("Draco", "🔫"),
    ("Ak47", "🔫"),
    ("HK MP5", "🔫"),
    ("Remington 870", "🔫"),
    ("Mossberg 500", "🔫"),
    ("Dwururka", "🔫"),
    ("Koktajl Molotova", "🔥"),
    ("Wkład Balistyczny", "🪖"),
    ("Ammo 9mm", "📦"),
    ("Ammo 9mm HP", "📦"),
    ("Ammo .45 ACP", "📦"),
    ("Ammo .380 ACP", "📦"),
    ("Ammo .50 AE", "📦"),
    ("Ammo .44 Magnum", "📦"),
    ("Ammo .357 Magnum", "📦"),
    ("Ammo 12 Gauge", "📦"),
    ("Ammo 7.62", "📦"),
    ("Ammo 5.56", "📦"),
    ("Tlumik 01", "💀"),
    ("Tlumik", "💀"),
    ("Powiekszony magazynek", "💀"),
    ("Magazynek bebenkowy", "💀"),
    ("Celownik do broni", "💀"),
    ("LSD Hefalump", "💊"),
    ("LSD Tromba", "💊"),
    ("Fentanyl", "💊"),
    ("Blue Monarch", "💊"),
    ("Crack", "💊"),
    ("Koks 100%", "💊"),
    ("Koks 70%", "💊")
]

NAZWY_ITEMOW = [nazwa for nazwa, _ in ITEMY]


def polacz():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = polacz()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS itemy (
            guild_id INTEGER NOT NULL,
            nazwa    TEXT    NOT NULL,
            ilosc    INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, nazwa)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historia (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id  INTEGER NOT NULL,
            user_id   INTEGER NOT NULL,
            user_tag  TEXT    NOT NULL,
            nazwa     TEXT    NOT NULL,
            zmiana    INTEGER NOT NULL,
            ilosc_po  INTEGER NOT NULL,
            powod TEXT,
            czas      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    cursor = conn.execute("PRAGMA table_info(historia)")
    kolumny = [row["name"] for row in cursor.fetchall()]

    if "powod" not in kolumny:
        print("Migracja bazy: Dodaję brakującą kolumnę 'powod'...")
        conn.execute("ALTER TABLE historia ADD COLUMN powod TEXT")

    conn.commit()
    conn.close()


def get_stan(guild_id: int) -> dict:
    conn = polacz()
    rows = conn.execute(
        "SELECT nazwa, ilosc FROM itemy WHERE guild_id = ?", (guild_id,)
    ).fetchall()
    conn.close()
    z_bazy = {row["nazwa"]: row["ilosc"] for row in rows}
    return {nazwa: z_bazy.get(nazwa, 0) for nazwa in NAZWY_ITEMOW}


def zmien_ilosc(guild_id, user_id, user_tag, nazwa, delta, powod=None):
    if nazwa not in NAZWY_ITEMOW:
        return (False, None)

    conn = polacz()
    row = conn.execute(
        "SELECT ilosc FROM itemy WHERE guild_id = ? AND nazwa = ?",
        (guild_id, nazwa),
    ).fetchone()
    obecna = row["ilosc"] if row else 0
    nowa = obecna + delta

    if nowa < 0:
        conn.close()
        return (False, obecna)

    conn.execute(
        """INSERT INTO itemy (guild_id, nazwa, ilosc) VALUES (?, ?, ?)
           ON CONFLICT(guild_id, nazwa) DO UPDATE SET ilosc = excluded.ilosc""",
        (guild_id, nazwa, nowa),
    )
    conn.execute(
        """INSERT INTO historia (guild_id, user_id, user_tag, nazwa, zmiana, ilosc_po, powod)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (guild_id, user_id, user_tag, nazwa, delta, nowa, powod),
    )
    conn.commit()
    conn.close()
    return (True, nowa)


def get_historia(guild_id: int, limit: int = 30):
    conn = polacz()
    rows = conn.execute(
        """SELECT user_tag, nazwa, zmiana, ilosc_po, powod, czas
           FROM historia WHERE guild_id = ?
           ORDER BY id DESC LIMIT ?""",
        (guild_id, limit),
    ).fetchall()
    conn.close()
    return rows