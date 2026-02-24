import json
import time

import requests
from tqdm import tqdm


def get_market_info(url):

    # Takes a Polymarket URL and returns market info
    # We need the condition_id from it
    if "/event/" in url:
        slug = url.split("/event/")[1].split("/")[0]
    elif "/sports/" in url:
        slug = url.split("/")[-1]
    else:
        print("Unrecognized URL format")
        return None

    gamma_url = f"https://gamma-api.polymarket.com/events?slug={slug}"

    response = requests.get(gamma_url)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    data = response.json()

    if not data:
        print("No data")
        return None

    # First matching event
    event = data[0]

    market_info = {"title": event.get("title"), "slug": slug, "markets": []}

    # Events might have multiple markets (eg multiple dates)
    for market in event.get("markets", []):
        market_info["markets"].append(
            {
                "question": market.get("question"),
                "condition_id": market.get("conditionId"),
                "outcomes": json.loads(market.get("outcomes", "[]")),
            }
        )

    return market_info


def get_top_holders(condition_id, limit=50):

    # Fetches top market holders

    url = f"https://data-api.polymarket.com/holders?market={condition_id}&limit={limit}&offset=0"

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    data = response.json()

    if not data:
        print("No holders found")
        return []

    holders = []

    for token_data in data:
        for holder in token_data.get("holders", []):
            amount = float(holder.get("amount", 0))
            if amount < 100:
                continue
            holders.append(
                {
                    "address": holder.get("proxyWallet"),
                    "amount": float(holder.get("amount", 0)),
                    "outcome_index": holder.get("outcomeIndex"),
                }
            )

    return holders


def group_holders_by_outcome(holders):

    grouped = {}
    for holder in holders:
        idx = holder["outcome_index"]
        grouped.setdefault(idx, []).append(holder)
    return grouped


def get_user_pnl(address):

    # Fetches total all time pnl of a holder

    url = (
        f"https://data-api.polymarket.com/v1/leaderboard?user={address}&timePeriod=ALL"
    )
    response = requests.get(url)

    if response.status_code != 200:
        return 0

    data = response.json()

    if not data:
        return 0

    return float(data[0].get("pnl", 0))


def calculate_weighted_pnl(holders):

    # Weighted PnL = Σ(PnL_i × Amount_i) / Σ(Amount_i)

    total_wpnl = 0
    total_share_amount = 0

    for holder in holders:
        pnl = holder.get("pnl", 0)
        amount = holder.get("amount", 0)

        if amount == 0 or pnl is None:
            continue

        total_wpnl += pnl * amount
        total_share_amount += amount

    if total_share_amount == 0:
        return 0

    return total_wpnl / total_share_amount


def analyze_market(url, limit=50):

    # Main function

    # Get market info
    market_info = get_market_info(url)

    if not market_info:
        print("Could not get market info")
        return

    markets = market_info["markets"]

    if len(markets) > 1:
        print(f"\n{'=' * 50}")
        print("Available markets:")
        for i, market in enumerate(markets):
            print(f"  {i + 1}. {market['question']}")
        print(f"{'=' * 50}")

        while True:
            try:
                choice = int(input("Pick a market (enter number): "))
                if 1 <= choice <= len(markets):
                    break
                print(f"Please enter a number between 1 and {len(markets)}")
            except ValueError:
                print("Please enter a valid number")
        selected = markets[choice - 1]
    else:
        selected = markets[0]

    question = selected["question"]
    condition_id = selected["condition_id"]
    outcomes = selected["outcomes"]

    print(f"\n{'=' * 50}")
    print(f"Market: {question}")
    print(f"{'=' * 50}")

    # Get top holders
    all_holders = get_top_holders(condition_id, limit)

    # Group holders dynamically by outcome
    grouped_holders = group_holders_by_outcome(all_holders)

    for idx, holders in grouped_holders.items():
        label = outcomes[idx] if idx < len(outcomes) else f"Outcome{idx}"
        for holder in tqdm(holders, desc=f"Fetching {label} holders PnL"):
            holder["pnl"] = get_user_pnl(holder["address"])
            time.sleep(0.2)

    # Calculate weighted PnL per outcome and print results
    print(f"\n{'=' * 50}")
    print("SMART MONEY SIGNAL")
    print(f"{'=' * 50}")

    weighted_pnls = {}
    for idx, holders in grouped_holders.items():
        label = outcomes[idx] if idx < len(outcomes) else f"Outcome {idx}"
        wpnl = calculate_weighted_pnl(holders)
        weighted_pnls[label] = wpnl
        print(f"Weighted pnl - {label} holders: ${wpnl:>10,.2f}")

    print(f"{'=' * 50}\n")

    if weighted_pnls:
        best = max(weighted_pnls, key=lambda label: weighted_pnls[label])
        worst = min(weighted_pnls, key=lambda label: weighted_pnls[label])
        if weighted_pnls[best] == weighted_pnls[worst]:
            print("Smart money is neutral")
        else:
            print(f"Smart money leans {best}")

    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    url = input("Please enter the polymarket url: ")
    analyze_market(url)
