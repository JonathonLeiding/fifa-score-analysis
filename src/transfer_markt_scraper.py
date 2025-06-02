import requests
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup


def build_url(stat_type: str, season: int) -> str:
    """Build URL for the given stat type and season."""
    base_urls = {
        'goals': 'https://www.transfermarkt.us/premier-league/torschuetzenliste/wettbewerb/GB1/plus/?saison_id={}',
        'assists': 'https://www.transfermarkt.us/premier-league/assistliste/wettbewerb/GB1/plus/?saison_id={}'
    }
    return base_urls[stat_type].format(season)


def get_paginated_urls(soup) -> list:
    """Extract all pagination URLs from the page soup."""
    paginations = soup.find_all('li', class_="tm-pagination__list-item")
    links = []
    for page in paginations[1:]:  # Skip the first page (already scraped)
        a_tag = page.find('a')
        if a_tag:
            links.append("https://www.transfermarkt.us" + a_tag.get('href'))
    return links


def extract_stats_from_page(soup, season: int) -> pd.DataFrame:
    """Extract player name and stat (goals or assists) from table rows."""
    table = soup.find("table", class_="items")
    if not table:
        return pd.DataFrame(columns=["name", "value", "season"])

    data = []
    for row in table.select("tbody > tr"):
        name_td = row.find("td", class_="hauptlink")
        stat_tds = row.find_all("td", class_="zentriert")

        if name_td and len(stat_tds) >= 1:
            name_tag = name_td.find("a")
            if name_tag:
                name = name_tag.get("title") or name_tag.text.strip()
                value_text = stat_tds[-1].text.strip()
                if value_text.isdigit():
                    data.append((name, int(value_text), (season % 2000) + 1))

    return pd.DataFrame(data, columns=["name", "value", "season"])



def create_table_if_not_exists(cursor, table: str):
    """Create table if it doesn't exist."""
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            name TEXT,
            value INTEGER,
            season INTEGER,
            PRIMARY KEY (name, season)
        )
    ''')


def insert_data_to_db(df: pd.DataFrame, db_path: str, table: str):
    """Insert DataFrame data into the specified table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_table_if_not_exists(cursor, table)

    for _, row in df.iterrows():
        cursor.execute(f'''
            INSERT INTO {table} (name, value, season)
            VALUES (?, ?, ?)
            ON CONFLICT(name, season) DO UPDATE SET value=excluded.value
        ''', (row['name'], row['value'], row['season']))

    conn.commit()
    conn.close()


def scrape_season(stat_type: str, season: int) -> pd.DataFrame:
    """Scrape a single season's data for the given stat type."""
    url = build_url(stat_type, season)
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")
    df = extract_stats_from_page(soup, season)

    for page_url in get_paginated_urls(soup):
        page = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(page.text, "html.parser")
        df = pd.concat([df, extract_stats_from_page(soup, season)], ignore_index=True)

    return df.drop_duplicates(subset=["name", "season"])


def scrape_and_save(stat_type: str, start: int, end: int, db_path: str):
    """Main control function to scrape multiple seasons and store to DB."""
    for season in range(start, end + 1):
        print(f"Scraping {stat_type} for {season}/{season + 1} season...")
        try:
            df = scrape_season(stat_type, season)
            insert_data_to_db(df, db_path, stat_type)
        except Exception as e:
            print(f"Failed to scrape {season}: {e}")


if __name__ == "__main__":
    DB_PATH = "../data/fifa_player_combined_stats.db"
    scrape_and_save("goals", 2014, 2022, DB_PATH)
    scrape_and_save("assists", 2014, 2022, DB_PATH)
