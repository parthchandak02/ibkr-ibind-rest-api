"""
Health monitoring module for the IBKR REST API.

This module handles health status monitoring, caching, and Server-Sent Events (SSE)
for real-time health updates.
"""

import json
import logging
import queue
import threading
import time
import uuid
from typing import Dict, Generator

from flask import Response

from .utils import check_ibkr_health_status

logger = logging.getLogger(__name__)

# Global health status cache
_health_status_cache = {
    'status': 'checking',
    'ibkr_connected': False,
    'last_updated': time.time(),
    'error': None
}

# Queue for SSE events
sse_queues = {}


def get_cached_health_status() -> Dict:
    """Get the current cached health status."""
    return {
        "status": "healthy" if _health_status_cache['ibkr_connected'] else "unhealthy",
        "ibkr_connected": _health_status_cache['ibkr_connected'],
        "timestamp": _health_status_cache['last_updated'],
        "cache_age_seconds": time.time() - _health_status_cache['last_updated']
    }


def broadcast_sse_event(event_type: str, data: dict):
    """Broadcast an event to all connected SSE clients."""
    event = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    # Remove disconnected clients
    dead_clients = []
    for client_id, client_queue in sse_queues.items():
        try:
            client_queue.put_nowait(event)
        except queue.Full:
            dead_clients.append(client_id)
    
    # Clean up disconnected clients
    for client_id in dead_clients:
        sse_queues.pop(client_id, None)


def background_health_monitor():
    """Background task to monitor health and push updates via SSE."""
    while True:
        try:
            # Check IBKR health using cached client
            ibkr_healthy = check_ibkr_health_status()
            
            current_status = {
                'status': 'healthy' if ibkr_healthy else 'unhealthy',
                'ibkr_connected': ibkr_healthy,
                'last_updated': time.time(),
                'error': None
            }
            
            # Only broadcast if status changed
            if (current_status['ibkr_connected'] != _health_status_cache['ibkr_connected'] or
                current_status['status'] != _health_status_cache['status']):
                
                _health_status_cache.update(current_status)
                
                # Broadcast to all SSE clients
                event_data = {
                    'status': current_status['status'],
                    'ibkr_connected': current_status['ibkr_connected'],
                    'timestamp': current_status['last_updated']
                }
                
                broadcast_sse_event('health_update', event_data)
                logging.info(f"Health status changed: {current_status}")
            
            # Update cache
            _health_status_cache.update(current_status)
            
        except Exception as e:
            error_status = {
                'status': 'unhealthy',
                'ibkr_connected': False,
                'last_updated': time.time(),
                'error': str(e)
            }
            
            if _health_status_cache['ibkr_connected'] != error_status['ibkr_connected']:
                _health_status_cache.update(error_status)
                broadcast_sse_event('health_update', {
                    'status': error_status['status'],
                    'ibkr_connected': error_status['ibkr_connected'],
                    'timestamp': error_status['last_updated'],
                    'error': str(e)
                })
                
            logging.error(f"Health monitor error: {e}")
        
        # Wait 15 seconds before next check
        time.sleep(15)


def start_health_monitor():
    """Start background health monitor."""
    monitor_thread = threading.Thread(target=background_health_monitor, daemon=True)
    monitor_thread.start()
    logging.info("Background health monitor started")


def create_health_event_stream() -> Generator[str, None, None]:
    """Create SSE event stream for health updates."""
    client_id = str(uuid.uuid4())
    client_queue = queue.Queue(maxsize=10)
    sse_queues[client_id] = client_queue
    
    # Send current status immediately
    current_status = {
        'status': _health_status_cache['status'],
        'ibkr_connected': _health_status_cache['ibkr_connected'],
        'timestamp': _health_status_cache['last_updated'],
        'error': _health_status_cache.get('error')
    }
    yield f"event: health_update\ndata: {json.dumps(current_status)}\n\n"
    
    try:
        while True:
            try:
                # Wait for new events with timeout
                event = client_queue.get(timeout=30)
                yield event
            except queue.Empty:
                # Send keepalive
                yield f"event: keepalive\ndata: {json.dumps({'timestamp': time.time()})}\n\n"
    except GeneratorExit:
        # Clean up when client disconnects
        sse_queues.pop(client_id, None)


def create_health_sse_response() -> Response:
    """Create Flask Response for health SSE endpoint."""
    return Response(create_health_event_stream(), mimetype='text/event-stream') 