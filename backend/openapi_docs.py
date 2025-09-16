"""
Lightweight OpenAPI Documentation for IBKR API
"""

from flask import jsonify


def generate_openapi_spec():
    """Generate minimal OpenAPI 3.1 specification"""
    
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "IBKR Trading API",
            "version": "1.0.0",
            "description": "REST API for Interactive Brokers trading with auto-generated documentation."
        },
        "servers": [{"url": "http://localhost:8080"}],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header", 
                    "name": "X-API-Key"
                }
            }
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {"200": {"description": "Health status"}}
                }
            },
            "/account": {
                "get": {
                    "summary": "Account Information",
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {"200": {"description": "Account data with positions"}}
                }
            },
            "/positions": {
                "get": {
                    "summary": "Portfolio Positions",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 10}
                        }
                    ],
                    "responses": {"200": {"description": "Position data"}}
                }
            },
            "/resolve/{symbol}": {
                "get": {
                    "summary": "Resolve Symbol to Contract ID",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Contract ID"}}
                }
            },
            "/order": {
                "post": {
                    "summary": "Place Order",
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {"200": {"description": "Order placed"}}
                }
            },
            "/percentage-limit-order/{symbol}": {
                "post": {
                    "summary": "Percentage-Based Order",
                    "security": [{"ApiKeyAuth": []}],
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Order placed"}}
                }
            }
        }
    }


# Simple HTML templates
SWAGGER_UI_HTML = """<!DOCTYPE html>
<html><head><title>IBKR API Documentation</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.presets.standalone]
});
</script></body></html>"""

REDOC_HTML = """<!DOCTYPE html>
<html><head><title>IBKR API Documentation</title></head><body>
<redoc spec-url='/openapi.json'></redoc>
<script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body></html>"""


def add_openapi_routes(app):
    """Add lightweight OpenAPI documentation routes"""
    
    @app.route('/openapi.json')
    def openapi_json():
        return jsonify(generate_openapi_spec())
    
    @app.route('/docs')
    def swagger_ui():
        return SWAGGER_UI_HTML
    
    @app.route('/redoc')
    def redoc_ui():
        return REDOC_HTML
    
    @app.route('/docs-info')
    def docs_info():
        return jsonify({
            "message": "🚀 IBKR Trading API Documentation",
            "available_interfaces": {
                "swagger_ui": {"url": "/docs", "description": "Interactive API testing"},
                "redoc": {"url": "/redoc", "description": "Beautiful documentation"},
                "openapi_json": {"url": "/openapi.json", "description": "OpenAPI specification"}
            }
        })