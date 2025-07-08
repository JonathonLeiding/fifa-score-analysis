# fifa-score-analysis

# 🏟 Predicting Premier League Player Performance from FIFA Ratings

This project builds a neural network model to predict **goals and assists** for Premier League players using **FIFA player ratings** combined with **real-world performance stats**.

It covers everything from **web scraping**, **SQL joins**, and **data cleaning** to **feature engineering** and **deep learning with PyTorch** — done entirely solo.

---

## 🔍 Overview

- 🎮 Source Data: [FIFA 15–23 player ratings](https://huggingface.co/datasets/jsulz/FIFA23) (5.6GB)
- 📈 Target Data: Goals and assists scraped from [Transfermarkt.com](https://www.transfermarkt.com)
- ⚽ League Filter: Premier League players only (`league_id == 13`)
- 🧼 Data Volume: Over 5,000 rows of player-season data after filtering and cleaning

---

## 🛠️ Features & Preprocessing

### ✅ Data Filtering
- Filtered to **Premier League** only
- Used only the **first version update per FIFA release** (`fifa_update == 1`)
- Removed duplicate or incomplete player rows

### 🧠 Feature Engineering
| Feature Type           | Examples                        | Strategy                                |
|------------------------|----------------------------------|------------------------------------------|
| Continuous (skewed)    | `value_eur`, `wage_eur`         | Log-transform + Z-score normalization   |
| Continuous (regular)   | `age`, `height_cm`, `weight_kg` | Z-score normalization                   |
| Ordinal Ratings        | `weak_foot`, `skill_moves`, etc.| Left as-is (range 1–5)                  |
| Categorical (low-card) | `work_rate`, `body_type`        | One-hot encoding                        |
| Categorical (ID)       | `player_id`, `club_team_id`     | Integer encoding + PyTorch embeddings   |
| Positional features    | `primary_position`, `club_position` | Mapped and embedded                    |
| Binary Flags           | `has_multiple_positions`, `preferred_foot` | Direct binary (0/1)          |

---

## 🤖 Model

The model is a **PyTorch regression neural network** with:

- Two **embedding layers** for player and club IDs
- One **dense feature vector** (all numerical + one-hot inputs)
- Several **fully connected layers** with LeakyReLU activations
- `SmoothL1Loss` for stable regression of `goals` and `assists`

---


## 🧑‍💻 How This Was Built

This project involved:

- 🕸 Web scraping with `requests` and `BeautifulSoup`
- 🧪 SQL merging of Transfermarkt and Hugging Face datasets
- 🔧 Data wrangling in pandas
- 📊 Feature engineering (log transforms, embeddings, one-hot)
- 🔥 Neural network training with PyTorch

> This is a solo-built project to showcase full-stack machine learning development on messy real-world data.

---

## 📢 About Me

I'm an independent ML practitioner exploring data-driven storytelling in sports, games, and real-world outcomes. This project represents my ability to work end-to-end: from unstructured data to predictive modeling.

📬 Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/jonathon-leiding/) or explore more on [GitHub](https://github.com/JonathonLeiding).

---

## 🚀 Future Work

- Add player injury or minutes played data for better targets
- Expand to other leagues or international data
- Convert to a multi-task model (classification + regression)
- Deploy a simple interface to input a player and predict output

---

## 🧾 License

MIT License.
