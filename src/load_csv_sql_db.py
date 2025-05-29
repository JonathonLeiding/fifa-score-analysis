import pandas as pd
import sqlite3


columns_to_keep = [
    'player_id', 'fifa_version', 'fifa_update', 'short_name', 'long_name',
    'player_positions', 'overall', 'potential', 'value_eur', 'wage_eur',
    'age', 'dob', 'height_cm', 'weight_kg', 'league_id', 'league_name',
    'league_level', 'club_team_id', 'club_name', 'club_position',
    'club_jersey_number', 'club_contract_valid_until_year', 'nationality_name',
    'nation_jersey_number', 'preferred_foot', 'weak_foot', 'skill_moves',
    'international_reputation', 'work_rate', 'body_type', 'release_clause_eur',
    'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic',
    'attacking_crossing', 'attacking_finishing'
]

# Creates Database and connects us to it
conn = sqlite3.connect("../data/fifa_players.db")


# Chunksize declaration to help parse the csv
chunksize = 100000


# Parse the CSV with the columns above
for chunk in pd.read_csv("male_players.csv", chunksize=chunksize, usecols=columns_to_keep):
    # Filters the dataframe to only PL players
    filter = chunk[chunk['league_name'] == 'Premier League']

    # Creates the table filled with prem players
    filter.to_sql("premier_league_players", conn, if_exists='append', index=False)

conn.close()