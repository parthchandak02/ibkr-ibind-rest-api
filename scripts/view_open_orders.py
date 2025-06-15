#!/usr/bin/env python3
"""
A simple, fast, and reliable script to view open orders from the IBKR REST API.
Formats the output in a human-readable table using the 'rich' library.
"""
import requests
from rich.console import Console
from rich.table import Table

API_URL = "http://localhost:8080/orders"

def display_orders():
    """Fetches and displays open orders in a formatted table."""
    console = Console()

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error connecting to the API server at {API_URL}.[/bold red]")
        console.print(f"   Please ensure the server is running and accessible. Details: {e}")
        return

    if data.get("status") != "ok" or "data" not in data:
        console.print("[bold red]❌ Error: The API response was not successful or was malformed.[/bold red]")
        console.print(data.get("message", "No specific error message provided."))
        return

    orders = data.get("data", {}).get("orders", [])

    if not orders:
        console.print("[bold green]✅ No open orders found.[/bold green]")
        return

    console.print(f"[bold cyan]📊 Found {len(orders)} open order(s):[/bold cyan]")

    # Create a table for displaying orders
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Action", justify="center")
    table.add_column("Qty", style="yellow", justify="right")
    table.add_column("Order Type", style="dim")
    table.add_column("Price", style="green", justify="right")
    table.add_column("TIF", style="dim", justify="center")
    table.add_column("Status", justify="left")
    table.add_column("Order ID", style="dim", justify="right")

    # Sort orders by side (BUY/SELL) then by ticker
    orders.sort(key=lambda x: (x.get('side', ''), x.get('ticker', '')))

    for order in orders:
        # Determine action style based on BUY or SELL
        side = order.get("side", "N/A")
        action_style = "bold green" if side == "BUY" else "bold red"

        # Format quantity - check for cash quantity vs. share quantity
        if order.get('cashQty'):
            quantity_str = f"${order['cashQty']:,.0f}"
        else:
            quantity_str = f"{order.get('totalSize', 0):,.0f}"

        table.add_row(
            order.get("ticker", "N/A"),
            f"[{action_style}]{side}[/]",
            quantity_str,
            order.get("orderType", "N/A"),
            f"${float(order.get('price', 0)):.2f}" if order.get('price') else "Market",
            order.get("timeInForce", "N/A"),
            order.get("status", "N/A"),
            str(order.get("orderId", "N/A"))
        )

    console.print(table)

if __name__ == "__main__":
    display_orders() 