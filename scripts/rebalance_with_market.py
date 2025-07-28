import json
import math
import subprocess
import argparse
import time
import requests

API_BASE_URL = "http://localhost:8080"

def get_api_key():
    """Reads the first API key from the config file."""
    try:
        with open('../api_keys.json', 'r') as f:
            data = json.load(f)
            return next(iter(data))
    except (FileNotFoundError, StopIteration, json.JSONDecodeError) as e:
        print(f"❌ Error loading API key: {e}. Cannot execute trades.")
        return None

def fetch_portfolio_data():
    """Fetches the latest portfolio data from the API."""
    print("🔄 Fetching latest portfolio data from API...")
    try:
        response = requests.get(f"{API_BASE_URL}/account", timeout=15)
        response.raise_for_status()
        portfolio_data = response.json()
        if portfolio_data.get("status") == "ok":
            print("✅ Portfolio data updated successfully.")
            return portfolio_data
        else:
            print(f"❌ API Error: {portfolio_data.get('message', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to API server at {API_BASE_URL}. Is it running?")
        return None

def execute_market_order(dry_run=True, target_tickers=None):
    """
    Calculates and executes MARKET orders to sell 25% of a specified list of stocks.
    """
    # This script now requires specific tickers to be provided via the command line.
    if not target_tickers:
        print("❌ Error: Please specify which tickers to process using the --tickers argument.")
        print("   Example: uv run python rebalance_with_market.py --tickers AAPL TSLA")
        return

    portfolio_data = fetch_portfolio_data()
    if not portfolio_data:
        return

    positions = portfolio_data.get("data", {}).get("positions", [])
    if not positions:
        print("⚠️ No positions found in portfolio data.")
        return

    all_positions_dict = {pos['ticker']: pos for pos in positions if 'ticker' in pos}
    
    trades_to_execute = []

    print("================================================================================")
    print("📊 Planning Trades (Sell 25%, Market Order)")
    print("================================================================================")

    for ticker in target_tickers:
        if ticker in all_positions_dict:
            position_data = all_positions_dict[ticker]
            current_position = position_data.get("position", 0)
            conid_str = position_data.get("conid")

            if not conid_str:
                print(f"|-> ⚠️ Skipping {ticker}: No 'conid' found.")
                continue
            
            try:
                conid = int(conid_str)
            except (ValueError, TypeError):
                print(f"|-> ⚠️ Skipping {ticker}: Invalid conid '{conid_str}'.")
                continue

            if isinstance(current_position, (int, float)) and current_position > 0:
                trade_qty = math.floor(current_position * 0.25)
                
                if trade_qty > 0:
                    trade = {
                        "ticker": ticker,
                        "conid": conid,
                        "quantity": trade_qty,
                    }
                    trades_to_execute.append(trade)
                    print(f"|-> ✅ Plan: Sell {trade_qty} of {ticker} at Market Price")
                else:
                    print(f"|-> ℹ️ Skipping {ticker}: Calculated trade quantity is 0.")
            else:
                 print(f"|-> ℹ️ Skipping {ticker}: No position to sell.")

    print("================================================================================")

    if not trades_to_execute:
        print("✅ No trades to execute.")
        return

    if dry_run:
        print("\nℹ️ Dry run complete. To execute these trades, run with the --execute flag.")
        return

    api_key = get_api_key()
    if not api_key:
        return

    print("\n🚀 Executing bulk trade...")

    # Prepare the list of orders for the bulk endpoint
    orders_payload = []
    for trade in trades_to_execute:
        orders_payload.append({
            "conid": trade["conid"],
            "side": "SELL",
            "quantity": trade["quantity"],
            "order_type": "MKT",
            "tif": "DAY"
        })

    # Send all orders in a single API call
    try:
        headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
        response = requests.post(
            f"{API_BASE_URL}/orders/bulk", 
            headers=headers, 
            json={"orders": orders_payload}
        )
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("status") == "ok":
            print("✅ Bulk order request processed successfully.")
            # Pretty-print the full response from the server for confirmation
            print("""Server Response:
{}""".format(json.dumps(response_data.get('data'), indent=2)))
        else:
            error_msg = response_data.get('message', 'Unknown error')
            print(f"❌ Bulk order failed. Reason: {error_msg}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Bulk order failed. HTTP Error: {e}")

    print("\n✅ All trades have been submitted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebalance portfolio by selling 25% of specified stocks with Market Orders.")
    parser.add_argument(
        '--execute',
        action='store_false',
        dest='dry_run',
        help="Actually execute the trades. Default is a dry run."
    )
    parser.add_argument(
        '--tickers',
        type=str,
        nargs='+',  # Accept one or more ticker symbols
        required=True,  # Make this argument mandatory
        help="One or more ticker symbols to process (e.g., --tickers AAPL TSLA)."
    )
    args = parser.parse_args()

    execute_market_order(dry_run=args.dry_run, target_tickers=args.tickers) 