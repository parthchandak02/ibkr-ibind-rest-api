# IBKR API Examples

This directory contains example scripts demonstrating various features of the IBKR API using the ibind library.

## Running Examples

**Important:** Always use a virtual environment when running these examples:

```bash
# From the project root directory
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Example Scripts

- `rest_01_basic.py` - Minimal example of using the IbkrClient class
- `rest_02_intermediate.py` - More advanced usage patterns
- `rest_03_stock_querying.py` - How to query stock information
- `rest_04_place_order.py` - How to place orders
- `rest_05_marketdata_history.py` - How to retrieve market data history
- `rest_06_options_chain.py` - How to work with options chains
- `rest_07_bracket_orders.py` - How to place bracket orders
- `rest_08_oauth.py` - How to use OAuth authentication
- `ws_01_basic.py` - Basic WebSocket example
- `ws_02_intermediate.py` - Intermediate WebSocket examples
- `ws_03_market_history.py` - Market history via WebSocket

## Security Notes

These examples follow best practices for security:
- Credentials are loaded from environment variables, not hardcoded
- OAuth keys are referenced by filepath, not included in code
- Trading mode (paper vs. live) is configurable

Never modify these examples to include your actual credentials or API keys directly in the code.
