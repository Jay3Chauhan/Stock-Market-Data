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
