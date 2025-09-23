#!/usr/bin/env python3
"""Utility to place laddered limit buys from parth-buy-2.csv via API."""
from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table


CSV_PATH = "parth-buy-2.csv"
API_URL = "http://127.0.0.1:8082/order/symbol"
REQUEST_TIMEOUT = 20
REQUEST_PAUSE_SECONDS = 0.35  # throttle between API calls

# Symbols to submit (the focus subset approved by user)
TARGET_SYMBOLS = {
    "ISRA",
    "SHLD",
    "WAR",
    "PPA",
    "MISL",
    "AHR",
    "PLD",
    "EWT",
    "FLTW",
    "EWS",
}

console = Console()


@dataclass
class OrderSpec:
    symbol: str
    quantity: float
    price: float

    @property
    def quantity_display(self) -> str:
        return f"{int(self.quantity)}" if self.quantity.is_integer() else f"{self.quantity:.2f}"

    @property
    def price_display(self) -> str:
        return f"${self.price:.2f}"


@dataclass
class OrderResult:
    spec: OrderSpec
    status: str
    message: str
    success: bool
    order_tag: Optional[str] = None


def load_orders(csv_path: str) -> Dict[str, List[OrderSpec]]:
    """Return mapping of symbol -> ladder OrderSpec list for target symbols."""
    results: Dict[str, List[OrderSpec]] = {}
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().lower().startswith("no"):
                continue
            values = [cell.strip() for cell in row if cell.strip()]
            if len(values) < 4:
                continue
            symbol = values[2]
            if symbol not in TARGET_SYMBOLS:
                continue
            pairs = values[3:]
            if len(pairs) % 2 != 0:
                pairs = pairs[:-1]
            ladder: List[OrderSpec] = []
            for qty_raw, price_raw in zip(pairs[0::2], pairs[1::2]):
                try:
                    qty = float(qty_raw)
                    price = float(price_raw)
                except ValueError:
                    continue
                ladder.append(OrderSpec(symbol, qty, price))
            if ladder:
                results[symbol] = ladder
    return results


def _normalize_quantity(qty: float) -> float:
    return int(qty) if abs(qty - round(qty)) < 1e-6 else round(qty, 4)


def place_order(session: requests.Session, spec: OrderSpec) -> OrderResult:
    payload = {
        "symbol": spec.symbol,
        "side": "BUY",
        "order_type": "LMT",
        "quantity": _normalize_quantity(spec.quantity),
        "limit_price": round(spec.price, 2),
        "tif": "GTC",
    }
    try:
        response = session.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:  # noqa: BLE001
        return OrderResult(spec, "error", f"Network error: {exc}", False)

    # Attempt to extract message even on non-2xx responses
    message: str = ""
    order_tag: Optional[str] = None
    status_code = response.status_code
    try:
        data = response.json()
    except ValueError:
        data = None

    if data:
        message = data.get("message") or data.get("error") or ""
        order_tag = data.get("order_tag")
        # When API errors but provides structured details
        if "data" in data and isinstance(data["data"], dict):
            detail = data["data"].get("error") or data["data"].get("message")
            if detail:
                message = f"{message} | {detail}" if message else detail

    if not response.ok:
        if not message:
            message = response.text.strip() or f"HTTP {status_code}"
        return OrderResult(spec, f"HTTP {status_code}", message, False)

    status = data.get("status", "ok") if isinstance(data, dict) else "ok"
    message = message or "Order accepted"
    return OrderResult(spec, status, message, True, order_tag)


def render_symbol_summary(symbol: str, results: Iterable[OrderResult]) -> None:
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Qty", justify="right", style="bold yellow")
    table.add_column("Price", justify="right", style="bold green")
    table.add_column("Status", style="cyan")
    table.add_column("Message", overflow="fold")

    success_count = 0
    failure_count = 0
    for result in results:
        status_style = "bold green" if result.success else "bold red"
        status_text = result.status.upper()
        if result.order_tag:
            status_text += f" [{result.order_tag}]"
        table.add_row(
            result.spec.quantity_display,
            result.spec.price_display,
            f"[{status_style}]{status_text}[/{status_style}]",
            result.message or "-",
        )
        if result.success:
            success_count += 1
        else:
            failure_count += 1

    header = f"{symbol} — {success_count} succeeded, {failure_count} failed"
    console.print(Panel(table, title=header, title_align="left", border_style="bright_blue"))


def main() -> None:
    console.print(
        Panel(
            Align.center("Automated Ladder Placement", vertical="middle"),
            title="📈 IBKR Ladder Orders",
            border_style="bold purple",
        )
    )

    ladders = load_orders(CSV_PATH)
    if not ladders:
        console.print("[bold red]No matching symbols found in CSV.[/bold red]")
        sys.exit(1)

    session = requests.Session()
    overall_results: Dict[str, List[OrderResult]] = {}

    progress = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )

    with progress:
        for symbol, specs in ladders.items():
            task_id = progress.add_task(f"Placing orders for [cyan]{symbol}[/cyan]", total=len(specs))
            symbol_results: List[OrderResult] = []
            for spec in specs:
                result = place_order(session, spec)
                symbol_results.append(result)
                progress.advance(task_id)
                status_note = "success" if result.success else "error"
                progress.log(
                    f"[dim]{symbol}: {spec.quantity_display} @ {spec.price_display}[/dim] -> "
                    f"[{('green' if result.success else 'red')}]{status_note}[/] ({result.message or 'no message'})"
                )
                time.sleep(REQUEST_PAUSE_SECONDS)
            overall_results[symbol] = symbol_results

    console.print("\n[bold underline]Placement summary[/bold underline]\n")
    total_success = 0
    total_failure = 0
    for symbol, results in overall_results.items():
        render_symbol_summary(symbol, results)
        total_success += sum(1 for res in results if res.success)
        total_failure += sum(1 for res in results if not res.success)

    summary_table = Table(box=box.MINIMAL_HEAVY_HEAD)
    summary_table.add_column("Metric", style="bold cyan")
    summary_table.add_column("Count", justify="right", style="bold white")
    summary_table.add_row("Total orders", str(total_success + total_failure))
    summary_table.add_row("Succeeded", f"[green]{total_success}[/]")
    summary_table.add_row("Failed", f"[red]{total_failure}[/]")

    console.print(Panel(summary_table, title="Overall Result", border_style="bright_magenta"))

    if total_failure:
        console.print(
            "[bold yellow]⚠️ Some orders failed. Review messages above and retry as needed.[/bold yellow]"
        )
        sys.exit(1)

    console.print("[bold green]✅ All requested orders submitted successfully.[/bold green]")


if __name__ == "__main__":
    main()

