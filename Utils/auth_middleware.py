"""
Authentication Middleware
=========================
FastAPI dependency for protecting routes with Firebase authentication.

This module provides:
- Token extraction from Authorization header
- Token verification via Firebase
- Current user injection into route handlers
- Optional authentication support

Usage:
    from Utils.auth_middleware import get_current_user
    
    @router.get("/protected")
    async def protected_route(current_user: dict = Depends(get_current_user)):
        # current_user contains verified user info
        ...
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Services.firebase_auth import FirebaseAuthService
from Utils.user_db import UserDatabase
from Utils.logger import get_logger

logger = get_logger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(
    scheme_name="Firebase Bearer Token",
    description="Enter your Firebase ID token",
    auto_error=False
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get current authenticated user.
    
    Extracts and verifies Firebase token from Authorization header.
    Raises HTTPException if token is invalid or missing.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        dict: Current user information from MongoDB
            {
                'uid': 'firebase_uid',
                'phone_number': '+1234567890',
                'email': 'user@example.com',
                ...
            }
    
    Raises:
        HTTPException: If authentication fails
    """
    # Check if credentials provided
    if not credentials:
        logger.warning("No authorization credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide Firebase ID token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token
        token = credentials.credentials
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token with Firebase
        firebase_auth = FirebaseAuthService()
        firebase_user = await firebase_auth.verify_token(token)
        
        if not firebase_user:
            logger.warning("Firebase token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Firebase token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_db = UserDatabase()
        user = await user_db.get_user_by_uid(firebase_user['uid'])
        
        if not user:
            logger.warning(f"User not found in database: {firebase_user['uid']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please register first."
            )
        
        # Check if user is active
        if not user.get('is_active', True):
            logger.warning(f"Inactive user attempted access: {firebase_user['uid']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        logger.info(f"User authenticated successfully: {firebase_user['uid']}")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    FastAPI dependency for optional authentication.
    
    Use this for endpoints that should work with or without authentication.
    Returns user info if authenticated, None if not.
    
    Args:
        credentials: HTTP Bearer token from Authorization header (optional)
        
    Returns:
        dict: Current user information if authenticated
        None: If no credentials provided or authentication failed
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        if not token:
            return None
        
        # Verify token
        firebase_auth = FirebaseAuthService()
        firebase_user = await firebase_auth.verify_token(token)
        
        if not firebase_user:
            return None
        
        # Get user from database
        user_db = UserDatabase()
        user = await user_db.get_user_by_uid(firebase_user['uid'])
        
        if not user or not user.get('is_active', True):
            return None
        
        return user
        
    except Exception as e:
        logger.debug(f"Optional auth failed (this is OK): {str(e)}")
        return None


async def verify_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    FastAPI dependency for admin-only routes.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Current admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    # TODO: Implement role-based access control
    # For now, you can add an 'is_admin' field in user document
    
    if not current_user.get('metadata', {}).get('is_admin', False):
        logger.warning(f"Non-admin user attempted admin access: {current_user['uid']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def require_permissions(*permissions: str):
    """
    Decorator factory for permission-based access control.
    
    Usage:
        @router.get("/admin/users")
        @require_permissions("users.read", "users.write")
        async def admin_users(current_user: dict = Depends(get_current_user)):
            ...
    
    Args:
        *permissions: Required permission strings
        
    Returns:
        Dependency function
    """
    async def check_permissions(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_permissions = current_user.get('metadata', {}).get('permissions', [])
        
        for permission in permissions:
            if permission not in user_permissions:
                logger.warning(
                    f"User {current_user['uid']} missing permission: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return current_user
    
    return check_permissions
