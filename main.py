import time

import requests
from tqdm import tqdm


def get_market_info(url):

    # Takes a Polymarket URL and returns market info
    # We need the condition_id from it

    slug = url.split("/event/")[-1].split("/")[0]
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

    print(f"\n{'=' * 50}")
    print(f"Market: {question}")
    print(f"{'=' * 50}")

    # Get top holders
    all_holders = get_top_holders(condition_id, limit)

    yes_holders = [h for h in all_holders if h["outcome_index"] == 0]
    no_holders = [h for h in all_holders if h["outcome_index"] == 1]

    print(f"Found {len(yes_holders)} YES holders and {len(no_holders)} NO holders")

    # Each holder pnl
    for holder in tqdm(yes_holders, desc="Fetching YES holders PnL"):
        holder["pnl"] = get_user_pnl(holder["address"])
        time.sleep(0.2)

    for holder in tqdm(no_holders, desc="Fetching NO holders PnL"):
        holder["pnl"] = get_user_pnl(holder["address"])
        time.sleep(0.2)

    # Weighted pnl
    yes_weighted_pnl = calculate_weighted_pnl(yes_holders)
    no_weighted_pnl = calculate_weighted_pnl(no_holders)

    # Print the results
    print(f"\n{'=' * 50}")
    print("SMART MONEY SIGNAL")
    print(f"{'=' * 50}")
    print(f"Weighted pnl - YES holders: ${yes_weighted_pnl:>10,.2f}")
    print(f"Weighted pnl - NO holders: ${no_weighted_pnl:>10,.2f}")
    print(f"{'=' * 50}")

    if yes_weighted_pnl > no_weighted_pnl:
        print("Smart money leans YES")
    elif yes_weighted_pnl < no_weighted_pnl:
        print("Smart money leans NO")
    else:
        print("Smart money is neutral")

    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    url = input("Please enter the polymarket url: ")
    analyze_market(url)
