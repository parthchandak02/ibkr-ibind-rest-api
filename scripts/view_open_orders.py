#!/usr/bin/env python3
"""
Interactive IBKR Orders Dashboard
A beautiful, interactive terminal application to view and manage open orders using Rich.
"""
import requests
import time
import sys
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.align import Align
from rich.columns import Columns
from rich import box

# Add backend to path for config access
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.config import Config

# Get API URL from config
config = Config()
API_URL = f"{config.get_api_base_url()}/orders"

class OrdersConfig:
    """Configuration for the orders dashboard"""
    REFRESH_INTERVAL = 5  # seconds
    SORT_OPTIONS = {
        '1': ('ticker', 'Ticker (A-Z)'),
        '2': ('side', 'Action (BUY/SELL)'),
        '3': ('totalSize', 'Quantity'),
        '4': ('orderType', 'Order Type'),
        '5': ('timeInForce', 'Time in Force'),
        '6': ('status', 'Status'),
        '7': ('orderId', 'Order ID')
    }

def create_header_panel() -> Panel:
    """Create a beautiful header panel"""
    header_text = Text()
    header_text.append("📊 IBKR Trading Dashboard ", style="bold cyan")
    header_text.append("• ", style="dim")
    header_text.append("Real-time Order Monitor", style="bold green")
    
    return Panel(
        Align.center(header_text),
        box=box.DOUBLE,
        style="bright_blue",
        title="[bold white]Interactive Brokers[/]",
        title_align="center"
    )

def create_stats_panel(orders: List[Dict]) -> Panel:
    """Create a statistics panel showing order summary"""
    if not orders:
        return Panel("[dim]No orders to display[/]", title="📈 Statistics")
    
    # Calculate statistics
    total_orders = len(orders)
    buy_orders = len([o for o in orders if o.get('side') == 'BUY'])
    sell_orders = len([o for o in orders if o.get('side') == 'SELL'])
    market_orders = len([o for o in orders if o.get('orderType') == 'Market'])
    limit_orders = len([o for o in orders if o.get('orderType') == 'Limit'])
    active_orders = len([o for o in orders if o.get('status') not in ['Cancelled', 'Filled']])
    
    stats_text = Text()
    stats_text.append(f"Total: {total_orders} ", style="bold white")
    stats_text.append(f"• Buy: {buy_orders} ", style="bold green")
    stats_text.append(f"• Sell: {sell_orders} ", style="bold red")
    stats_text.append(f"• Market: {market_orders} ", style="bold yellow")
    stats_text.append(f"• Limit: {limit_orders} ", style="bold blue")
    stats_text.append(f"• Active: {active_orders}", style="bold cyan")
    
    return Panel(
        Align.center(stats_text),
        box=box.ROUNDED,
        style="bright_green",
        title="📈 Order Statistics"
    )

def create_orders_table(orders: List[Dict], sort_by: str = 'ticker', reverse: bool = False) -> Table:
    """Create a beautifully formatted orders table with sorting"""
    
    # Sort orders based on the selected criteria
    def get_sort_value(order):
        value = order.get(sort_by, '')
        if sort_by == 'totalSize':
            return float(value) if value else 0
        elif sort_by == 'orderId':
            return int(value) if value else 0
        return str(value)
    
    try:
        sorted_orders = sorted(orders, key=get_sort_value, reverse=reverse)
    except (ValueError, TypeError):
        sorted_orders = orders  # Fallback to original order if sorting fails
    
    # Create table with beautiful styling
    table = Table(
        show_header=True, 
        header_style="bold magenta on black",
        border_style="bright_blue",
        box=box.HEAVY_HEAD,
        show_lines=True,
        expand=True
    )
    
    # Add columns with improved styling
    table.add_column("🎯 Ticker", style="bold cyan", no_wrap=True, width=10)
    table.add_column("📈 Action", justify="center", width=8)
    table.add_column("📊 Qty", style="bold yellow", justify="right", width=12)
    table.add_column("📋 Type", style="dim white", width=10)
    table.add_column("💰 Price", style="bold green", justify="right", width=12)
    table.add_column("⏰ TIF", justify="center", width=8)
    table.add_column("🔄 Status", justify="center", width=15)
    table.add_column("🔢 Order ID", style="dim", justify="right", width=12)
    
    # Group orders for better visual organization
    current_group = None
    for i, order in enumerate(sorted_orders):
        side = order.get("side", "N/A")
        status = order.get("status", "N/A")
        
        # Add visual separators for different groups
        if sort_by == 'side' and side != current_group:
            if current_group is not None:
                table.add_row("", "", "", "", "", "", "", "", style="dim")
            current_group = side
        
        # Style based on order status and type
        row_style = ""
        if status == "Cancelled":
            row_style = "dim red strike"
        elif status == "Filled":
            row_style = "dim green"
        elif side == "BUY":
            row_style = "bright_green"
        elif side == "SELL":
            row_style = "bright_red"
        
        # Format values with enhanced styling
        ticker = order.get('ticker', 'N/A')
        action_icon = "🟢" if side == "BUY" else "🔴"
        action_text = f"{action_icon} {side}"
        
        # Format quantity
        if order.get('cashQty'):
            quantity = f"${order['cashQty']:,.0f}"
        else:
            quantity = f"{order.get('totalSize', 0):,.0f}"
        
        # Format price
        price_value = order.get('price', 0)
        if price_value:
            price = f"${float(price_value):.2f}"
        else:
            price = "Market"
        
        # Format time in force
        tif = order.get('timeInForce', 'CLOSE')
        tif_icon = "⏰" if tif == "GTC" else "🕐"
        tif_text = f"{tif_icon} {tif}"
        
        # Format status with icons
        status_icons = {
            'PreSubmitted': '⏳',
            'Submitted': '📤',
            'Filled': '✅',
            'Cancelled': '❌',
            'PendingCancel': '⏸️'
        }
        status_icon = status_icons.get(status, '❓')
        status_text = f"{status_icon} {status}"
        
        table.add_row(
            ticker,
            action_text,
            quantity,
            order.get('orderType', 'Market'),
            price,
            tif_text,
            status_text,
            str(order.get('orderId', 'N/A')),
            style=row_style
        )
    
    return table

