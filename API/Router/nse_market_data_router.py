#!/usr/bin/env python3
"""
NSE Market Data Router
======================
Unified FastAPI router for all NSE market data endpoints.
Provides read-only access to data collected by cron jobs and stored in MongoDB.

All endpoints return cached data from MongoDB collections.
Data is refreshed by background cron jobs running at configured intervals.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response_n, create_error_response

router = APIRouter()
logger = get_logger(__name__)


def convert_object_ids(doc: Any) -> Any:
    """Convert ObjectId instances to strings for JSON serialization."""
    if isinstance(doc, dict):
        return {k: convert_object_ids(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_object_ids(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc


def get_db():
    """Get DatabaseManager instance."""
    return DatabaseManager()


# ==================== TOP GAINERS & LOSERS ====================

@router.get("/gainers-losers", tags=["Market Analysis"])
async def get_top_gainers_losers(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'NIFTY 50', 'NIFTY NEXT 50', 'NIFTY BANK')"),
    data_type: Optional[str] = Query(None, description="Filter by type ('gainers' or 'losers')"),
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get top gainers and losers data from NSE.
    
    Data is collected every 7 minutes during market hours.
    Returns stocks with highest gains and losses across various indices.
    """
    try:
        db = get_db()
        query = {}
        
        if category:
            query["category"] = category
        if data_type:
            query["data_type"] = data_type.lower()
        
        data = db.get_collection_data(
            collection_name="nse_gainers_losers",
            query=query,
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No gainers/losers data available")
        
        return create_success_response_n({
            "endpoint": "gainers-losers",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching gainers/losers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 52 WEEK HIGH/LOW ====================

@router.get("/52week-high-low", tags=["Market Analysis"])
async def get_52_week_high_low(
    data_type: Optional[str] = Query(None, description="Filter by '52week_high' or '52week_low'"),
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get stocks at 52-week highs and lows.
    
    Data is collected every 8 minutes during market hours.
    Returns stocks touching their 52-week high or low prices.
    """
    try:
        db = get_db()
        query = {}
        
        if data_type:
            query["data_type"] = data_type
        
        data = db.get_collection_data(
            collection_name="nse_week_52_data",
            query=query,
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No 52-week high/low data available")
        
        return create_success_response_n({
            "endpoint": "52week-high-low",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching 52-week data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NSE INDICES ====================

@router.get("/indices", tags=["Indices"])
async def get_all_indices(
    index_name: Optional[str] = Query(None, description="Filter by index name (e.g., 'NIFTY 50', 'NIFTY BANK')"),
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get all NSE indices data with constituent stocks.
    
    Data is collected every 7 minutes during market hours.
    Returns index values, changes, and constituent stock data.
    """
    try:
        db = get_db()
        query = {}
        
        if index_name:
            query["index_name"] = index_name.upper()
        
        data = db.get_collection_data(
            collection_name="nse_indices_data",
            query=query,
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No indices data available")
        
        return create_success_response_n({
            "endpoint": "indices",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching indices data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADVANCES/DECLINES/UNCHANGED ====================

@router.get("/advances-declines", tags=["Market Analysis"])
async def get_advances_declines(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get market breadth data - advances, declines, and unchanged stocks.
    
    Data is collected every 8 minutes during market hours.
    Returns market breadth indicator showing overall market sentiment.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_advances_declines",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No advances/declines data available")
        
        return create_success_response_n({
            "endpoint": "advances-declines",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching advances/declines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOST ACTIVE EQUITIES ====================

@router.get("/most-active-equities", tags=["Market Analysis"])
async def get_most_active_equities(
    activity_type: Optional[str] = Query(None, description="Filter by 'volume' or 'value'"),
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get most actively traded equities by volume and value.
    
    Data is collected every 8 minutes during market hours.
    Returns stocks with highest trading volumes and values.
    """
    try:
        db = get_db()
        query = {}
        
        if activity_type:
            query["activity_type"] = activity_type.lower()
        
        data = db.get_collection_data(
            collection_name="nse_most_active_equities",
            query=query,
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No most active equities data available")
        
        return create_success_response_n({
            "endpoint": "most-active-equities",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching most active equities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOST ACTIVE CONTRACTS (F&O) ====================

@router.get("/most-active-contracts", tags=["F&O Data"])
async def get_most_active_contracts(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get most active F&O contracts by open interest and volume.
    
    Data is collected every 8 minutes during market hours.
    Returns futures and options contracts with highest activity.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_most_active_contracts",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No most active contracts data available")
        
        return create_success_response_n({
            "endpoint": "most-active-contracts",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching most active contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOST ACTIVE UNDERLYING (F&O) ====================

@router.get("/most-active-underlying", tags=["F&O Data"])
async def get_most_active_underlying(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get most active underlying securities in F&O segment.
    
    Data is collected every 7 minutes during market hours.
    Returns underlying stocks with highest derivative activity.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_most_active_underlying",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No most active underlying data available")
        
        return create_success_response_n({
            "endpoint": "most-active-underlying",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching most active underlying: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRICE BAND HITTERS ====================

@router.get("/price-band-hitters", tags=["Market Analysis"])
async def get_price_band_hitters(
    band_type: Optional[str] = Query(None, description="Filter by 'upper', 'lower', or 'both'"),
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get stocks hitting upper or lower price bands (circuit breakers).
    
    Data is collected every 7 minutes during market hours.
    Returns stocks at circuit limits.
    """
    try:
        db = get_db()
        query = {}
        
        if band_type:
            query["band_type"] = band_type.lower()
        
        data = db.get_collection_data(
            collection_name="nse_price_band_hitters",
            query=query,
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No price band hitters data available")
        
        return create_success_response_n({
            "endpoint": "price-band-hitters",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching price band hitters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LARGE DEALS ====================

@router.get("/large-deals", tags=["Market Analysis"])
async def get_large_deals(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get large institutional deals and bulk trades.
    
    Data is collected every 7 minutes during market hours.
    Returns significant trades by institutional investors.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_large_deals",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No large deals data available")
        
        return create_success_response_n({
            "endpoint": "large-deals",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching large deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW LISTINGS ====================

@router.get("/new-listings", tags=["Listings"])
async def get_new_listings(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get stocks newly listed today.
    
    Data is collected every 7 minutes during market hours.
    Returns IPOs and other new listings from today.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_new_listings",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No new listings data available")
        
        return create_success_response_n({
            "endpoint": "new-listings",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching new listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RECENT LISTINGS ====================

@router.get("/recent-listings", tags=["Listings"])
async def get_recent_listings(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get recently listed stocks (past few weeks).
    
    Data is collected every 8 minutes during market hours.
    Returns recent IPO listings with performance data.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_recent_listings",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No recent listings data available")
        
        return create_success_response_n({
            "endpoint": "recent-listings",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FORTHCOMING LISTINGS ====================

@router.get("/forthcoming-listings", tags=["Listings"])
async def get_forthcoming_listings(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get upcoming IPO listings scheduled for the near future.
    
    Data is collected every 8 minutes during market hours.
    Returns IPOs scheduled to list soon.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_forthcoming_listings",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No forthcoming listings data available")
        
        return create_success_response_n({
            "endpoint": "forthcoming-listings",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching forthcoming listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SPECIAL PREOPEN LISTINGS ====================

@router.get("/special-preopen-listings", tags=["Listings"])
async def get_special_preopen_listings(
    limit: Optional[int] = Query(None, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get special pre-open session listings data.
    
    Data is collected every 8 minutes during market hours.
    Returns stocks in special pre-open session.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="nse_special_preopen_listings",
            limit=limit,
            sort_by="timestamp",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No special pre-open listings data available")
        
        return create_success_response_n({
            "endpoint": "special-preopen-listings",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching special pre-open listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MANUAL REFRESH ENDPOINTS ====================
# These endpoints allow manual triggering of data scraping

import asyncio
from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController
from API.Controller.nse_all_indexes import NSEAllIndexesController
from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController
from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController
from API.Controller.most_active_contract import NSEMostActiveContractsController
from API.Controller.most_active_underlying import NSEMostActiveUnderlyingController
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController
from API.Controller.large_deal import NSELargeDealsController
from API.Controller.new_listing_stoks import NSENewListingsController
from API.Controller.recent_listing import NSERecentListingsController
from API.Controller.forth_comming_listing import NSEForthcomingListingsController
from API.Controller.special_preopen_listing import NSESpecialPreopenListingsController


@router.post("/refresh/gainers-losers", tags=["Manual Refresh"])
async def refresh_gainers_losers() -> Dict[str, Any]:
    """Manually trigger scraping of top gainers and losers data."""
    try:
        controller = NSETopGainersloosersController()
        result = await controller.scrap_top_gainers_loosers()
        return create_success_response_n({
            "endpoint": "refresh/gainers-losers",
            "message": "Gainers/Losers data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing gainers/losers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/52week-high-low", tags=["Manual Refresh"])
async def refresh_52week_high_low() -> Dict[str, Any]:
    """Manually trigger scraping of 52-week high/low data."""
    try:
        controller = NSE52WeekHighLowController()
        result = await controller.scrap_52week_high_low()
        return create_success_response_n({
            "endpoint": "refresh/52week-high-low",
            "message": "52-week high/low data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing 52-week data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/indices", tags=["Manual Refresh"])
async def refresh_indices() -> Dict[str, Any]:
    """Manually trigger scraping of all NSE indices data."""
    try:
        controller = NSEAllIndexesController()
        result = await controller.scrap_nse_all_indexes()
        return create_success_response_n({
            "endpoint": "refresh/indices",
            "message": "Indices data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/advances-declines", tags=["Manual Refresh"])
async def refresh_advances_declines() -> Dict[str, Any]:
    """Manually trigger scraping of advances/declines data."""
    try:
        controller = NSEAdvancesDeclinesUnchangedController()
        result = await controller.scrap_advance_decline_unchanged()
        return create_success_response_n({
            "endpoint": "refresh/advances-declines",
            "message": "Advances/Declines data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing advances/declines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/most-active-equities", tags=["Manual Refresh"])
async def refresh_most_active_equities() -> Dict[str, Any]:
    """Manually trigger scraping of most active equities data."""
    try:
        controller = NSEMostActiveEquitiesController()
        result = await controller.scrap_most_active_equities()
        return create_success_response_n({
            "endpoint": "refresh/most-active-equities",
            "message": "Most active equities data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing most active equities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/most-active-contracts", tags=["Manual Refresh"])
async def refresh_most_active_contracts() -> Dict[str, Any]:
    """Manually trigger scraping of most active F&O contracts data."""
    try:
        controller = NSEMostActiveContractsController()
        result = await controller.scrap_most_active_contracts()
        return create_success_response_n({
            "endpoint": "refresh/most-active-contracts",
            "message": "Most active contracts data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing most active contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/most-active-underlying", tags=["Manual Refresh"])
async def refresh_most_active_underlying() -> Dict[str, Any]:
    """Manually trigger scraping of most active underlying data."""
    try:
        controller = NSEMostActiveUnderlyingController()
        result = await controller.scrap_most_active_underlying()
        return create_success_response_n({
            "endpoint": "refresh/most-active-underlying",
            "message": "Most active underlying data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing most active underlying: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/price-band-hitters", tags=["Manual Refresh"])
async def refresh_price_band_hitters() -> Dict[str, Any]:
    """Manually trigger scraping of price band hitters data."""
    try:
        controller = NSEPriceBandHittersController()
        result = await controller.scrap_price_band_hitters()
        return create_success_response_n({
            "endpoint": "refresh/price-band-hitters",
            "message": "Price band hitters data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing price band hitters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/large-deals", tags=["Manual Refresh"])
async def refresh_large_deals() -> Dict[str, Any]:
    """Manually trigger scraping of large deals data."""
    try:
        controller = NSELargeDealsController()
        result = await controller.scrap_large_deals()
        return create_success_response_n({
            "endpoint": "refresh/large-deals",
            "message": "Large deals data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing large deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/new-listings", tags=["Manual Refresh"])
async def refresh_new_listings() -> Dict[str, Any]:
    """Manually trigger scraping of new listings data."""
    try:
        controller = NSENewListingsController()
        result = await controller.scrap_new_listings()
        return create_success_response_n({
            "endpoint": "refresh/new-listings",
            "message": "New listings data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing new listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/recent-listings", tags=["Manual Refresh"])
async def refresh_recent_listings() -> Dict[str, Any]:
    """Manually trigger scraping of recent listings data."""
    try:
        controller = NSERecentListingsController()
        result = await controller.scrap_recent_listings()
        return create_success_response_n({
            "endpoint": "refresh/recent-listings",
            "message": "Recent listings data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing recent listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/forthcoming-listings", tags=["Manual Refresh"])
async def refresh_forthcoming_listings() -> Dict[str, Any]:
    """Manually trigger scraping of forthcoming listings data."""
    try:
        controller = NSEForthcomingListingsController()
        result = await controller.scrap_forthcoming_listings()
        return create_success_response_n({
            "endpoint": "refresh/forthcoming-listings",
            "message": "Forthcoming listings data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing forthcoming listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/special-preopen-listings", tags=["Manual Refresh"])
async def refresh_special_preopen_listings() -> Dict[str, Any]:
    """Manually trigger scraping of special pre-open listings data."""
    try:
        controller = NSESpecialPreopenListingsController()
        result = await controller.scrap_special_preopen_listings()
        return create_success_response_n({
            "endpoint": "refresh/special-preopen-listings",
            "message": "Special pre-open listings data refreshed successfully",
            "result": result
        })
    except Exception as e:
        logger.error(f"Error refreshing special pre-open listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/all", tags=["Manual Refresh"])
async def refresh_all_data() -> Dict[str, Any]:
    """
    Manually trigger scraping of ALL NSE data sources.
    
    ⚠️ Warning: This may take several minutes to complete.
    """
    results = {}
    errors = []
    
    controllers = [
        ("gainers-losers", NSETopGainersloosersController, "scrap_top_gainers_loosers"),
        ("52week-high-low", NSE52WeekHighLowController, "scrap_52week_high_low"),
        ("indices", NSEAllIndexesController, "scrap_nse_all_indexes"),
        ("advances-declines", NSEAdvancesDeclinesUnchangedController, "scrap_advance_decline_unchanged"),
        ("most-active-equities", NSEMostActiveEquitiesController, "scrap_most_active_equities"),
        ("most-active-contracts", NSEMostActiveContractsController, "scrap_most_active_contracts"),
        ("most-active-underlying", NSEMostActiveUnderlyingController, "scrap_most_active_underlying"),
        ("price-band-hitters", NSEPriceBandHittersController, "scrap_price_band_hitters"),
        ("large-deals", NSELargeDealsController, "scrap_large_deals"),
        ("new-listings", NSENewListingsController, "scrap_new_listings"),
        ("recent-listings", NSERecentListingsController, "scrap_recent_listings"),
        ("forthcoming-listings", NSEForthcomingListingsController, "scrap_forthcoming_listings"),
        ("special-preopen-listings", NSESpecialPreopenListingsController, "scrap_special_preopen_listings"),
    ]
    
    for name, controller_class, method_name in controllers:
        try:
            controller = controller_class()
            method = getattr(controller, method_name)
            result = await method()
            results[name] = {"status": "success", "result": result}
            logger.info(f"Refreshed {name} successfully")
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            errors.append(name)
            logger.error(f"Error refreshing {name}: {e}")
    
    return create_success_response_n({
        "endpoint": "refresh/all",
        "message": f"Refresh completed. {len(controllers) - len(errors)}/{len(controllers)} succeeded.",
        "results": results,
        "errors": errors
    })
