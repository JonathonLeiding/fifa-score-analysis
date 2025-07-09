# fifa-score-analysis

# ⚽ Predicting Premier League Player Performance from FIFA Data

This project builds a deep learning model to predict **goals and assists** for Premier League players based on their **FIFA attributes** and real-world performance data. The project integrates multiple data sources, extensive preprocessing, and is designed for potential deployment.

---

## 📦 Data Sources

- 🎮 **FIFA 15–23 player dataset** from [Hugging Face](https://huggingface.co/datasets/jsulz/FIFA23) (5.6 GB total)
- 📊 **Goals and assists** scraped from [Transfermarkt.com](https://www.transfermarkt.com)
- 🏆 Filtered for **Premier League players** (`league_id == 13`) and **first season updates** (`fifa_update == 1`) to ensure consistency

---

## 🔍 Project Goals

- Create a dataset of **Premier League player-seasons** with matching FIFA ratings and performance stats
- Use deep learning (PyTorch) to predict:
  - `goals`
  - `assists`

---

## 🧼 Data Cleaning & Feature Engineering

The preprocessing pipeline combines SQL joins (via Beekeeper Studio) and pandas-based feature engineering in Python. Final outputs are stored in `cleaned_prem_data.csv`.

### ✅ Core Steps

| Step                         | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| **Filtering**                | Removed duplicates, mid-season updates, and non-PL players                  |
| **Manual Corrections**       | Fixed known incorrect `goals`/`assists` using Transfermarkt verification   |
| **Derived Features**         | `primary_position`, `has_multiple_positions`, `years_remaining`            |
| **Monetary Features**        | `value_eur`, `wage_eur` → log-transformed + normalized                     |
| **Physical Features**        | `age`, `height_cm`, `weight_kg` normalized                                 |
| **One-Hot Encoded**          | `work_rate`, `body_type` (small cardinality categorical)                   |
| **Mapped to Int**            | `preferred_foot`: {'Right': 0, 'Left': 1}                                  |
| **Embedded via Category Codes** | `player_id`, `club_team_id`, `primary_position_mapped`, `club_position_mapped` |
| **Removed Redundancy**       | Dropped raw strings like `primary_position` in favor of mapped versions    |

---

## 🧠 Modeling Strategy

A neural network will be built using **PyTorch** and trained on the processed data. Features include both structured float inputs and embedded ID/category variables.

### Architecture Highlights:

- **Regression model** predicting integer-valued `goals` and `assists`
- **Embeddings** for player ID, club ID, and position mappings
- **SmoothL1Loss** for robust regression
- **Adam optimizer** with learning rate scheduler
- **GPU training via Google Colab**

---


---

## 🚀 Future Plans

- Refactor modeling into `.py` files for deployment
- Build a **Streamlit** or **Django** app for interactive predictions
- Host the trained model and API via **Streamlit Cloud** or **Render**

---

## 🎓 What This Demonstrates

- Full-stack ML project: data sourcing → cleaning → modeling
- Deep understanding of data quality and integrity
- Manual and automated feature engineering
- Model-ready design with embeddings and encodings
- Positioned for future deployment and real-world usability

---

## 🧑‍💻 About Me

This is an independent project designed to showcase my data science and machine learning engineering skills — especially in applied settings where structured data meets real-world prediction tasks.

📫 Feel free to reach out on [LinkedIn](https://www.linkedin.com/in/jonathon-leiding/) or explore more on [GitHub](https://github.com/JonathonLeiding).
