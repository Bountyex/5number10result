import streamlit as st
import pandas as pd
from itertools import product
from collections import Counter
from heapq import heappush, heappop

st.set_page_config(page_title="Lowest Payout Combination Finder", layout="wide")

st.title("🎯 Lowest Payout Combination Finder (Advanced Constraints Version)")

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

    RUMBLE_PAYOUT = {
        3: 10,
        4: 400,
        5: 2000
    }

    CHANCE_PAYOUT = {
        1: 15,
        2: 110,
        3: 1150,
        4: 8500,
        5: 12500
    }


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

    st.subheader("🎛 Advanced Match Constraints")

    st.write("Set MIN and MAX matches required (0 means ignore)")


    def constraint_row(title, matches):

        cols = st.columns(len(matches))

        min_vals = {}
        max_vals = {}

        for i, m in enumerate(matches):

            with cols[i]:

                st.markdown(f"**{title} {m}-digit**")

                min_vals[m] = st.number_input(
                    f"{title}_{m}_min",
                    min_value=0,
                    max_value=100,
                    value=0
                )

                max_vals[m] = st.number_input(
                    f"{title}_{m}_max",
                    min_value=0,
                    max_value=100,
                    value=0
                )

        return min_vals, max_vals


    rumble_min, rumble_max = constraint_row("Rumble", [3,4,5])

    chance_min, chance_max = constraint_row("Chance", [1,2,3,4,5])

    straight_min, straight_max = constraint_row("Straight", [5])


    # ===============================
    # CONSTRAINT CHECK FUNCTION
    # ===============================

    def check_constraints(match_counts, min_vals, max_vals):

        for k in match_counts:

            if min_vals[k] != 0:

                if match_counts[k] < min_vals[k]:

                    return True

            if max_vals[k] != 0:

                if match_counts[k] > max_vals[k]:

                    return True

        return False


    # ===============================
    # RUN BUTTON
    # ===============================

    if st.button("🚀 Calculate Lowest 10 Payouts"):

        progress_bar = st.progress(0)

        status_text = st.empty()

        best_results = []

        total_combos = 100000


        for idx, combo in enumerate(product(range(10), repeat=5)):

            combo_counter = Counter(combo)

            straight_total = 0
            rumble_total = 0
            chance_total = 0


            rumble_match_counts = {3:0,4:0,5:0}
            chance_match_counts = {1:0,2:0,3:0,4:0,5:0}
            straight_match_counts = {5:0}


            current_threshold = max(
                [r[0] for r in best_results],
                default=float("inf")
            )


            # STRAIGHT

            for ticket in straight_tickets:

                m = straight_match(combo, ticket)

                if m in straight_match_counts:

                    straight_match_counts[m] += 1

                straight_total += STRAIGHT_PAYOUT.get(m, 0)

                if straight_total >= current_threshold:

                    break


            # RUMBLE

            if straight_total < current_threshold:

                for ticket_counter in rumble_tickets:

                    m = rumble_match(combo_counter, ticket_counter)

                    if m in rumble_match_counts:

                        rumble_match_counts[m] += 1

                    rumble_total += RUMBLE_PAYOUT.get(m, 0)

                    if straight_total + rumble_total >= current_threshold:

                        break


            # CHANCE

            if straight_total + rumble_total < current_threshold:

                for ticket in chance_tickets:

                    m = chance_match(combo, ticket)

                    if m in chance_match_counts:

                        chance_match_counts[m] += 1

                    chance_total += CHANCE_PAYOUT.get(m, 0)

                    if straight_total + rumble_total + chance_total >= current_threshold:

                        break


            # APPLY CONSTRAINT FILTER

            if check_constraints(rumble_match_counts, rumble_min, rumble_max):

                continue

            if check_constraints(chance_match_counts, chance_min, chance_max):

                continue

            if check_constraints(straight_match_counts, straight_min, straight_max):

                continue


            total_payout = straight_total + rumble_total + chance_total


            heappush(best_results, (

                total_payout,

                ",".join(map(str, combo)),

                straight_total,

                rumble_total,

                chance_total

            ))


            if len(best_results) > 10:

                heappop(best_results)


            if idx % 1000 == 0:

                progress_bar.progress(idx / total_combos)

                status_text.text(f"Processing {idx:,} / {total_combos:,}")


        progress_bar.progress(1.0)

        status_text.text("Completed ✔")


        result_df = pd.DataFrame(

            sorted(best_results),

            columns=[

                "Total Payout",

                "Combination",

                "Straight",

                "Rumble",

                "Chance"

            ]

        )


        st.subheader("🏆 Top 10 Lowest Payout Combinations")

        st.dataframe(result_df, use_container_width=True)
