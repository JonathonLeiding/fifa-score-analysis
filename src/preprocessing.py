import pandas as pd
import sqlite3
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Mapping from position names to indices
POSITION_MAP = {
    'RCM': 0, 'ST': 1, 'LCB': 2, 'RW': 3, 'LW': 4, 'GK': 5, 'LB': 6, 'LCM': 7,
    'RCB': 8, 'CDM': 9, 'RB': 10, 'CB': 11, 'SUB': 12, 'RDM': 13, 'CAM': 14,
    'RES': 15, 'LDM': 16, 'RWB': 17, 'LM': 18, 'LWB': 19, 'RM': 20, 'LS': 21,
    'RS': 22, 'CF': 23, 'CM': 24
}


def load_sql_table(path: str, query: str) -> pd.DataFrame:
    """Connect to SQLite and return result of query."""
    conn = sqlite3.connect(path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def manual_goal_assist_corrections(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply manual corrections to goal/assist stats based on external Transfermarkt lookup.
    These were manually verified and edited during preprocessing.
    """
    corrections = {
        4147: [7, 1],
        2687: [5, 0],
        1578: [1, 1],
        2493: [0, 0],
        2946: [0, 0],
        3762: [0, 0],
        5057: [3, 3],
        4928: [0, 0],
        4781: [0, 0],
        3749: [0, 0],
        3323: [0, 0],
        5319: [0, 0],
        3484: [0, 0],
        4167: [2, 2],
        2692: [3, 2],
        4994: [3, 1],
        4019: [1, 0],
        3260: [0, 0],
        4733: [0, 0],
        2515: [0, 0],
        2399: [1, 1],
        3506: [1, 0],
        3481: [2, 0],
        4995: [4, 3],
        5064: [1, 0],
        2854: [2, 1],
        3656: [1, 0],
        3394: [1, 1],
        3362: [0, 1],
        5018: [2, 2],
        5095: [0, 1],
        3460: [0, 1],
        3402: [1, 0],
        2460: [0, 0],
        4957: [2, 0],
        5047: [3, 0],
        5086: [0, 0],
        3389: [0, 0],
        3493: [1, 0],
        2536: [0, 0],
        4835: [1, 1],
        3217: [1, 0],
        3186: [2, 1],
        4992: [0, 1],
        4080: [1, 0],
        2592: [1, 0],
        4706: [1, 1],
        3267: [1, 1],
        3291: [0, 0],
        2866: [0, 0],
        4726: [1, 2],
        2734: [0, 0],
        4750: [0, 0],
        4130: [0, 1],
        4404: [0, 0],
        4715: [1, 2],
        5101: [0, 1],
        4561: [0, 0],
        5112: [0, 0],
        4976: [0, 0],
        3071: [0, 0],
        4534: [0, 0],
        4645: [1, 1],
        5005: [0, 0],
        2737: [0, 0],
        3343: [1, 0],
        2585: [2, 0],
        4912: [1, 1],
        2685: [0, 0],
        4943: [1, 0],
        3063: [0, 0],
        3131: [1, 0],
        4683: [2, 0],
        4832: [2, 0],
        5039: [1, 0],
        2742: [1, 1],
        2939: [2, 0],
        5116: [0, 0],
        4646: [0, 0],
        2897: [1, 1],
        5040: [0, 1],
        4571: [1, 0],
        5055: [0, 0],
        2874: [0, 0],
        3130: [1, 1],
        4545: [0, 1],
        4691: [0, 0],
        3314: [1, 0],
        4783: [2, 1],
        3105: [0, 0],
        4713: [1, 1],
        3224: [0, 0],
        3152: [0, 0],
        3341: [0, 1],
        5110: [0, 0]
    }

    for idx, (goals, assists) in corrections.items():
        df.loc[idx, ['goals', 'assists']] = [goals, assists]

    # Drop rows that were found to be misattributed, duplicates, or corrupt
    drop_indices = [
        5318, 4695, 4962, 2809, 5114, 4444, 2970, 3165, 2679, 4742,
        3037, 2974, 4752, 3463, 2813, 3470, 4676, 4709, 2802, 4830,
        4751, 4686, 3180, 3202, 2770, 2757, 2725, 2776, 2763, 3236,
        2803, 3232, 2733, 2744, 2830, 3035, 2785, 2730, 2716, 2947,
        2914, 3294, 2956, 2886, 3327, 2841, 2844, 2826, 2790, 2919,
        2784, 2787, 3238, 3066, 2797, 2811, 2780, 2852, 2869, 2817,
        2981, 2767, 2812, 2820, 2896, 2900, 2810, 2858, 2835, 2890,
        2985, 2864, 2883, 2904, 2909, 2764, 3073, 2821, 2889, 2871,
        2827, 2873, 2849, 2769, 2987, 2823, 2838, 2887, 2786, 2926,
        2992, 3068, 2901, 2851, 2964, 3078
    ]

    df = df.drop(index=drop_indices, errors='ignore')
    return df



def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features like years_remaining, primary_position, etc."""
    df['primary_position'] = df['player_positions'].apply(lambda x: x.split(',')[0].strip())
    df['has_multiple_positions'] = df['player_positions'].apply(lambda x: ',' in x).astype(int)
    df['primary_position_mapped'] = df['primary_position'].map(POSITION_MAP)
    df['club_position_mapped'] = df['club_position'].map(POSITION_MAP)
    df['years_remaining'] = df['club_contract_valid_until_year'] - 2000 - df['fifa_version']
    return df


def handle_missing_and_log_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values for monetary features, apply log transform."""
    for col in ['value_eur', 'wage_eur']:
        if df[col].isna().any():
            low_val = df[col].quantile(0.01)
            df[col] = df[col].fillna(low_val)
        df[f'log_{col}'] = np.log1p(df[col])
    return df


def normalize_numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply z-score normalization to numerical columns."""
    scaler = StandardScaler()
    cols_to_scale = ['log_value_eur', 'log_wage_eur', 'age', 'height_cm', 'weight_kg']
    df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
    return df


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode work_rate and body_type."""
    ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    for col in ['work_rate', 'body_type']:
        encoded = ohe.fit_transform(df[[col]])
        encoded_df = pd.DataFrame(encoded, columns=ohe.get_feature_names_out([col]))
        df = pd.concat([df.reset_index(drop=True), encoded_df.reset_index(drop=True)], axis=1)
        df.drop(columns=[col], inplace=True)
    return df


def encode_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Convert player_id and club_team_id to integer category codes for embeddings."""
    df['player_id'] = df['player_id'].astype('category').cat.codes
    df['club_team_id'] = df['club_team_id'].astype('category').cat.codes
    df['preferred_foot'] = df['preferred_foot'].map({'Right': 0, 'Left': 1})
    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only final model-ready columns."""
    use_cols = [
        'player_id', 'fifa_version',
        'overall', 'potential', 'age', 'height_cm', 'weight_kg',
        'club_team_id', 'club_jersey_number', 'preferred_foot',
        'weak_foot', 'skill_moves', 'international_reputation',
        'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic',
        'attacking_crossing', 'attacking_finishing', 'goals', 'assists',
        'club_position_mapped', 'has_multiple_positions',
        'primary_position_mapped', 'years_remaining',
        'log_value_eur', 'log_wage_eur',
    ]
    # Add one-hot columns for work_rate and body_type
    ohe_cols = [col for col in df.columns if col.startswith('work_rate_') or col.startswith('body_type_')]
    return df[use_cols + ohe_cols]


def preprocess_all(sql_path: str, query: str, out_path: str = None) -> pd.DataFrame:
    """Main preprocessing pipeline."""
    df = load_sql_table(sql_path, query)
    df = df[df['fifa_update'].notna()]  # remove unmatched Transfermarkt-only rows
    df = manual_goal_assist_corrections(df)
    df = feature_engineering(df)
    df = handle_missing_and_log_transform(df)
    df = normalize_numeric_features(df)
    df = encode_categorical_features(df)
    df = encode_ids(df)
    df = select_columns(df)

    if out_path:
        df.to_csv(out_path, index=False)
        print(f"✅ Saved to {out_path}")

    return df


if __name__ == "__main__":
    final_df = preprocess_all(
        sql_path="../data/fifa_players.db",
        query="SELECT * FROM prem_name_join",
        out_path="data/cleaned_prem_data.csv"
    )
