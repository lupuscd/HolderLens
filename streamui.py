import time

import streamlit as st

from main import (
    calculate_weighted_pnl,
    get_market_info,
    get_top_holders,
    get_user_pnl,
    group_holders_by_outcome,
)

st.set_page_config(page_title="HolderLens", page_icon="🔍", layout="centered")

# Clear Inoput field
if "url_input" not in st.session_state:
    st.session_state.url_input = ""

# Header
st.title("HolderLens")
st.markdown("Smart money analysis for Polymarket")
st.caption(
    "Fetches up to 50 holders per side. Holders with less than 100 shares are filtered out."
)
st.divider()

# URL input
url = st.text_input(
    "Polymarket URL", placeholder="https://polymarket.com/event/...", key="url_input"
)

if url:
    market_info = get_market_info(url)

    if not market_info:
        st.error("Could not fetch market info")
        st.stop()

    markets = market_info["markets"]

    questions = [m["question"] for m in markets]
    selected_question = st.selectbox("Select a market", questions)
    selected = markets[questions.index(selected_question)]

    condition_id = selected["condition_id"]
    outcomes = selected["outcomes"]

    st.divider()

    if st.button("Run Analysis"):
        # Create an empty status placeholder
        status_placeholder = st.empty()

        # Create a placeholder for holders
        holders_placeholder = st.empty()

        st.divider()

        # Create progress placeholder
        progress_label = st.empty()
        progress_bar = st.empty()

        # Create results placeholder
        results_placeholder = st.empty()

        status_placeholder.info("Fetching top holders...")

        all_holders = get_top_holders(condition_id, limit=50)

        # Group holders dynamically by outcome
        grouped_holders = group_holders_by_outcome(all_holders)

        with holders_placeholder.container():
            cols = st.columns(len(outcomes))
            for idx, col in enumerate(cols):
                label = outcomes[idx] if idx < len(outcomes) else f"Outcome {idx}"
                count = len(grouped_holders.get(idx, []))
                col.metric(f"{label} Holders", count)

        # Fetch PnL for each group
        for idx, holders in grouped_holders.items():
            label = outcomes[idx] if idx < len(outcomes) else f"Outcome {idx}"
            progress_label.markdown(f"**Fetching PnL for {label} holders...**")
            progress_bar.progress(0)

            for i, holder in enumerate(holders):
                holder["pnl"] = get_user_pnl(holder["address"])
                progress_bar.progress((i + 1) / len(holders) if holders else 1)
                time.sleep(0.2)

        progress_label.empty()
        progress_bar.empty()
        status_placeholder.empty()

        # Calculate weighted PnL per outcome
        weighted_pnls = {}
        for idx, holders in grouped_holders.items():
            label = outcomes[idx] if idx < len(outcomes) else f"Outcome {idx}"
            weighted_pnls[label] = calculate_weighted_pnl(holders)

        # Fill results
        with results_placeholder.container():
            st.subheader("Smart Money Signal")

            # One column per outcome
            cols = st.columns(len(outcomes))
            for i, (label, wpnl) in enumerate(weighted_pnls.items()):
                cols[i].metric(f"Weighted PnL - {label}", f"${wpnl:,.2f}")

            st.divider()

            if weighted_pnls:
                best = max(weighted_pnls, key=lambda label: weighted_pnls[label])
                worst = min(weighted_pnls, key=lambda label: weighted_pnls[label])

                if weighted_pnls[best] == weighted_pnls[worst]:
                    st.info("Smart money is neutral")
                else:
                    st.success(f"Smart money leans **{best}**")

    # Start over button
    if st.button("↺ Start Over"):
        del st.session_state.url_input
        st.rerun()

# Discaimer

st.divider()
st.caption(
    "HolderLens is for informational purposes only. Nothing here is financial advice. Prediction markets are risky and past PnL of holders does not guarantee future performance."
)
