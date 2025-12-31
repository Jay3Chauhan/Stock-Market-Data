#!/usr/bin/env python3
"""
IPO Data Router
===============
FastAPI router for IPO (Initial Public Offering) data endpoints.
Provides access to comprehensive IPO data from InvestorGain.

Data is collected every 6 hours and stored in both MongoDB and SQL Server.
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


# ==================== IPO LIST ====================

@router.get("/list", tags=["IPO Data"])
async def get_ipo_list(
    status: Optional[str] = Query(None, description="Filter by status: 'Open', 'Closed', 'Upcoming', 'Listed', 'Allotment', etc."),
    year: Optional[int] = Query(None, description="Filter by IPO year (e.g., 2025)"),
    category: Optional[str] = Query(None, description="Filter by category: 'Mainboard', 'SME'"),
    limit: Optional[int] = Query(100, description="Limit number of results (default: 100)")
) -> Dict[str, Any]:
    """
    Get list of all IPOs with optional filters.
    
    Data is collected every 6 hours from InvestorGain.
    Returns comprehensive IPO information including GMP, subscription, and listing details.
    """
    try:
        db = get_db()
        query = {}
        
        if status:
            query["apiIpoStatusFormatted"] = {"$regex": status, "$options": "i"}
        if year:
            query["apiIpoYear"] = str(year)
        if category:
            query["apiIpoCategory"] = {"$regex": category, "$options": "i"}
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query=query,
            limit=limit,
            sort_by="lastUpdatedDb",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No IPO data available")
        
        return create_success_response_n({
            "endpoint": "ipo/list",
            "total_records": len(data),
            "filters": {
                "status": status,
                "year": year,
                "category": category
            },
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching IPO list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IPO BY ID ====================

@router.get("/detail/{ipo_id}", tags=["IPO Data"])
async def get_ipo_detail(ipo_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific IPO by its ID.
    
    Args:
        ipo_id: The unique IPO identifier (e.g., 'mainboard-ipo-sebi-filing-2025')
    
    Returns comprehensive IPO data including:
    - Company details and about text
    - GMP (Grey Market Premium) data
    - Subscription status
    - Listing performance
    - Timeline (open/close dates, allotment, refund dates)
    - Financial information
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={"ipoId": ipo_id},
            limit=1
        )
        
        if not data:
            return create_error_response(message=f"IPO with ID '{ipo_id}' not found")
        
        return create_success_response_n({
            "endpoint": f"ipo/detail/{ipo_id}",
            "data": convert_object_ids(data[0])
        })
        
    except Exception as e:
        logger.error(f"Error fetching IPO detail for {ipo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== OPEN IPOs ====================

@router.get("/open", tags=["IPO Data"])
async def get_open_ipos(
    limit: Optional[int] = Query(50, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get currently open IPOs accepting applications.
    
    Returns IPOs where subscription is currently active.
    """
    try:
        db = get_db()
        
        # Match various "Open" status patterns
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={
                "$or": [
                    {"apiIpoStatusFormatted": {"$regex": "Open", "$options": "i"}},
                    {"apiIpoStatus": {"$regex": "Open", "$options": "i"}}
                ]
            },
            limit=limit,
            sort_by="apiIssueOpenDate",
            sort_order=-1
        )
        
        if not data:
            return create_success_response_n({
                "endpoint": "ipo/open",
                "total_records": 0,
                "message": "No IPOs are currently open for subscription",
                "data": []
            })
        
        return create_success_response_n({
            "endpoint": "ipo/open",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching open IPOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UPCOMING IPOs ====================

@router.get("/upcoming", tags=["IPO Data"])
async def get_upcoming_ipos(
    limit: Optional[int] = Query(50, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get upcoming IPOs scheduled to open soon.
    
    Returns IPOs with future opening dates or "Upcoming" status.
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={
                "$or": [
                    {"apiIpoStatusFormatted": {"$regex": "Upcoming|Soon|Awaited", "$options": "i"}},
                    {"apiIpoStatus": {"$regex": "Upcoming|Soon|Awaited", "$options": "i"}}
                ]
            },
            limit=limit,
            sort_by="apiIssueOpenDate",
            sort_order=1
        )
        
        if not data:
            return create_success_response_n({
                "endpoint": "ipo/upcoming",
                "total_records": 0,
                "message": "No upcoming IPOs found",
                "data": []
            })
        
        return create_success_response_n({
            "endpoint": "ipo/upcoming",
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching upcoming IPOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LISTED IPOs ====================

@router.get("/listed", tags=["IPO Data"])
async def get_listed_ipos(
    year: Optional[int] = Query(None, description="Filter by listing year"),
    limit: Optional[int] = Query(100, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get IPOs that have been listed on the exchange.
    
    Returns listed IPOs with listing price, listing gains, and current performance.
    """
    try:
        db = get_db()
        query = {
            "$or": [
                {"apiIpoStatusFormatted": {"$regex": "Listed", "$options": "i"}},
                {"apiListedPrice": {"$ne": None, "$gt": 0}}
            ]
        }
        
        if year:
            query["apiIpoYear"] = str(year)
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query=query,
            limit=limit,
            sort_by="listingDate",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No listed IPO data available")
        
        return create_success_response_n({
            "endpoint": "ipo/listed",
            "total_records": len(data),
            "year_filter": year,
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching listed IPOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IPO GMP DATA ====================

@router.get("/gmp", tags=["IPO Data"])
async def get_ipo_gmp_data(
    limit: Optional[int] = Query(50, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get Grey Market Premium (GMP) data for active IPOs.
    
    Returns current GMP values, estimated listing prices, and GMP trends.
    GMP indicates expected listing premium based on grey market trading.
    """
    try:
        db = get_db()
        
        # Get IPOs with GMP data
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={
                "$or": [
                    {"apiGmpValue": {"$ne": None}},
                    {"currentGmp": {"$ne": None}}
                ]
            },
            limit=limit,
            sort_by="lastUpdatedDb",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No GMP data available")
        
        # Extract GMP-specific fields
        gmp_data = []
        for ipo in data:
            gmp_data.append({
                "ipoId": ipo.get("ipoId"),
                "companyName": ipo.get("apiCompanyName") or ipo.get("scrapedCompanyName"),
                "status": ipo.get("apiIpoStatusFormatted"),
                "issuePrice": ipo.get("apiPrice"),
                "currentGmp": ipo.get("apiGmpValue") or ipo.get("currentGmp"),
                "gmpPercent": ipo.get("apiGmpPercent") or ipo.get("gmpPercentCalc"),
                "estimatedListingPrice": ipo.get("apiEstimatedListingPrice") or ipo.get("estimatedListingPrice"),
                "estimatedListingPercent": ipo.get("apiEstimatedListingPercent"),
                "fireRating": ipo.get("apiFireRating"),
                "gmpTrend": ipo.get("gmpTrendHistoryTable"),
                "lastUpdated": ipo.get("lastUpdatedDb")
            })
        
        return create_success_response_n({
            "endpoint": "ipo/gmp",
            "total_records": len(gmp_data),
            "data": convert_object_ids(gmp_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching IPO GMP data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IPO SUBSCRIPTION STATUS ====================

@router.get("/subscription", tags=["IPO Data"])
async def get_ipo_subscription_data(
    limit: Optional[int] = Query(50, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get subscription status data for open/recently closed IPOs.
    
    Returns subscription times across categories (Retail, HNI, QIB).
    """
    try:
        db = get_db()
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={
                "apiSubscription": {"$ne": None, "$ne": ""}
            },
            limit=limit,
            sort_by="lastUpdatedDb",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message="No subscription data available")
        
        # Extract subscription-specific fields
        subscription_data = []
        for ipo in data:
            subscription_data.append({
                "ipoId": ipo.get("ipoId"),
                "companyName": ipo.get("apiCompanyName") or ipo.get("scrapedCompanyName"),
                "status": ipo.get("apiIpoStatusFormatted"),
                "overallSubscription": ipo.get("apiSubscription"),
                "daywiseSubscription": ipo.get("ipoDaywiseSubscriptionTable"),
                "sharesBidAmount": ipo.get("ipoSharesBidAmountTable"),
                "openDate": ipo.get("apiIssueOpenDate"),
                "closeDate": ipo.get("apiIssueCloseDate"),
                "lastUpdated": ipo.get("lastUpdatedDb")
            })
        
        return create_success_response_n({
            "endpoint": "ipo/subscription",
            "total_records": len(subscription_data),
            "data": convert_object_ids(subscription_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching IPO subscription data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IPO BY YEAR ====================

@router.get("/year/{year}", tags=["IPO Data"])
async def get_ipos_by_year(
    year: int,
    category: Optional[str] = Query(None, description="Filter by 'Mainboard' or 'SME'"),
    limit: Optional[int] = Query(200, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Get all IPOs for a specific year.
    
    Args:
        year: The year to filter by (e.g., 2024, 2025)
    
    Returns IPOs from the specified year with performance statistics.
    """
    try:
        db = get_db()
        query = {"apiIpoYear": str(year)}
        
        if category:
            query["apiIpoCategory"] = {"$regex": category, "$options": "i"}
        
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query=query,
            limit=limit,
            sort_by="apiIssueOpenDate",
            sort_order=-1
        )
        
        if not data:
            return create_error_response(message=f"No IPO data available for year {year}")
        
        # Calculate year statistics
        total_ipos = len(data)
        listed_count = sum(1 for ipo in data if ipo.get("apiListedPrice"))
        positive_listings = sum(1 for ipo in data if (ipo.get("apiListingGain") or 0) > 0)
        
        return create_success_response_n({
            "endpoint": f"ipo/year/{year}",
            "year": year,
            "statistics": {
                "total_ipos": total_ipos,
                "listed": listed_count,
                "positive_listings": positive_listings,
                "success_rate": f"{(positive_listings/listed_count*100):.1f}%" if listed_count > 0 else "N/A"
            },
            "category_filter": category,
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching IPOs for year {year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEARCH IPO ====================

@router.get("/search", tags=["IPO Data"])
async def search_ipos(
    q: str = Query(..., description="Search query (company name, symbol, or ID)"),
    limit: Optional[int] = Query(20, description="Limit number of results")
) -> Dict[str, Any]:
    """
    Search IPOs by company name, symbol, or ID.
    
    Args:
        q: Search query string
    
    Returns matching IPOs across all fields.
    """
    try:
        db = get_db()
        
        # Search across multiple fields
        data = db.get_collection_data(
            collection_name="investorgain_ipo_data_v1",
            query={
                "$or": [
                    {"apiCompanyName": {"$regex": q, "$options": "i"}},
                    {"scrapedCompanyName": {"$regex": q, "$options": "i"}},
                    {"companyFullNameScraped": {"$regex": q, "$options": "i"}},
                    {"ipoId": {"$regex": q, "$options": "i"}},
                    {"ipoSymbol": {"$regex": q, "$options": "i"}}
                ]
            },
            limit=limit,
            sort_by="lastUpdatedDb",
            sort_order=-1
        )
        
        if not data:
            return create_success_response_n({
                "endpoint": "ipo/search",
                "query": q,
                "total_records": 0,
                "message": f"No IPOs found matching '{q}'",
                "data": []
            })
        
        return create_success_response_n({
            "endpoint": "ipo/search",
            "query": q,
            "total_records": len(data),
            "data": convert_object_ids(data)
        })
        
    except Exception as e:
        logger.error(f"Error searching IPOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MANUAL REFRESH ENDPOINTS ====================

from API.Controller.scrap_investorgain_ipo_data import NSEInvestorGainIPOController
from Utils.ipo_zerodha_and_investorgain_matcher import UltimateIPOMatcher


@router.post("/refresh/investorgain", tags=["IPO Manual Refresh"])
async def refresh_investorgain_ipo_data() -> Dict[str, Any]:
    """
    Manually trigger scraping of IPO data from InvestorGain.
    
    This scrapes comprehensive IPO data including:
    - GMP (Grey Market Premium)
    - Subscription status
    - Company details
    - Listing performance
    
    ⚠️ Note: This may take a few minutes to complete.
    """
    try:
        controller = NSEInvestorGainIPOController()
        result = controller.scrape_investorgain_ipo_data()
        return create_success_response_n({
            "endpoint": "ipo/refresh/investorgain",
            "message": "InvestorGain IPO data refreshed successfully",
            "result": convert_object_ids(result) if result else None
        })
    except Exception as e:
        logger.error(f"Error refreshing InvestorGain IPO data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/match-zerodha", tags=["IPO Manual Refresh"])
async def refresh_zerodha_investorgain_matching() -> Dict[str, Any]:
    """
    Manually trigger Zerodha-InvestorGain IPO data matching.
    
    This matches IPO data with Zerodha's IPO information for:
    - Enhanced company details
    - Symbol mapping
    - Additional metadata
    
    ⚠️ Note: This may take a few minutes to complete.
    """
    try:
        matcher = UltimateIPOMatcher()
        result = matcher.run_ultimate_matching()
        return create_success_response_n({
            "endpoint": "ipo/refresh/match-zerodha",
            "message": "Zerodha-InvestorGain matching completed successfully",
            "result": convert_object_ids(result) if result else {"status": "completed"}
        })
    except Exception as e:
        logger.error(f"Error in Zerodha-InvestorGain matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/all", tags=["IPO Manual Refresh"])
async def refresh_all_ipo_data() -> Dict[str, Any]:
    """
    Manually trigger refresh of ALL IPO data sources.
    
    This runs:
    1. InvestorGain IPO scraping
    2. Zerodha-InvestorGain matching
    
    ⚠️ Warning: This may take several minutes to complete.
    """
    results = {}
    errors = []
    
    # Step 1: Scrape InvestorGain data
    try:
        logger.info("Refreshing InvestorGain IPO data...")
        controller = NSEInvestorGainIPOController()
        result = controller.scrape_investorgain_ipo_data()
        results["investorgain"] = {"status": "success", "records": len(result) if isinstance(result, list) else (1 if result else 0)}
        logger.info("InvestorGain IPO data refreshed successfully")
    except Exception as e:
        results["investorgain"] = {"status": "error", "error": str(e)}
        errors.append("investorgain")
        logger.error(f"Error refreshing InvestorGain data: {e}")
    
    # Step 2: Run Zerodha matching
    try:
        logger.info("Running Zerodha-InvestorGain matching...")
        matcher = UltimateIPOMatcher()
        result = matcher.run_ultimate_matching()
        results["zerodha-matching"] = {"status": "success", "message": "Matching completed"}
        logger.info("Zerodha-InvestorGain matching completed")
    except Exception as e:
        results["zerodha-matching"] = {"status": "error", "error": str(e)}
        errors.append("zerodha-matching")
        logger.error(f"Error in Zerodha matching: {e}")
    
    return create_success_response_n({
        "endpoint": "ipo/refresh/all",
        "message": f"IPO refresh completed. {2 - len(errors)}/2 succeeded.",
        "results": results,
        "errors": errors
    })
