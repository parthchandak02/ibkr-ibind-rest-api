#!/usr/bin/env python3
"""
Cancel Duplicate Orders Script

A beautiful, interactive script to identify and cancel duplicate IBKR orders.
Uses the Rich library for gorgeous terminal output with progress tracking.
"""
import requests
import time
from typing import List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import box

# Configuration
API_URL = "http://localhost:8080"
API_KEY = "YOUR_API_KEY_PLACEHOLDER"

console = Console()

def get_orders() -> List[Dict]:
    """Fetch all orders from the API."""
    try:
        response = requests.get(f"{API_URL}/orders", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("orders", [])
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error fetching orders: {e}[/bold red]")
        return []

def find_duplicates(orders: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """Find duplicate orders - returns list of (keep_order, cancel_order) tuples."""
    duplicates = []
    processed = set()
    
    for i, order1 in enumerate(orders):
        if i in processed or order1.get('status') == 'Cancelled':
            continue
            
        for j, order2 in enumerate(orders[i+1:], i+1):
            if j in processed or order2.get('status') == 'Cancelled':
                continue
                
            # Check if orders are duplicates (same symbol, side, quantity, order type)
            if (order1.get('ticker') == order2.get('ticker') and
                order1.get('side') == order2.get('side') and
                order1.get('totalSize') == order2.get('totalSize') and
                order1.get('orderType') == order2.get('orderType') and
                order1.get('timeInForce') == order2.get('timeInForce')):
                
                # For limit orders, also check price
                if order1.get('orderType') == 'Limit':
                    if order1.get('price') != order2.get('price'):
                        continue
                
                # Determine which to keep (older order ID = keep)
                if int(order1.get('orderId', 0)) < int(order2.get('orderId', 0)):
                    duplicates.append((order1, order2))  # Keep order1, cancel order2
                else:
                    duplicates.append((order2, order1))  # Keep order2, cancel order1
                
                processed.add(j)
                break
                
        if i not in processed:
            processed.add(i)
    
    return duplicates

def display_duplicates_table(duplicates: List[Tuple[Dict, Dict]]) -> Table:
    """Create a beautiful table showing duplicate orders."""
    table = Table(title="🔍 Duplicate Orders Found", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Side", justify="center")
    table.add_column("Qty", style="yellow", justify="right")
    table.add_column("Type", style="dim")
    table.add_column("Price", style="green", justify="right")
    table.add_column("TIF", justify="center")
    table.add_column("Action", justify="center")
    table.add_column("Order ID", style="dim", justify="right")
    
    for keep_order, cancel_order in duplicates:
        # Add the order to keep (green)
        side = keep_order.get('side', 'N/A')
        side_style = "bold green" if side == "BUY" else "bold red"
        
        price_val = keep_order.get('price', 0)
        price_str = f"${float(price_val):.2f}" if price_val else "Market"
        
        tif = keep_order.get('timeInForce', 'N/A')
        tif_styled = f"[bold blue]{tif}[/bold blue]" if tif == "GTC" else f"[dim yellow]{tif}[/dim yellow]"
        
        table.add_row(
            keep_order.get('ticker', 'N/A'),
            f"[{side_style}]{side}[/]",
            f"{keep_order.get('totalSize', 0):,.0f}",
            keep_order.get('orderType', 'N/A'),
            price_str,
            tif_styled,
            "[bold green]✅ KEEP[/bold green]",
            str(keep_order.get('orderId', 'N/A'))
        )
        
        # Add the order to cancel (red)
        cancel_price_val = cancel_order.get('price', 0)
        cancel_price_str = f"${float(cancel_price_val):.2f}" if cancel_price_val else "Market"
        
        table.add_row(
            cancel_order.get('ticker', 'N/A'),
            f"[{side_style}]{cancel_order.get('side', 'N/A')}[/]",
            f"{cancel_order.get('totalSize', 0):,.0f}",
            cancel_order.get('orderType', 'N/A'),
            cancel_price_str,
            tif_styled,
            "[bold red]❌ CANCEL[/bold red]",
            str(cancel_order.get('orderId', 'N/A'))
        )
        
        # Add separator
        table.add_row("", "", "", "", "", "", "", "")
    
    return table

def cancel_order(order_id: str) -> bool:
    """Cancel a specific order by ID."""
    try:
        response = requests.delete(
            f"{API_URL}/order/{order_id}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("status") == "ok"
    except requests.exceptions.RequestException:
        return False

def main():
    """Main function to run the duplicate cancellation process."""
    console.print(Panel.fit(
        "[bold cyan]🚀 IBKR Duplicate Order Cancellation Tool[/bold cyan]\n"
        "[dim]Powered by Rich Python Library[/dim]",
        border_style="cyan"
    ))
    
    # Step 1: Fetch orders
    with console.status("[bold green]Fetching orders from IBKR API...", spinner="dots"):
        orders = get_orders()
    
    if not orders:
        console.print("[bold red]❌ No orders found or failed to fetch orders![/bold red]")
        return
    
    console.print(f"[bold green]✅ Found {len(orders)} total orders[/bold green]")
    
    # Step 2: Find duplicates
    with console.status("[bold yellow]🔍 Analyzing orders for duplicates...", spinner="dots"):
        duplicates = find_duplicates(orders)
    
    if not duplicates:
        console.print(Panel(
            "[bold green]🎉 No duplicate orders found!\n"
            "All orders are unique.[/bold green]",
            title="✅ Success",
            border_style="green"
        ))
        return
    
    # Step 3: Display duplicates
    console.print(f"\n[bold yellow]⚠️  Found {len(duplicates)} duplicate pairs![/bold yellow]")
    
    duplicates_table = display_duplicates_table(duplicates)
    console.print(duplicates_table)
    
    # Step 4: Confirm cancellation
    orders_to_cancel = [cancel_order for _, cancel_order in duplicates]
    
    console.print(Panel(
        f"[bold yellow]About to cancel {len(orders_to_cancel)} duplicate orders[/bold yellow]\n"
        "[dim]Keeping the older order from each duplicate pair[/dim]",
        title="⚠️  Confirmation Required",
        border_style="yellow"
    ))
    
    if not Confirm.ask("[bold red]Do you want to proceed with cancelling these duplicate orders?[/bold red]"):
        console.print("[bold blue]👍 Cancellation aborted by user.[/bold blue]")
        return
    
    # Step 5: Cancel orders with progress tracking
    console.print("\n[bold red]🚫 Cancelling duplicate orders...[/bold red]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        
        cancel_task = progress.add_task("[red]Cancelling orders...", total=len(orders_to_cancel))
        
        cancelled_count = 0
        failed_count = 0
        
        for order in orders_to_cancel:
            order_id = order.get('orderId')
            ticker = order.get('ticker', 'Unknown')
            
            progress.update(cancel_task, description=f"[red]Cancelling {ticker} (ID: {order_id})")
            
            if cancel_order(str(order_id)):
                cancelled_count += 1
                progress.console.print(f"  [bold green]✅ Cancelled {ticker} order {order_id}[/bold green]")
            else:
                failed_count += 1
                progress.console.print(f"  [bold red]❌ Failed to cancel {ticker} order {order_id}[/bold red]")
            
            progress.update(cancel_task, advance=1)
            time.sleep(0.5)  # Be polite to the API
    
    # Step 6: Summary
    if failed_count == 0:
        console.print(Panel(
            f"[bold green]🎉 Successfully cancelled all {cancelled_count} duplicate orders![/bold green]\n"
            "[dim]Your trading account is now clean of duplicates.[/dim]",
            title="✅ Complete Success",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]⚠️  Partially completed:[/bold yellow]\n"
            f"[green]✅ Successfully cancelled: {cancelled_count}[/green]\n"
            f"[red]❌ Failed to cancel: {failed_count}[/red]",
            title="⚠️  Partial Success",
            border_style="yellow"
        ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Cancelled by user[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]💥 Unexpected error: {e}[/bold red]") 