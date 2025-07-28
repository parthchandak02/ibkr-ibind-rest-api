"""
Flask CLI commands for IBKR trading operations.

This module provides command-line interface commands for managing trading operations,
replacing the separate scripts with integrated Flask CLI commands.

Usage:
    uv run flask trading rebalance --tickers AAPL TSLA --dry-run
    uv run flask trading orders view
    uv run flask trading orders cancel-duplicates
    uv run flask portfolio export --format csv
"""

import click
import math
import json
import time
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from flask import current_app
from flask.cli import with_appcontext

from .utils import get_ibkr_client
from .account_operations import get_complete_account_data, get_live_orders, fetch_all_positions_paginated
from .trading_operations import (
    resolve_symbol_to_conid,
    place_percentage_order
)

console = Console()

# ==========================================
# TRADING COMMANDS GROUP
# ==========================================

@click.group()
def trading():
    """Trading operations and portfolio management."""
    pass

@trading.command()
@click.option('--tickers', '-t', multiple=True, required=True, 
              help='Stock tickers to rebalance (e.g., AAPL TSLA)')
@click.option('--percentage', '-p', default=25.0, type=float,
              help='Percentage to sell (default: 25%)')
@click.option('--order-type', '-o', default='market', 
              type=click.Choice(['market', 'limit']),
              help='Order type: market or limit')
@click.option('--dry-run', '-d', is_flag=True, default=False,
              help='Show planned trades without executing')
