from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import time

def scrape_transfermarkt_stats(stat_type: str, season_start: int, season_end: int, db_path: str):
    base_urls = {
        'goals': 'https://www.transfermarkt.us/premier-league/torschuetzenliste/wettbewerb/GB1/plus/?saison_id={}',
        'assists': 'https://www.transfermarkt.com/premier-league/assistliste/wettbewerb/GB1/plus/?saison_id={}'
    }

    if stat_type not in base_urls:
        raise ValueError("Invalid stat_type. Choose 'goals' or 'assists'.")

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            name TEXT,
            goals INTEGER,
            assists INTEGER,
            season INTEGER,
            PRIMARY KEY (name, season)
        )
    ''')

    for year in range(season_start, season_end + 1):
        url = base_urls[stat_type].format(year)
        print(f"Loading: {url}")
        driver.get(url)

        # Accept popup if present
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept & continue')]"))
            ).click()
            print("Accepted cookie popup.")
        except TimeoutException:
            print("No popup to accept.")

        # Wait until the stats table is present
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
            )
        except TimeoutException:
            print(f"Timeout waiting for table in season {year}. Skipping.")
            continue

        rows = driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr")

        for row in rows:
            try:
                # Only rows with "inline-table" have player data
                player_table = row.find_element(By.CSS_SELECTOR, "table.inline-table")
                name = player_table.find_element(By.CSS_SELECTOR, "td.hauptlink a").text.strip()

                stats_cells = row.find_elements(By.CSS_SELECTOR, "td.zentriert")
                if not stats_cells:
                    raise ValueError("No stat cells found.")

                raw_value = stats_cells[-1].text.strip()
                value = int(raw_value) if raw_value.isdigit() else 0

                if stat_type == "goals":
                    cursor.execute('''
                        INSERT INTO player_stats (name, goals, season)
                        VALUES (?, ?, ?)
                        ON CONFLICT(name, season) DO UPDATE SET goals=excluded.goals
                    ''', (name, value, year + 1))
                else:
                    cursor.execute('''
                        INSERT INTO player_stats (name, assists, season)
                        VALUES (?, ?, ?)
                        ON CONFLICT(name, season) DO UPDATE SET assists=excluded.assists
                    ''', (name, value, year + 1))

            except (NoSuchElementException, ValueError, IndexError) as e:
                print(f"Skipping row due to error: {e}")

    conn.commit()
    conn.close()
    driver.quit()

if __name__ == '__main__':
    db_path = "../data/fifa_player_stats.db"
    scrape_transfermarkt_stats("goals", 2014, 2022, db_path)
    scrape_transfermarkt_stats("assists", 2014, 2022, db_path)
