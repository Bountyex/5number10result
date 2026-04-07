import streamlit as st
import pandas as pd
from itertools import product
from collections import Counter
from heapq import heappush, heappop

st.set_page_config(page_title="Lowest Payout Finder", layout="wide")

st.title("🎯 Lowest Payout Combination Finder (Accurate Version)")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"])

if uploaded_file:

    # ===============================
    # LOAD FILE (SAFE)
    # ===============================
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    df = df.iloc[:, [0, 1]]
    df.columns = ["ticket", "category"]

    df = df.dropna(subset=["ticket", "category"])
    df["category"] = df["category"].astype(str).str.strip().str.lower()

    st.write("Total tickets:", len(df))

    # ===============================
    # PREPROCESS
    # ===============================
    straight_tickets = []
    rumble_tickets = []
    chance_tickets = []

    for _, row in df.iterrows():
        digits = tuple(map(int, str(row["ticket"]).split(",")))
        category = row["category"]

        if category == "straight":
            straight_tickets.append(digits)

        elif category == "rumble":
            rumble_tickets.append(Counter(digits))

        elif category == "chance":
            chance_tickets.append(digits)

    # ===============================
    # PAYOUT TABLE
    # ===============================
    STRAIGHT_PAYOUT = {5: 45000}
    RUMBLE_PAYOUT = {3: 10, 4: 400, 5: 2000}
    CHANCE_PAYOUT = {1: 15, 2: 110, 3: 1150, 4: 8500, 5: 12500}

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
    # CONSTRAINT UI
    # ===============================
    st.subheader("🎛 Constraints (Min / Max)")

    def constraint_row(title, matches):
        cols = st.columns(len(matches))
        min_vals = {}
        max_vals = {}

        for i, m in enumerate(matches):
            with cols[i]:
                st.markdown(f"**{title} {m}**")
                min_vals[m] = st.number_input(f"{title}_{m}_min", 0, 100, 0)
                max_vals[m] = st.number_input(f"{title}_{m}_max", 0, 100, 0)

        return min_vals, max_vals

    rumble_min, rumble_max = constraint_row("Rumble", [3,4,5])
    chance_min, chance_max = constraint_row("Chance", [1,2,3,4,5])
    straight_min, straight_max = constraint_row("Straight", [5])

    def check_constraints(match_counts, min_vals, max_vals):
        for k in match_counts:
            if min_vals[k] != 0 and match_counts[k] < min_vals[k]:
                return True
            if max_vals[k] != 0 and match_counts[k] > max_vals[k]:
                return True
        return False

    # ===============================
    # RUN
    # ===============================
    if st.button("🚀 Find TRUE Lowest Payout"):

        progress_bar = st.progress(0)
        status = st.empty()

        best_results = []

        # 🔥 FORCE TRACK GLOBAL MIN
        global_min_payout = float("inf")

        total_combos = 100000

        for idx, combo in enumerate(product(range(10), repeat=5)):

            combo_counter = Counter(combo)

            straight_total = 0
            rumble_total = 0
            chance_total = 0

            rumble_counts = {3:0,4:0,5:0}
            chance_counts = {1:0,2:0,3:0,4:0,5:0}
            straight_counts = {5:0}

            # =====================
            # FULL CALCULATION (NO EARLY STOP BUG)
            # =====================

            for t in straight_tickets:
                m = straight_match(combo, t)
                if m in straight_counts:
                    straight_counts[m] += 1
                straight_total += STRAIGHT_PAYOUT.get(m, 0)

            for t in rumble_tickets:
                m = rumble_match(combo_counter, t)
                if m in rumble_counts:
                    rumble_counts[m] += 1
                rumble_total += RUMBLE_PAYOUT.get(m, 0)

            for t in chance_tickets:
                m = chance_match(combo, t)
                if m in chance_counts:
                    chance_counts[m] += 1
                chance_total += CHANCE_PAYOUT.get(m, 0)

            # =====================
            # CONSTRAINT CHECK
            # =====================

            if check_constraints(rumble_counts, rumble_min, rumble_max):
                continue
            if check_constraints(chance_counts, chance_min, chance_max):
                continue
            if check_constraints(straight_counts, straight_min, straight_max):
                continue

            total_payout = straight_total + rumble_total + chance_total

            # 🔥 FORCE LOWEST ONLY TRACK
            if total_payout < global_min_payout:
                global_min_payout = total_payout
                best_results = []  # reset list

            if total_payout == global_min_payout:
                heappush(best_results, (
                    total_payout,
                    ",".join(map(str, combo)),
                    straight_total,
                    rumble_total,
                    chance_total
                ))

            if len(best_results) > 10:
                heappop(best_results)

            # progress
            if idx % 1000 == 0:
                progress_bar.progress(idx / total_combos)
                status.text(f"Checked {idx:,} / {total_combos:,} | Best: {global_min_payout}")

        progress_bar.progress(1.0)
        status.text(f"Completed ✔ TRUE Lowest Payout = {global_min_payout}")

        # ===============================
        # RESULTS
        # ===============================
        result_df = pd.DataFrame(
            sorted(best_results),
            columns=["Total", "Combination", "Straight", "Rumble", "Chance"]
        )

        st.subheader("🏆 TRUE LOWEST Payout Results")
        st.dataframe(result_df, use_container_width=True)