def fetch_orders() -> List[Dict]:
    """Fetch orders from the API with error handling"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok" or "data" not in data:
            return []
        
        return data.get("data", {}).get("orders", [])
    except requests.exceptions.RequestException:
        return []

def create_controls_panel() -> Panel:
    """Create a controls panel showing available commands"""
    controls_text = Text()
    controls_text.append("Controls: ", style="bold white")
    controls_text.append("[1-7] ", style="bold yellow")
    controls_text.append("Sort • ", style="dim")
    controls_text.append("[R] ", style="bold yellow")
    controls_text.append("Reverse • ", style="dim")
    controls_text.append("[Space] ", style="bold yellow")
    controls_text.append("Refresh • ", style="dim")
    controls_text.append("[A] ", style="bold yellow")
    controls_text.append("Auto-refresh • ", style="dim")
    controls_text.append("[Q] ", style="bold yellow")
    controls_text.append("Quit", style="dim")
    
    return Panel(
        Align.center(controls_text),
        box=box.ROUNDED,
        style="bright_yellow",
        title="🎮 Interactive Controls"
    )

def interactive_dashboard():
    """Run the interactive orders dashboard"""
    console = Console()
    
    # Initialize state
    current_sort = 'ticker'
    reverse_sort = False
    auto_refresh = False
    last_refresh = 0
    
    try:
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            while True:
                current_time = time.time()
                
                # Auto-refresh logic
                if auto_refresh and (current_time - last_refresh) >= OrdersConfig.REFRESH_INTERVAL:
                    last_refresh = current_time
                
                # Fetch orders
                orders = fetch_orders()
                
                # Create layout
                layout = Layout()
                layout.split_column(
                    Layout(create_header_panel(), size=3),
                    Layout(create_stats_panel(orders), size=3),
                    Layout(create_controls_panel(), size=3),
                    Layout(name="main")
                )
                
                # Add orders table or empty message
                if orders:
                    orders_table = create_orders_table(orders, current_sort, reverse_sort)
                    sort_info = Panel(
                        f"[bold white]Sorted by: [cyan]{OrdersConfig.SORT_OPTIONS.get(str(list(OrdersConfig.SORT_OPTIONS.keys())[list(v[0] for v in OrdersConfig.SORT_OPTIONS.values()).index(current_sort)] if current_sort in [v[0] for v in OrdersConfig.SORT_OPTIONS.values()] else '1'), ('ticker', 'Ticker'))[1]}[/] {'(Descending)' if reverse_sort else '(Ascending)'} • [yellow]Last Updated: {datetime.now().strftime('%H:%M:%S')}[/]",
                        box=box.ROUNDED,
                        style="dim"
                    )
                    layout["main"].split_column(
                        Layout(sort_info, size=3),
                        Layout(orders_table)
                    )
                else:
                    empty_panel = Panel(
                        Align.center(Text("No orders found\n\nPress [Space] to refresh", style="dim")),
                        box=box.ROUNDED,
                        style="dim"
                    )
                    layout["main"] = Layout(empty_panel)
                
                live.update(layout)
                
                # Handle user input (non-blocking)
                if console.input.ready():
                    key = console.input.read_key()
                    
                    if key.lower() == 'q':
                        break
                    elif key in '1234567':
                        option = OrdersConfig.SORT_OPTIONS.get(key)
                        if option:
                            current_sort = option[0]
                    elif key.lower() == 'r':
                        reverse_sort = not reverse_sort
                    elif key == ' ':  # Space for manual refresh
                        last_refresh = current_time
                    elif key.lower() == 'a':
                        auto_refresh = not auto_refresh
                        if auto_refresh:
                            last_refresh = current_time
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[bold green]✨ Thanks for using IBKR Orders Dashboard![/bold green]")

def display_orders():
    """Legacy function - redirects to interactive dashboard"""
    console = Console()
    
    # Show sort options menu
    console.print(create_header_panel())
    console.print()
    
    console.print(Panel(
        "[bold white]Sort Options:[/bold white]\n" + 
        "\n".join([f"[bold yellow]{k}[/bold yellow] - {v[1]}" for k, v in OrdersConfig.SORT_OPTIONS.items()]) +
        "\n\n[dim]Press [bold]Enter[/bold] for interactive mode or choose a number:[/dim]",
        title="📊 Sorting Options",
        box=box.ROUNDED
    ))
    
    choice = Prompt.ask(
        "Select sort option (1-7) or press Enter for interactive mode",
        choices=list(OrdersConfig.SORT_OPTIONS.keys()) + [""],
        default=""
    )
    
    if choice == "":
        interactive_dashboard()
    else:
        # Simple static display
        orders = fetch_orders()
        if orders:
            sort_by = OrdersConfig.SORT_OPTIONS[choice][0]
            table = create_orders_table(orders, sort_by)
            console.print(create_stats_panel(orders))
            console.print(table)
        else:
            console.print("[bold red]❌ No orders found or error connecting to API.[/bold red]")

if __name__ == "__main__":
    display_orders() 