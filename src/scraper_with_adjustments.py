import requests, sqlite3, pandas as pd, random, time, sys, argparse, pathlib
from bs4 import BeautifulSoup
from datetime import date
from requests.adapters import HTTPAdapter, Retry

# --------------------------------------------------------------------------- #
# ------------------------------  GLOBAL SESSION  --------------------------- #
# --------------------------------------------------------------------------- #
HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=4, backoff_factor=1,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["GET"],
        )
    ),
)

def fetch(url: str, timeout: int = 15) -> str:
    """GET a page with retries + random delay to avoid rate‑limits."""
    print(f"     … {url}", flush=True)
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    finally:
        time.sleep(random.uniform(0.8, 1.6))


# --------------------------------------------------------------------------- #
# -----------------------------  URL UTILITIES  ----------------------------- #
# --------------------------------------------------------------------------- #
def build_url(stat_type: str, season: int) -> str:
    base = {
        "goals":   "https://www.transfermarkt.us/premier-league/torschuetzenliste/wettbewerb/GB1/plus/?saison_id={}",
        "assists": "https://www.transfermarkt.us/premier-league/assistliste/wettbewerb/GB1/plus/?saison_id={}",
    }
    return base[stat_type].format(season)

def get_paginated_urls(soup):
    return [
        "https://www.transfermarkt.us" + a["href"]
        for li in soup.select("li.tm-pagination__list-item")[1:]
        if (a := li.find("a")) and a.get("href")
    ]


# --------------------------------------------------------------------------- #
# ---------------------  TABLE‑PAGE   →   DATAFRAME  ------------------------ #
# --------------------------------------------------------------------------- #
def extract_stats_from_page(soup: BeautifulSoup, season: int) -> pd.DataFrame:
    """Return DF with: name • value • season • nationality • age"""
    table = soup.find("table", class_="items")
    if not table:
        return pd.DataFrame(columns=["name", "value", "season", "nationality", "age"])

    rows = []
    for tr in table.select("tbody > tr"):
        name_td = tr.find("td", class_="hauptlink")
        stat_tds = tr.find_all("td", class_="zentriert")
        if not name_td or len(stat_tds) < 6:
            continue

        name = (a := name_td.find("a")) and (a.get("title") or a.text).strip()
        if not name:
            continue

        nats = [img["title"].strip()
                for img in stat_tds[1].find_all("img")
                if img.get("title")]
        nationality = "/".join(nats) if nats else None

        age_txt = stat_tds[2].get_text(strip=True)
        age = int(age_txt) if age_txt.isdigit() else None

        value_txt = stat_tds[-1].get_text(strip=True)
        if not value_txt.isdigit():
            continue
        value = int(value_txt)

        rows.append((name, value, (season % 2000) + 1, nationality, age))

    return pd.DataFrame(rows,
                        columns=["name", "value", "season", "nationality", "age"])


# --------------------------------------------------------------------------- #
# -----------------------------  DB UTILITIES  ------------------------------ #
# --------------------------------------------------------------------------- #
def ensure_table(cur, table: str):
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS {table} (
            name TEXT,
            value INTEGER,
            season INTEGER,
            nationality TEXT,
            age INTEGER,
            PRIMARY KEY (name, season)
        )"""
    )

def pythonify(df: pd.DataFrame) -> pd.DataFrame:
    """Cast numeric cols to *Python* ints & drop in‑DF dups."""
    df = df.copy()
    for col in ["value", "season", "age"]:
        df[col] = df[col].astype("Int64").astype(object)
    return df.drop_duplicates(subset=["name", "season"])


def insert_df(df: pd.DataFrame, db: str, table: str):
    df = pythonify(df)
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        ensure_table(cur, table)

        # dedupe any pre‑existing duplicates in the table ------------------
        cur.execute(
            f"""
            DELETE FROM {table}
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM {table} GROUP BY name, season
            )
        """
        )

        cur.executemany(
            f"""
            INSERT INTO {table} (name, value, season, nationality, age)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name, season) DO UPDATE SET
                value       = excluded.value,
                nationality = COALESCE(excluded.nationality, {table}.nationality),
                age         = COALESCE(excluded.age, {table}.age)
            """,
            list(df.itertuples(index=False, name=None)),
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# -----------------------------  TOP‑LEVEL LOOP  ---------------------------- #
# --------------------------------------------------------------------------- #
def scrape_season(stat_type: str, season: int) -> pd.DataFrame:
    print(f"  ↳ {stat_type} {season}/{season+1}")
    soup = BeautifulSoup(fetch(build_url(stat_type, season)), "html.parser")
    df = extract_stats_from_page(soup, season)

    for page_url in get_paginated_urls(soup):
        page = BeautifulSoup(fetch(page_url), "html.parser")
        df = pd.concat([df, extract_stats_from_page(page, season)], ignore_index=True)

    return pythonify(df)


def scrape_and_save(stat_type: str, first: int, last: int,
                    db: str, suffix: str = "_plus"):
    table = stat_type + suffix
    failed = []
    for yr in range(first, last + 1):
        try:
            insert_df(scrape_season(stat_type, yr), db, table)
        except Exception as e:
            print(f"⚠️  {table} {yr}/{yr+1} failed → {e}", file=sys.stderr)
            failed.append((stat_type, yr))
    if failed:
        print("\n❌  Still missing:", failed)


# --------------------------------------------------------------------------- #
# ---------------------------------  CLI  ----------------------------------- #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["goals", "assists", "both"],
                        default="both", help="what to scrape")
    parser.add_argument("start", nargs="?", type=int, default=2014)
    parser.add_argument("end",   nargs="?", type=int, default=2022)
    args = parser.parse_args()

    DB_PATH = pathlib.Path("../data/fifa_players.db")

    if args.only in ("goals", "both"):
        scrape_and_save("goals",   args.start, args.end, DB_PATH)
    if args.only in ("assists", "both"):
        scrape_and_save("assists", args.start, args.end, DB_PATH)
