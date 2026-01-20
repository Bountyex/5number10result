import streamlit as st
import pandas as pd
from itertools import product
from collections import Counter

st.set_page_config(page_title="Lowest Payout Combination", layout="wide")

st.title("🎯 Lowest Payout Combination Finder")
st.write("Upload your Excel file to calculate the lowest payout 5-digit combinations.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.iloc[:, [0, 1]]
    df.columns = ["ticket", "category"]

    df = df.dropna(subset=["ticket", "category"])
    df["category"] = df["category"].astype(str).str.strip().str.lower()

    st.subheader("📊 Data Preview")
    st.dataframe(df.head())
    st.write("Total tickets:", len(df))

    # ===============================
    # PREPROCESS TICKETS
    # ===============================
    tickets = []
    for _, row in df.iterrows():
        digits = tuple(map(int, str(row["ticket"]).split(",")))
        tickets.append({
            "digits": digits,
            "counter": Counter(digits),
            "category": row["category"]
        })

    # ===============================
    # PAYOUT TABLES
    # ===============================
    STRAIGHT_PAYOUT = {5: 45000}
    RUMBLE_PAYOUT   = {3: 5, 4: 120, 5: 1850}
    CHANCE_PAYOUT   = {1: 15, 2: 100, 3: 1250, 4: 8500, 5: 13500}

    # ===============================
    # MATCH FUNCTIONS
    # ===============================
    def straight_match(combo, ticket):
        count = 0
        for i in range(5):
            if combo[i] == ticket[i]:
                count += 1
            else:
                break
        return count

    def chance_match(combo, ticket):
        count = 0
        for i in range(1, 6):
            if combo[-i] == ticket[-i]:
                count += 1
            else:
                break
        return count

    def rumble_match(combo_counter, ticket_counter):
        return sum((combo_counter & ticket_counter).values())

    # ===============================
    # RUN
    # ===============================
    if st.button("🚀 Calculate Lowest 10 Payouts"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        best_results = []  # store top 10 lowest payouts
        total_combos = 100000

        for idx, combo in enumerate(product(range(10), repeat=5)):
            combo_counter = Counter(combo)

            straight_total = 0
            rumble_total = 0
            chance_total = 0

            current_threshold = max(
                [r["Total Payout"] for r in best_results], default=float("inf")
            )

            for t in tickets:
                if t["category"] == "straight":
                    m = straight_match(combo, t["digits"])
                    straight_total += STRAIGHT_PAYOUT.get(m, 0)

                elif t["category"] == "rumble":
                    m = rumble_match(combo_counter, t["counter"])
                    rumble_total += RUMBLE_PAYOUT.get(m, 0)

                elif t["category"] == "chance":
                    m = chance_match(combo, t["digits"])
                    chance_total += CHANCE_PAYOUT.get(m, 0)

                if straight_total + rumble_total + chance_total >= current_threshold:
                    break

            total_payout = straight_total + rumble_total + chance_total

            if len(best_results) < 10 or total_payout < current_threshold:
                best_results.append({
                    "Best Combination": ",".join(map(str, combo)),
                    "Total Payout": total_payout,
                    "Straight Payout": straight_total,
                    "Rumble Payout": rumble_total,
                    "Chance Payout": chance_total
                })

                best_results = sorted(best_results, key=lambda x: x["Total Payout"])[:10]

            if idx % 1000 == 0:
                progress_bar.progress(idx / total_combos)
                status_text.text(f"Processing {idx:,} / {total_combos:,}")

        progress_bar.progress(1.0)
        status_text.text("Completed ✔")

        # ===============================
        # RESULTS
        # ===============================
        result_df = pd.DataFrame(best_results)

        st.subheader("🏆 Top 10 Lowest Payout Combinations")
        st.dataframe(result_df, use_container_width=True)
