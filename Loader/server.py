#!/usr/bin/env python3
"""
NSE Scraper API Server
======================
FastAPI server configuration with all API routers and documentation.

Features:
- Comprehensive NSE market data endpoints
- IPO data with GMP, subscription, and listing information
- ScanX stock analysis endpoints
- Stockwise event data
- Auto-generated API documentation at /docs and /redoc

Data Collection:
- Cron jobs run in background to collect real-time NSE data
- Market data collected every 7-8 minutes during market hours
- IPO data collected every 6 hours
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from Utils.logger import get_logger
from Utils.response import create_response
from Utils.monitor import get_all_services_health
from Constant.general import APP_NAME, APP_VERSION, APP_DESCRIPTION

# Import all routers
from API.Router import stoks_wise_event_data
from API.Router import scanx_scrap_stocks_data_by_symbol_router
from API.Router import scanx_stock_data_getter_router
from API.Router import nse_market_data_router
from API.Router import ipo_data_router

logger = get_logger(__name__)


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="NSE Scraper API",
        version="1.0.0",
        description="""
## NSE Data Scraper API

A comprehensive API for accessing real-time and historical NSE (National Stock Exchange) market data.

### 📊 Features

- **Market Analysis**: Top gainers/losers, 52-week highs/lows, advances/declines
- **Most Active**: Equities, F&O contracts, and underlying securities
- **Listings**: New, recent, forthcoming, and special pre-open listings
- **IPO Data**: GMP, subscription status, listing performance, company details
- **Stock Analysis**: ScanX data with financials, peer comparison, holdings

### ⏰ Data Refresh Intervals

| Data Type | Interval | Notes |
|-----------|----------|-------|
| Market Data | 7-8 min | During market hours (9:15 AM - 3:30 PM IST) |
| IPO Data | 6 hours | Runs 24/7 |
| Cookie Refresh | 4 min | For NSE session management |

### 🔗 Quick Links

- **Swagger UI**: [/docs](/docs)
- **ReDoc**: [/redoc](/redoc)
- **Health Check**: [/meta/health](/meta/health)

### 📝 Response Format

