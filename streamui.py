import time

import streamlit as st
from pandas._libs.window.indexers import calculate_variable_window_bounds
from pandas.core.indexes.base import get_unanimous_names

from main import calculate_weighted_pnl, get_market_info, get_top_holders, get_user_pnl

st.set_page_config(page_title="HolderLens", page_icon="🔍", layout="centered")

# Header
st.title("HolderLens")
st.markdown("Smart money analysis for Polymarket")
st.divider()

# URL input
url = st.text_input("Polymarket URL", placeholder="https://polymarket.com/event/...")

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

    st.divider()

    if st.button("Run Analysis"):
        with st.spinner("Fetching top holders..."):
            all_holders = get_top_holders(condition_id, limit=50)

        yes_holders = [h for h in all_holders if h["outcome_index"] == 0]
        no_holders = [h for h in all_holders if h["outcome_index"] == 1]

        col1, col2 = st.columns(2)

        col1.metric("YES Holders", len(yes_holders))
        col2.metric("NO Holders", len(no_holders))

        st.divider()

        st.markdown("**Fetching PnL for YES holders...**")

        yes_bar = st.progress(0)
        for i, holder in enumerate(yes_holders):
            holder["pnl"] = get_user_pnl(holder["address"])
            yes_bar.progress((i + 1) / len(yes_holders) if yes_holders else 1)
            time.sleep(0.2)

        st.markdown("**Fetching PnL for NO holders...**")

        yes_bar = st.progress(0)
        for i, holder in enumerate(no_holders):
            holder["pnl"] = get_user_pnl(holder["address"])
            yes_bar.progress((i + 1) / len(no_holders) if no_holders else 1)
            time.sleep(0.2)

        yes_wpnl = calculate_weighted_pnl(yes_holders)
        no_wpnl = calculate_weighted_pnl(no_holders)

        st.divider()

        st.subheader("Smart Money Signal")

        col3, col4 = st.columns(2)
        col3.metric("Weighted PnL - YES", f"${yes_wpnl:,.2f}")
        col4.metric("Weighted PnL - NO", f"${no_wpnl:,.2f}")

        st.divider()

        if yes_wpnl > no_wpnl:
            st.success("Smart money leans **YES**")
        elif no_wpnl > yes_wpnl:
            st.error("Smart money leans **NO**")
        else:
            st.info("Smart money is neutral")
