import requests
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import date

# --------------------------------------------------------------------------- #
# ------------------------------  CORE HELPERS  ----------------------------- #
# --------------------------------------------------------------------------- #
HEADERS = {"User-Agent": "Mozilla/5.0"}

def build_url(stat_type: str, season: int) -> str:
    base_urls = {
        "goals":   "https://www.transfermarkt.us/premier-league/torschuetzenliste/wettbewerb/GB1/plus/?saison_id={}",
        "assists": "https://www.transfermarkt.us/premier-league/assistliste/wettbewerb/GB1/plus/?saison_id={}",
    }
    return base_urls[stat_type].format(season)


def get_paginated_urls(soup) -> list[str]:
    links = []
    for li in soup.find_all("li", class_="tm-pagination__list-item")[1:]:
        a = li.find("a")
        if a and a.get("href"):
            links.append("https://www.transfermarkt.us" + a["href"])
    return links


def season_start(season: int) -> date:
    return date(season, 8, 1)          # 1 Aug of that season (kept for possible later use)


# --------------------------------------------------------------------------- #
# ---------------  PAGE‑LEVEL SCRAPE (now includes nat & age)  -------------- #
# --------------------------------------------------------------------------- #
def extract_stats_from_page(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    """
    Parse one Transfermarkt list page and return a DataFrame with columns:
        name • value • season • nationality • age
    Nationality (‘Nat.’ column) is given by the title of each flag; if a player
    shows several flags the titles are joined with “/”.  Age is the integer in
    the ‘Age’ column.  ‘value’ is the goals or assists number (last numeric col).
    """
    table = soup.find("table", class_="items")
    if not table:
        return pd.DataFrame(
            columns=["name", "value", "season", "nationality", "age"]
        )

    rows = []
    for tr in table.select("tbody > tr"):
        name_td = tr.find("td", class_="hauptlink")
        stat_tds = tr.find_all("td", class_="zentriert")

        # sanity checks -----------------------------------------------------
        if not name_td or len(stat_tds) < 6:
            continue

        # player name & url -------------------------------------------------
        a_tag = name_td.find("a")
        if not a_tag:
            continue
        name = (a_tag.get("title") or a_tag.text).strip()

        # nationality -------------------------------------------------------
        nat_td = stat_tds[1]                 # [0]=rank, [1]=Nat., [2]=Age, ...
        nat_titles = [
            img.get("title").strip()
            for img in nat_td.find_all("img")
            if img.get("title")
        ]
        nationality = "/".join(nat_titles) if nat_titles else None

        # age ---------------------------------------------------------------
        age_td = stat_tds[2]
        age_text = age_td.get_text(strip=True)
        age = int(age_text) if age_text.isdigit() else None

        # goals / assists value (last numeric col) -------------------------
        value_text = stat_tds[-1].get_text(strip=True)
        if not value_text.isdigit():
            continue
        value = int(value_text)

        rows.append(
            (
                name,
                value,
                (season % 2000) + 1,         # store as 15 for 2014/15 etc.
                nationality,
                age,
            )
        )

    return pd.DataFrame(
        rows, columns=["name", "value", "season", "nationality", "age"]
    )


# --------------------------------------------------------------------------- #
# ----------------------------  DB UTILITIES  ------------------------------- #
# --------------------------------------------------------------------------- #
def ensure_table_schema(cursor: sqlite3.Cursor, table: str):
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            name TEXT,
            value INTEGER,
            season INTEGER,
            nationality TEXT,
            age INTEGER,
            PRIMARY KEY (name, season)
        )
    """
    )


def insert_data_to_db(df: pd.DataFrame, db_path: str, table: str):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        ensure_table_schema(cur, table)

        records = df.to_records(index=False)
        cur.executemany(
            f"""
            INSERT INTO {table} (name, value, season, nationality, age)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name, season) DO UPDATE
               SET value        = excluded.value,
                   nationality  = COALESCE(excluded.nationality, {table}.nationality),
                   age          = COALESCE(excluded.age, {table}.age)
        """,
            records,
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# -------------------------  SEASON‑LEVEL SCRAPER  -------------------------- #
# --------------------------------------------------------------------------- #
def scrape_season(stat_type: str, season: int) -> pd.DataFrame:
    print(f"  ↳ fetching {stat_type} {season}/{season+1} …")
    url = build_url(stat_type, season)
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=30).text, "html.parser")

    # first page
    df = extract_stats_from_page(soup, season)

    # paginated pages
    for page_url in get_paginated_urls(soup):
        soup_p = BeautifulSoup(requests.get(page_url, headers=HEADERS, timeout=30).text, "html.parser")
        df = pd.concat([df, extract_stats_from_page(soup_p, season)], ignore_index=True)

    return df.drop_duplicates(subset=["name", "season"])


def scrape_and_save(stat_type: str, start: int, end: int, db_path: str, table_suffix: str = "_plus"):
    table_name = stat_type + table_suffix
    for season in range(start, end + 1):
        try:
            df = scrape_season(stat_type, season)
            insert_data_to_db(df, db_path, table_name)
        except Exception as exc:
            print(f"⚠️  {table_name} {season}/{season+1} failed → {exc}")


# --------------------------------------------------------------------------- #
# -----------------------------  MAIN  ENTRY  ------------------------------- #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    DB_PATH = "../data/fifa_players.db"            # change if necessary
    scrape_and_save("goals",   2014, 2022, DB_PATH)    # → goals_plus
    scrape_and_save("assists", 2014, 2022, DB_PATH)    # → assists_plus