All endpoints return standardized responses:
```json
{
    "success": true,
    "message": "Success message",
    "data": { ... },
    "timestamp": "2025-01-01T10:00:00+05:30"
}
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Market Analysis",
                "description": "NSE market analysis endpoints - gainers, losers, 52-week data, price bands"
            },
            {
                "name": "Indices",
                "description": "NSE index data including NIFTY 50, NIFTY Bank, and 15+ other indices"
            },
            {
                "name": "F&O Data",
                "description": "Futures & Options market data - most active contracts and underlying"
            },
            {
                "name": "Listings",
                "description": "IPO listings - new, recent, forthcoming, and special pre-open"
            },
            {
                "name": "IPO Data",
                "description": "Comprehensive IPO information - GMP, subscription, company details, listing performance"
            },
            {
                "name": "ScanX Stock Data",
                "description": "Detailed stock data scraping and retrieval"
            },
            {
                "name": "ScanX Getter",
                "description": "Granular stock data sections - financials, holdings, forecasts"
            },
            {
                "name": "Stockwise Event Data",
                "description": "Corporate events, announcements, and actions for specific stocks"
            },
            {
                "name": "System",
                "description": "API health check and system status"
            }
        ]
    )
    
    # Add server info
    openapi_schema["servers"] = [
        {"url": "http://localhost:1020", "description": "Local Development"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def apiserver() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application with all routers
    """
    app = FastAPI(
        title="NSE Scraper API",
        description="Comprehensive NSE market data and IPO information API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict to specific domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================== REGISTER ROUTERS ====================
    
    # NSE Market Data (collected by cron jobs)
    app.include_router(
        nse_market_data_router.router, 
        prefix='/nse', 
        tags=['Market Analysis', 'Indices', 'F&O Data', 'Listings']
    )
    
    # IPO Data
    app.include_router(
        ipo_data_router.router, 
        prefix='/ipo', 
        tags=['IPO Data']
    )
    
    # ScanX Stock Data Scraper
    app.include_router(
        scanx_scrap_stocks_data_by_symbol_router.router, 
        prefix='/scanx', 
        tags=['ScanX Stock Data']
    )
    
    # ScanX Data Getter (granular sections)
    app.include_router(
        scanx_stock_data_getter_router.router, 
        prefix='/scanx/getter', 
        tags=['ScanX Getter']
    )
    
    # Stockwise Event Data
    app.include_router(
        stoks_wise_event_data.router, 
        prefix='/stoks-wise-event-data', 
        tags=['Stockwise Event Data']
    )

    # ==================== CORE ENDPOINTS ====================
    
    @app.get("/", tags=["System"])
    async def root():
        """
        Root endpoint - API welcome message and overview.
        
        Returns basic API information and links to documentation.
        """
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "message": "Welcome to NSE Scraper API",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_json": "/openapi.json"
            },
            "endpoints": {
                "market_data": "/nse",
                "ipo_data": "/ipo",
                "stock_analysis": "/scanx",
                "stockwise_events": "/stoks-wise-event-data",
                "health": "/meta/health"
            }
        }

    @app.get("/meta/health", tags=["System"])
    async def meta_health_check():
        """
        Health check endpoint - System and service status.
        
        Returns:
        - MongoDB connection status
        - Cron job status
        - Memory usage
        - Uptime information
        """
        return create_response(
            success=True,
            data=get_all_services_health(),
            message="Server health metadata"
        )
    
    @app.get("/api-endpoints", tags=["System"])
    async def list_api_endpoints():
        """
        List all available API endpoints with descriptions.
        
        Useful for programmatic discovery of available endpoints.
        """
        endpoints = {
            "nse_market_data": {
                "prefix": "/nse",
                "endpoints": [
                    {"path": "/nse/gainers-losers", "method": "GET", "description": "Top gainers and losers"},
                    {"path": "/nse/52week-high-low", "method": "GET", "description": "52-week highs and lows"},
                    {"path": "/nse/indices", "method": "GET", "description": "All NSE indices data"},
                    {"path": "/nse/advances-declines", "method": "GET", "description": "Market breadth data"},
                    {"path": "/nse/most-active-equities", "method": "GET", "description": "Most traded equities"},
                    {"path": "/nse/most-active-contracts", "method": "GET", "description": "Most active F&O contracts"},
                    {"path": "/nse/most-active-underlying", "method": "GET", "description": "Most active F&O underlying"},
                    {"path": "/nse/price-band-hitters", "method": "GET", "description": "Circuit breaker stocks"},
                    {"path": "/nse/large-deals", "method": "GET", "description": "Bulk/block deals"},
                    {"path": "/nse/new-listings", "method": "GET", "description": "Today's new listings"},
                    {"path": "/nse/recent-listings", "method": "GET", "description": "Recent IPO listings"},
                    {"path": "/nse/forthcoming-listings", "method": "GET", "description": "Upcoming listings"},
                    {"path": "/nse/special-preopen-listings", "method": "GET", "description": "Special pre-open data"},
                ]
            },
            "ipo_data": {
                "prefix": "/ipo",
                "endpoints": [
                    {"path": "/ipo/list", "method": "GET", "description": "All IPOs with filters"},
                    {"path": "/ipo/detail/{ipo_id}", "method": "GET", "description": "Single IPO details"},
                    {"path": "/ipo/open", "method": "GET", "description": "Currently open IPOs"},
                    {"path": "/ipo/upcoming", "method": "GET", "description": "Upcoming IPOs"},
                    {"path": "/ipo/listed", "method": "GET", "description": "Listed IPOs"},
                    {"path": "/ipo/gmp", "method": "GET", "description": "Grey Market Premium data"},
                    {"path": "/ipo/subscription", "method": "GET", "description": "Subscription status"},
                    {"path": "/ipo/year/{year}", "method": "GET", "description": "IPOs by year"},
                    {"path": "/ipo/search", "method": "GET", "description": "Search IPOs"},
                ]
            },
            "scanx_stock_data": {
                "prefix": "/scanx",
                "endpoints": [
                    {"path": "/scanx/get/stocks", "method": "GET", "description": "Get stock data by symbol(s)"},
                ]
            },
            "scanx_getter": {
                "prefix": "/scanx/getter",
                "endpoints": [
                    {"path": "/scanx/getter/company/about_company", "method": "GET", "description": "Company about info"},
                    {"path": "/scanx/getter/company/analyst_ratings", "method": "GET", "description": "Analyst ratings"},
                    {"path": "/scanx/getter/company/financials", "method": "GET", "description": "Financial bundle"},
                    {"path": "/scanx/getter/company/peer_comparison", "method": "GET", "description": "Peer comparison"},
                    {"path": "/scanx/getter/mf/holdings", "method": "GET", "description": "MF holdings"},
                    {"path": "/scanx/getter/mf/transactions", "method": "GET", "description": "MF transactions"},
                    {"path": "/scanx/getter/company/forecast_Q", "method": "GET", "description": "Quarterly forecasts"},
                    {"path": "/scanx/getter/company/forecast_A", "method": "GET", "description": "Annual forecasts"},
                ]
            },
            "stockwise_events": {
                "prefix": "/stoks-wise-event-data",
                "endpoints": [
                    {"path": "/stoks-wise-event-data/stoks_wise_event_data/{symbol}", "method": "GET", "description": "Stock events by symbol"},
                ]
            },
            "system": {
                "endpoints": [
                    {"path": "/", "method": "GET", "description": "API root/welcome"},
                    {"path": "/meta/health", "method": "GET", "description": "Health check"},
                    {"path": "/docs", "method": "GET", "description": "Swagger UI"},
                    {"path": "/redoc", "method": "GET", "description": "ReDoc"},
                ]
            }
        }
        
        return create_response(
            success=True,
            data=endpoints,
            message="Available API endpoints"
        )

    # Set custom OpenAPI schema
    app.openapi = lambda: custom_openapi(app)

    return app


def create_application() -> FastAPI:
    """
    Create FastAPI application for main.py integration.
    This is an alias for apiserver() for backward compatibility.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    return apiserver()
