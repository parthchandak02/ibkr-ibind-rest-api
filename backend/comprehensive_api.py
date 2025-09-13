"""
Comprehensive API Router for GitHub Actions Integration

This module provides a unified endpoint that can handle ANY backend operation
triggered remotely via GitHub Actions. It routes requests to appropriate
backend modules based on operation type.

Supports:
- Trading operations (buy, sell, rebalance)
- Portfolio management (view, export)
- Order management (view, cancel, history)
- Market data (quotes, prices, history)  
- Account operations (info, positions)
- Data export (CSV, JSON, Excel)
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import jsonify, request

from .auth import require_api_key
from .utils import get_ibkr_client
from .account_operations import get_complete_account_data, get_live_orders, fetch_all_positions_paginated
from .trading_operations import (
    resolve_symbol_to_conid,
    place_percentage_order,
    find_position_by_symbol,
    calculate_sell_quantity,
    calculate_buy_quantity,
    SymbolResolutionError,
    PositionNotFoundError
)
from .market_data import get_current_price_for_symbol, get_market_data_for_conids, MarketDataError
from .data_export import generate_positions_csv, get_positions_with_limit
from ibind import make_order_request, QuestionType

logger = logging.getLogger(__name__)


class ComprehensiveAPIRouter:
    """
    Unified router for all backend operations.
    
    This class provides a single entry point for GitHub Actions to trigger
    any backend functionality. It handles routing, validation, and response
    formatting in a consistent manner.
    """
    
    def __init__(self):
        self.operation_handlers = {
            'trading': self._handle_trading_operation,
            'portfolio': self._handle_portfolio_operation,
            'orders': self._handle_orders_operation,
            'market_data': self._handle_market_data_operation,
            'account': self._handle_account_operation,
            'data_export': self._handle_export_operation
        }
    
    def execute_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute any backend operation based on the provided data.
        
        Args:
            operation_data: Dictionary containing operation details
            
        Returns:
            Dictionary with operation results
            
        Raises:
            ValueError: If operation type is not supported
        """
        operation_type = operation_data.get('operation_type')
        
        if operation_type not in self.operation_handlers:
            raise ValueError(f"Unsupported operation type: {operation_type}")
        
        logger.info(f"Executing {operation_type} operation: {operation_data}")
        
        try:
            # Add metadata
            operation_data['execution_timestamp'] = datetime.utcnow().isoformat()
            operation_data['triggered_by'] = operation_data.get('triggered_by', 'api')
            
            # Route to appropriate handler
            handler = self.operation_handlers[operation_type]
            result = handler(operation_data)
            
            # Standardize response format
            return {
                'status': 'success',
                'operation_type': operation_type,
                'timestamp': operation_data['execution_timestamp'],
                'dry_run': operation_data.get('dry_run', False),
                'environment': operation_data.get('environment', 'paper'),
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Operation {operation_type} failed: {e}")
            return {
                'status': 'error',
                'operation_type': operation_type,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _handle_trading_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle all trading operations (buy, sell, rebalance, etc.)"""
        action = data.get('action', 'rebalance')
        symbol = data.get('symbol', 'AAPL')
        quantity = data.get('quantity', '1')
        price = data.get('price', '')
        dry_run = data.get('dry_run', True)
        
        logger.info(f"Trading operation: {action} {quantity} {symbol}")
        
        if dry_run:
            # Simulate the operation for safety
            return {
                'action': action,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'simulated': True,
                'message': f"DRY RUN: Would execute {action} {quantity} shares of {symbol}"
            }
        
        client = get_ibkr_client()
        if not client:
            raise Exception("IBKR client not available")
        
        try:
            # Resolve symbol to contract ID
            conid = resolve_symbol_to_conid(client, symbol)
            
            if action == 'rebalance':
                # Handle rebalancing (sell percentage)
                percentage = float(quantity)
                all_positions = fetch_all_positions_paginated()
                position = find_position_by_symbol(all_positions, symbol, conid)

                sell_quantity = calculate_sell_quantity(position, percentage, symbol)
                current_price = get_current_price_for_symbol(symbol, conid)
                limit_price = current_price

                result = place_percentage_order(
                    client=client,
                    symbol=symbol,
                    conid=conid,
                    side="SELL",
                    quantity=sell_quantity,
                    limit_price=limit_price,
                    time_in_force=data.get('time_in_force', 'GTC')
                )

                return {
                    'action': 'rebalance',
                    'symbol': symbol,
                    'percentage': percentage,
                    'quantity_sold': sell_quantity,
                    'limit_price': limit_price,
                    'result': result
                }
                
            elif action in ['buy', 'sell']:
                # Handle direct buy/sell orders
                side = action.upper()
                order_quantity = int(float(quantity))

                if price:
                    order_type = "LMT"
                    limit_price = float(price)
                else:
                    order_type = "MKT"
                    limit_price = None

                order_request = make_order_request(
                    conid=conid,
                    side=side,
                    quantity=order_quantity,
                    order_type=order_type,
                    price=limit_price,
                    acct_id=client.account_id,
                    tif=data.get('time_in_force', 'DAY'),
                )

                answers = {
                    QuestionType.PRICE_PERCENTAGE_CONSTRAINT: True,
                    QuestionType.ORDER_VALUE_LIMIT: True,
                    QuestionType.MISSING_MARKET_DATA: True,
                    QuestionType.STOP_ORDER_RISKS: True,
                    "Unforeseen new question": True,
                }

                result = client.place_order(order_request, answers)

                return {
                    'action': action,
                    'symbol': symbol,
                    'quantity': order_quantity,
                    'order_type': order_type,
                    'limit_price': limit_price,
                    'data': result.data
                }
            
            else:
                raise ValueError(f"Unknown trading action: {action}")
                
        except (SymbolResolutionError, PositionNotFoundError, MarketDataError) as e:
            raise Exception(f"Trading operation failed: {str(e)}")
    
    def _handle_portfolio_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle portfolio operations (view, summary, positions)"""
        action = data.get('action', 'view')
        format_type = data.get('format', 'json')
        
        logger.info(f"Portfolio operation: {action}")
        
        if action == 'view' or action == 'summary':
            # Get complete account data including positions
            account_data = get_complete_account_data()
            return {
                'action': action,
                'format': format_type,
                'account_data': account_data
            }
            
        elif action == 'positions':
            # Get just positions data
            positions = fetch_all_positions_paginated()
            return {
                'action': action,
                'format': format_type,
                'positions': positions,
                'total_positions': len(positions)
            }
            
        elif action == 'performance':
            # Get performance metrics (simplified)
            account_data = get_complete_account_data()
            positions = account_data.get('positions', [])
            
            total_value = sum(
                pos.get('market_value', 0) for pos in positions 
                if isinstance(pos.get('market_value'), (int, float))
            )
            
            return {
                'action': action,
                'format': format_type,
                'performance': {
                    'total_positions': len(positions),
                    'total_market_value': total_value,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        else:
            raise ValueError(f"Unknown portfolio action: {action}")
    
    def _handle_orders_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order operations (view, cancel, history)"""
        action = data.get('action', 'view')
        order_id = data.get('order_id', '')
        dry_run = data.get('dry_run', True)
        
        logger.info(f"Orders operation: {action}")
        
        if action == 'view' or action == 'history':
            # Get live orders
            orders_data = get_live_orders()
            return {
                'action': action,
                'orders': orders_data
            }
            
        elif action == 'cancel':
            if not order_id:
                raise ValueError("Order ID required for cancel operation")
            
            if dry_run:
                return {
                    'action': action,
                    'order_id': order_id,
                    'simulated': True,
                    'message': f"DRY RUN: Would cancel order {order_id}"
                }
            
            # TODO: Implement actual order cancellation
            # This would require additional IBKR API calls
            raise NotImplementedError("Order cancellation not yet implemented")
            
        elif action == 'cancel_all':
            if dry_run:
                orders_data = get_live_orders()
                order_count = len(orders_data.get('orders', []))
                return {
                    'action': action,
                    'simulated': True,
                    'message': f"DRY RUN: Would cancel {order_count} orders"
                }
            
            # TODO: Implement cancel all orders
            raise NotImplementedError("Cancel all orders not yet implemented")
            
        elif action == 'cancel_duplicates':
            if dry_run:
                return {
                    'action': action,
                    'simulated': True,
                    'message': "DRY RUN: Would identify and cancel duplicate orders"
                }
            
            # TODO: Implement duplicate order detection and cancellation
            raise NotImplementedError("Cancel duplicates not yet implemented")
        
        else:
            raise ValueError(f"Unknown orders action: {action}")
    
    def _handle_market_data_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle market data operations (quotes, prices, history)"""
        action = data.get('action', 'quote')
        symbol = data.get('symbol', 'AAPL')
        symbols_list = data.get('symbols_list', 'AAPL,TSLA')
        
        logger.info(f"Market data operation: {action} for {symbol}")
        
        if action == 'quote' or action == 'price':
            # Get single symbol quote
            client = get_ibkr_client()
            if not client:
                raise Exception("IBKR client not available")
            
            try:
                conid = resolve_symbol_to_conid(client, symbol)
                current_price = get_current_price_for_symbol(symbol, conid)
                
                return {
                    'action': action,
                    'symbol': symbol,
                    'conid': conid,
                    'price': current_price,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            except (SymbolResolutionError, MarketDataError) as e:
                raise Exception(f"Market data operation failed: {str(e)}")
        
        elif action == 'multiple_quotes':
            # Get quotes for multiple symbols
            symbols = [s.strip() for s in symbols_list.split(',') if s.strip()]
            
            client = get_ibkr_client()
            if not client:
                raise Exception("IBKR client not available")
            
            results = []
            for sym in symbols:
                try:
                    conid = resolve_symbol_to_conid(client, sym)
                    price = get_current_price_for_symbol(sym, conid)
                    results.append({
                        'symbol': sym,
                        'conid': conid,
                        'price': price,
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'symbol': sym,
                        'error': str(e),
                        'status': 'error'
                    })
            
            return {
                'action': action,
                'symbols': symbols,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        elif action == 'history':
            # TODO: Implement historical data retrieval
            return {
                'action': action,
                'symbol': symbol,
                'message': 'Historical data not yet implemented',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        else:
            raise ValueError(f"Unknown market data action: {action}")
    
    def _handle_account_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle account operations (info, summary)"""
        action = data.get('action', 'info')
        
        logger.info(f"Account operation: {action}")
        
        # All account operations return the complete account data
        account_data = get_complete_account_data()
        
        return {
            'action': action,
            'account_data': account_data
        }
    
    def _handle_export_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data export operations (CSV, JSON, Excel)"""
        format_type = data.get('format', 'csv')
        action = data.get('action', 'positions')
        
        logger.info(f"Export operation: {action} in {format_type} format")
        
        if action == 'positions':
            if format_type.lower() == 'csv':
                # Generate CSV response
                csv_response = generate_positions_csv()
                return {
                    'action': action,
                    'format': format_type,
                    'message': 'CSV generated successfully',
                    'content_type': 'text/csv'
                }
            else:
                # Get positions data for JSON/other formats
                positions = fetch_all_positions_paginated()
                return {
                    'action': action,
                    'format': format_type,
                    'positions': positions,
                    'total_positions': len(positions)
                }
        
        else:
            raise ValueError(f"Unknown export action: {action}")


# Global router instance
comprehensive_router = ComprehensiveAPIRouter()


def handle_comprehensive_request() -> Dict[str, Any]:
    """
    Flask route handler for comprehensive API requests.
    
    This function should be called from a Flask route that requires API key authentication.
    """
    try:
        # Parse request data
        if request.is_json:
            operation_data = request.get_json()
        else:
            operation_data = request.form.to_dict()
        
        if not operation_data:
            return jsonify({
                'status': 'error',
                'message': 'No operation data provided',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Execute the operation
        result = comprehensive_router.execute_operation(operation_data)
        
        # Return appropriate HTTP status code
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': 'validation_error',
            'timestamp': datetime.utcnow().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"Comprehensive API error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_type': 'internal_error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500 