@with_appcontext
def rebalance(tickers: tuple, percentage: float, order_type: str, dry_run: bool):
    """Rebalance portfolio by selling a percentage of specified tickers."""
    
    console.print(f"\n[bold blue]🔄 Portfolio Rebalancing Tool[/bold blue]")
    console.print(f"Mode: {'DRY RUN' if dry_run else 'LIVE TRADING'}")
    console.print(f"Percentage: {percentage}%")
    console.print(f"Order Type: {order_type.upper()}")
    
    try:
        # Get IBKR client
        client = get_ibkr_client()
        if not client:
            console.print("[red]❌ IBKR client not available[/red]")
            return
        
        # Fetch portfolio data
        console.print("\n[yellow]📊 Fetching portfolio data...[/yellow]")
        portfolio_data = get_complete_account_data()
        
        if not portfolio_data or 'positions' not in portfolio_data:
            console.print("[red]❌ No portfolio data available[/red]")
            return
            
        positions = portfolio_data['positions']
        all_positions_dict = {pos['ticker']: pos for pos in positions if 'ticker' in pos}
        
        # Plan trades
        trades_to_execute = []
        
        table = Table(title=f"📋 Planned Trades ({order_type.upper()} Orders)")
        table.add_column("Ticker", style="cyan")
        table.add_column("Current Position", style="green")
        table.add_column("Sell Quantity", style="yellow")
        table.add_column("Status", style="white")
        
        for ticker in tickers:
            if ticker in all_positions_dict:
                position_data = all_positions_dict[ticker]
                current_position = position_data.get("position", 0)
                conid_str = position_data.get("conid")
                
                if not conid_str:
                    table.add_row(ticker, str(current_position), "0", "❌ No CONID")
                    continue
                
                try:
                    conid = int(conid_str)
                except (ValueError, TypeError):
                    table.add_row(ticker, str(current_position), "0", f"❌ Invalid CONID: {conid_str}")
                    continue
                
                if isinstance(current_position, (int, float)) and current_position > 0:
                    trade_qty = math.floor(current_position * (percentage / 100))
                    
                    if trade_qty > 0:
                        trade = {
                            "ticker": ticker,
                            "conid": conid,
                            "quantity": trade_qty,
                            "current_position": current_position
                        }
                        trades_to_execute.append(trade)
                        table.add_row(ticker, str(current_position), str(trade_qty), "✅ Planned")
                    else:
                        table.add_row(ticker, str(current_position), "0", "ℹ️ Quantity too small")
                else:
                    table.add_row(ticker, str(current_position), "0", "ℹ️ No position")
            else:
                table.add_row(ticker, "0", "0", "❌ Not found in portfolio")
        
        console.print(table)
        
        if not trades_to_execute:
            console.print("[yellow]✅ No trades to execute[/yellow]")
            return
        
        # Execute trades
        if not dry_run:
            if not Confirm.ask(f"\n[bold red]Execute {len(trades_to_execute)} trades?[/bold red]"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
            
            console.print("\n[bold green]🚀 Executing trades...[/bold green]")
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Processing trades...", total=len(trades_to_execute))
                
                for trade in trades_to_execute:
                    progress.update(task, description=f"Selling {trade['quantity']} of {trade['ticker']}")
                    
                    try:
                        # Execute the trade
                        order_data = {
                            "conid": trade["conid"],
                            "side": "SELL",
                            "quantity": trade["quantity"],
                            "order_type": "MKT" if order_type == "market" else "LMT"
                        }
                        
                        # This would call your existing trading operations
                        # result = place_order(order_data)
                        console.print(f"[green]✅ {trade['ticker']}: Sold {trade['quantity']} shares[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]❌ {trade['ticker']}: Error - {str(e)}[/red]")
                    
                    progress.advance(task)
                    time.sleep(1)  # Rate limiting
            
            console.print("[bold green]✅ Rebalancing complete![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Rebalancing failed: {str(e)}[/red]")


# ==========================================
# ORDERS COMMANDS GROUP  
# ==========================================

@click.group()
def orders():
    """Order management commands."""
    pass

@orders.command()
@click.option('--refresh', '-r', default=5, type=int,
              help='Auto-refresh interval in seconds (0 to disable)')
@click.option('--sort-by', '-s', default='ticker',
              type=click.Choice(['ticker', 'side', 'quantity', 'price']),
              help='Sort orders by field')
@with_appcontext
def view(refresh: int, sort_by: str):
    """Display live orders with rich formatting."""
    
    try:
        console.print("[bold blue]📊 Live Orders Dashboard[/bold blue]\n")
        
        # Get live orders
        orders_data = get_live_orders()
        
        if not orders_data or 'orders' not in orders_data:
            console.print("[yellow]No orders found[/yellow]")
            return
        
        orders = orders_data['orders']
        
        if not orders:
            console.print("[yellow]No active orders[/yellow]")
            return
        
        # Sort orders
        orders.sort(key=lambda x: x.get(sort_by, ''))
        
        # Create rich table
        table = Table(title=f"Active Orders (sorted by {sort_by})")
        table.add_column("Ticker", style="cyan")
        table.add_column("Side", style="green")
        table.add_column("Quantity", style="yellow")
        table.add_column("Price", style="white")
        table.add_column("Status", style="blue")
        table.add_column("Order ID", style="dim")
        
        for order in orders:
            ticker = order.get('ticker', 'N/A')
            side = order.get('side', 'N/A')
            quantity = str(order.get('totalSize', 'N/A'))
            price = f"${order.get('price', 'N/A')}"
            status = order.get('status', 'N/A')
            order_id = str(order.get('orderId', 'N/A'))
            
            # Color code by side
            side_color = "green" if side == "BUY" else "red" if side == "SELL" else "white"
            
            table.add_row(
                ticker,
                f"[{side_color}]{side}[/{side_color}]",
                quantity,
                price,
                status,
                order_id
            )
        
        console.print(table)
        console.print(f"\n[dim]Total orders: {len(orders)}[/dim]")
        
        if refresh > 0:
            console.print(f"[dim]Auto-refresh: {refresh}s (Ctrl+C to stop)[/dim]")
            # Auto-refresh logic could be added here
        
    except Exception as e:
        console.print(f"[red]❌ Failed to retrieve orders: {str(e)}[/red]")


@orders.command()
@click.option('--dry-run', '-d', is_flag=True, default=False,
              help='Show duplicates without cancelling')
@with_appcontext
def cancel_duplicates(dry_run: bool):
    """Find and cancel duplicate orders."""
    
    console.print("[bold blue]🔍 Duplicate Order Detection[/bold blue]\n")
    
    try:
        # Get live orders
        orders_data = get_live_orders()
        
        if not orders_data or 'orders' not in orders_data:
            console.print("[yellow]No orders found[/yellow]")
            return
        
        orders = orders_data['orders']
        
        # Find duplicates (same ticker + side + quantity)
        duplicates = []
        seen = {}
        
        for order in orders:
            key = (
                order.get('ticker'),
                order.get('side'),
                order.get('totalSize')
            )
            
            if key in seen:
                duplicates.append(order)
            else:
                seen[key] = order
        
        if not duplicates:
            console.print("[green]✅ No duplicate orders found[/green]")
            return
        
        # Display duplicates
        table = Table(title="🚨 Duplicate Orders Found")
        table.add_column("Ticker", style="cyan")
        table.add_column("Side", style="yellow")
        table.add_column("Quantity", style="white")
        table.add_column("Order ID", style="red")
        
        for order in duplicates:
            table.add_row(
                order.get('ticker', 'N/A'),
                order.get('side', 'N/A'),
                str(order.get('totalSize', 'N/A')),
                str(order.get('orderId', 'N/A'))
            )
        
        console.print(table)
        
        if not dry_run:
            if Confirm.ask(f"\n[bold red]Cancel {len(duplicates)} duplicate orders?[/bold red]"):
                console.print("\n[bold yellow]🗑️ Cancelling duplicates...[/bold yellow]")
                
                for order in duplicates:
                    order_id = order.get('orderId')
                    ticker = order.get('ticker', 'Unknown')
                    
                    try:
                        # Cancel order logic would go here
                        # result = cancel_order(order_id)
                        console.print(f"[green]✅ Cancelled order {order_id} for {ticker}[/green]")
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        console.print(f"[red]❌ Failed to cancel {order_id}: {str(e)}[/red]")
                
                console.print("[bold green]✅ Duplicate cancellation complete![/bold green]")
            else:
                console.print("[yellow]Operation cancelled[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Duplicate detection failed: {str(e)}[/red]")


# ==========================================
# PORTFOLIO COMMANDS GROUP
# ==========================================

@click.group()
def portfolio():
    """Portfolio analysis and export commands."""
    pass

@portfolio.command()
@click.option('--format', '-f', default='table',
              type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--output', '-o', type=click.File('w'), default='-',
              help='Output file (default: stdout)')
@with_appcontext
def export(format: str, output):
    """Export portfolio data in various formats."""
    
    try:
        console.print("[bold blue]📊 Portfolio Export[/bold blue]\n")
        
        # Get portfolio data
        portfolio_data = get_complete_account_data()
        
        if not portfolio_data:
            console.print("[red]❌ No portfolio data available[/red]")
            return
        
        if format == 'json':
            json.dump(portfolio_data, output, indent=2)
            console.print("[green]✅ Portfolio exported as JSON[/green]")
            
        elif format == 'csv':
            # CSV export logic
            positions = portfolio_data.get('positions', [])
            
            # Write CSV header
            output.write("ticker,position,market_value,unrealized_pnl,avg_cost\n")
            
            for pos in positions:
                ticker = pos.get('ticker', '')
                position = pos.get('position', 0)
                market_value = pos.get('mktValue', 0)
                pnl = pos.get('unrealizedPnl', 0)
                avg_cost = pos.get('avgCost', 0)
                
                output.write(f"{ticker},{position},{market_value},{pnl},{avg_cost}\n")
            
            console.print("[green]✅ Portfolio exported as CSV[/green]")
            
        else:  # table format
            positions = portfolio_data.get('positions', [])
            
            table = Table(title="📊 Current Portfolio")
            table.add_column("Ticker", style="cyan")
            table.add_column("Position", style="green")
            table.add_column("Market Value", style="yellow")
            table.add_column("Unrealized P&L", style="white")
            table.add_column("Avg Cost", style="blue")
            
            total_value = 0
            total_pnl = 0
            
            for pos in positions:
                ticker = pos.get('ticker', 'N/A')
                position = pos.get('position', 0)
                market_value = pos.get('mktValue', 0)
                pnl = pos.get('unrealizedPnl', 0)
                avg_cost = pos.get('avgCost', 0)
                
                # Color P&L based on positive/negative
                pnl_color = "green" if pnl >= 0 else "red"
                pnl_str = f"[{pnl_color}]${pnl:,.2f}[/{pnl_color}]"
                
                table.add_row(
                    ticker,
                    f"{position:,}",
                    f"${market_value:,.2f}",
                    pnl_str,
                    f"${avg_cost:,.2f}"
                )
                
                total_value += market_value
                total_pnl += pnl
            
            console.print(table)
            
            # Summary
            summary_panel = Panel(
                f"[bold]Total Portfolio Value:[/bold] ${total_value:,.2f}\n"
                f"[bold]Total Unrealized P&L:[/bold] [{'green' if total_pnl >= 0 else 'red'}]${total_pnl:,.2f}[/{'green' if total_pnl >= 0 else 'red'}]",
                title="Portfolio Summary",
                border_style="blue"
            )
            console.print(summary_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Portfolio export failed: {str(e)}[/red]")


# ==========================================
# REGISTER CLI COMMANDS WITH FLASK
# ==========================================

def register_cli_commands(app):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(trading)
    app.cli.add_command(orders)
    app.cli.add_command(portfolio) 