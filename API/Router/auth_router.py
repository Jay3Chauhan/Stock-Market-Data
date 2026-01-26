"""
Authentication Router
=====================
API endpoints for user authentication and management.

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login existing user
- POST /auth/verify-token - Verify Firebase token
- GET /auth/me - Get current user profile
- PUT /auth/fcm-token - Update FCM token
- POST /auth/send-notification - Send push notification (testing)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from API.Controller.user_controller import UserController
from Services.push_notification import PushNotificationService
from Utils.auth_middleware import get_current_user
from Utils.response import create_response
from Utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== Request Models ====================

class RegisterRequest(BaseModel):
    """Request model for user registration"""
    firebase_token: str = Field(..., description="Firebase ID token from client")
    fcm_token: Optional[str] = Field(None, description="FCM device token for push notifications")
    display_name: Optional[str] = Field(None, description="User's display name (optional)")
    photo_url: Optional[str] = Field(None, description="User's profile photo URL (optional)")
    phone_number: Optional[str] = Field(None, description="User's phone number (optional, for display only)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",
                "fcm_token": "fcm_device_token_here",
                "display_name": "John Doe",
                "photo_url": "https://example.com/photo.jpg",
                "phone_number": "+919876543210"
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login"""
    firebase_token: str = Field(..., description="Firebase ID token from client")
    fcm_token: Optional[str] = Field(None, description="FCM device token for push notifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",
                "fcm_token": "fcm_device_token_here"
            }
        }


class VerifyTokenRequest(BaseModel):
    """Request model for token verification"""
    firebase_token: str = Field(..., description="Firebase ID token to verify")
    
    class Config:
        json_schema_extra = {
            "example": {
                "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."
            }
        }


class UpdateFCMTokenRequest(BaseModel):
    """Request model for updating FCM token"""
    fcm_token: str = Field(..., description="New FCM device token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fcm_token": "new_fcm_device_token_here"
            }
        }


class SendNotificationRequest(BaseModel):
    """Request model for sending push notification"""
    user_uid: str = Field(..., description="Target user's Firebase UID")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[dict] = Field(None, description="Additional data payload")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_uid": "firebase_user_uid",
                "title": "Market Alert",
                "body": "NIFTY crossed 22,000!",
                "data": {
                    "type": "market_alert",
                    "symbol": "NIFTY",
                    "price": "22050"
                }
            }
        }


class BroadcastNotificationRequest(BaseModel):
    """Request model for broadcasting notification to all users"""
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[dict] = Field(None, description="Additional data payload")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Market Update",
                "body": "NIFTY 50 reached new all-time high!",
                "data": {
                    "type": "market_update",
                    "symbol": "NIFTY",
                    "price": "22500"
                }
            }
        }


# ==================== Endpoints ====================

@router.post("/register", tags=["Authentication"])
async def register(request: RegisterRequest):
    """
    Register a new user with Firebase authentication.
    
    **Workflow:**
    1. Client authenticates with Firebase (email/password or Google)
    2. Client sends Firebase ID token to this endpoint
    3. Backend verifies token and creates user in MongoDB
    4. FCM token is stored for push notifications
    
    **Returns:**
    - User profile data
    - `is_new_user` flag (true for new registrations)
    """
    try:
        controller = UserController()
        result = await controller.register_user(
            firebase_token=request.firebase_token,
            fcm_token=request.fcm_token,
            display_name=request.display_name,
            photo_url=request.photo_url,
            phone_number=request.phone_number
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Registration failed')
            )
        
        return create_response(
            success=True,
            data=result['data'],
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.post("/login", tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Login existing user with Firebase authentication.
    
    **Workflow:**
    1. Client authenticates with Firebase
    2. Client sends Firebase ID token to this endpoint
    3. Backend verifies token and returns user data
    4. Updates FCM token and last login timestamp
    
    **Note:** If user doesn't exist in MongoDB, automatically registers them.
    """
    try:
        controller = UserController()
        result = await controller.login_user(
            firebase_token=request.firebase_token,
            fcm_token=request.fcm_token
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Login failed')
            )
        
        return create_response(
            success=True,
            data=result['data'],
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post("/verify-token", tags=["Authentication"])
async def verify_token(request: VerifyTokenRequest):
    """
    Verify Firebase ID token without database operations.
    
    **Use Cases:**
    - Token validation before making authenticated requests
    - Checking token expiry
    - Debugging authentication issues
    """
    try:
        controller = UserController()
        result = await controller.verify_token_only(request.firebase_token)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Token verification failed')
            )
        
        return create_response(
            success=True,
            data=result['data'],
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify token endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )


@router.get("/me", tags=["Authentication"])
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    **Authentication Required:**
    - Add header: `Authorization: Bearer <firebase_token>`
    
    **Returns:**
    - User profile data from MongoDB
    - Includes: uid, phone, email, display_name, created_at, last_login
    """
    try:
        # Remove sensitive fields
        safe_user = {
            "uid": current_user.get('uid'),
            "phone_number": current_user.get('phone_number'),
            "email": current_user.get('email'),
            "display_name": current_user.get('display_name'),
            "photo_url": current_user.get('photo_url'),
            "is_active": current_user.get('is_active'),
            "created_at": current_user.get('created_at'),
            "last_login": current_user.get('last_login')
        }
        
        return create_response(
            success=True,
            data=safe_user,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get profile endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/fcm-token", tags=["Authentication"])
async def update_fcm_token(
    request: UpdateFCMTokenRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update FCM token for push notifications.
    
    **Authentication Required:**
    - Add header: `Authorization: Bearer <firebase_token>`
    
    **Use Cases:**
    - App installed on new device
    - FCM token refreshed by Firebase
    - User logged in on different device
    """
    try:
        controller = UserController()
        result = await controller.update_fcm_token(
            uid=current_user['uid'],
            fcm_token=request.fcm_token
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Failed to update FCM token')
            )
        
        return create_response(
            success=True,
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update FCM token endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update FCM token"
        )


@router.post("/send-notification", tags=["Notifications"])
async def send_push_notification_test(
    request: SendNotificationRequest
):
    """
    Send push notification to a user (Testing/Development Only - No Auth Required).
    
    **⚠️ WARNING: This endpoint has NO AUTHENTICATION for testing purposes!**
    **Do not use in production without proper access control.**
    
    **Use Cases:**
    - Testing push notifications during development
    - Quick debugging of FCM integration
    - Testing notification delivery without auth setup
    
    **How to Use:**
    1. Register a user and note their `uid`
    2. Call this endpoint with the `user_uid`
    3. Check if notification arrives on device
    
    **Example Request:**
    ```json
    {
      "user_uid": "szYcaytSN7hTDvDsDjIQ2ZXLr2S2",
      "title": "Market Alert",
      "body": "NIFTY crossed 22,000!",
      "data": {
        "type": "market_alert",
        "symbol": "NIFTY",
        "price": "22050"
      }
    }
    ```
    
    **Production Alternative:** Use `/send-notification-auth` with Firebase token.
    """
    try:
        notification_service = PushNotificationService()
        
        result = await notification_service.send_to_user(
            user_uid=request.user_uid,
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to send notification')
            )
        
        return create_response(
            success=True,
            data={"message_id": result.get('message_id')},
            message="Notification sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send notification endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )


@router.post("/send-notification-auth", tags=["Notifications"])
async def send_push_notification_authenticated(
    request: SendNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send push notification to a user (Production - Authentication Required).
    
    **Authentication Required:**
    - Add header: `Authorization: Bearer <firebase_token>`
    
    **Use Cases:**
    - Admin sending manual alerts to users
    - Authenticated users sending notifications
    - Production notification system
    
    **Security:**
    - Only authenticated users can send notifications
    - Consider adding admin-only check for production
    
    **Example Request:**
    ```bash
    curl -X POST https://api.jaychauhan.tech/auth/send-notification-auth \
      -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "user_uid": "target_user_uid",
        "title": "Alert",
        "body": "Message body"
      }'
    ```
    """
    try:
        notification_service = PushNotificationService()
        
        result = await notification_service.send_to_user(
            user_uid=request.user_uid,
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to send notification')
            )
        
        return create_response(
            success=True,
            data={
                "message_id": result.get('message_id'),
                "sent_by": current_user.get('uid')
            },
            message="Notification sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send notification endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )


@router.post("/broadcast-notification", tags=["Notifications"])
async def broadcast_notification_test(
    request: BroadcastNotificationRequest
):
    """
    Broadcast notification to ALL users (Testing/Development - No Auth).
    
    **⚠️ WARNING: Sends to ALL USERS! No authentication required for testing.**
    
    **Use Cases:**
    - Testing broadcast functionality
    - App-wide announcements during testing
    - Market updates to all users
    
    **Example:**
    ```json
    {
      "title": "Market Update",
      "body": "NIFTY 50 reached 22,500!",
      "data": {
        "type": "market_update",
        "symbol": "NIFTY",
        "price": "22500"
      }
    }
    ```
    
    **Response includes:**
    - Total users in database
    - Users with FCM tokens
    - Successfully sent count
    - Failed count
    """
    try:
        notification_service = PushNotificationService()
        
        result = await notification_service.send_to_all_users(
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to send broadcast')
            )
        
        return create_response(
            success=True,
            data=result,
            message=f"Broadcast sent to {result.get('sent', 0)} users"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Broadcast notification endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send broadcast notification"
        )


@router.post("/broadcast-notification-auth", tags=["Notifications"])
async def broadcast_notification_authenticated(
    request: BroadcastNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Broadcast notification to ALL users (Production - Authentication Required).
    
    **Authentication Required:**
    - Add header: `Authorization: Bearer <firebase_token>`
    
    **⚠️ WARNING: Sends to ALL USERS!**
    
    **Use Cases:**
    - Admin sending app-wide announcements
    - Critical market updates
    - System notifications
    
    **Security:**
    - Requires authentication
    - Consider adding admin-only check
    - Track who sent the broadcast
    
    **Example:**
    ```bash
    curl -X POST https://api.jaychauhan.tech/auth/broadcast-notification-auth \
      -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Market Update",
        "body": "Important announcement",
        "data": {"type": "announcement"}
      }'
    ```
    """
    try:
        notification_service = PushNotificationService()
        
        result = await notification_service.send_to_all_users(
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to send broadcast')
            )
        
        # Log who sent the broadcast
        logger.info(f"Broadcast sent by {current_user.get('uid')}: {result.get('sent')} users")
        
        return create_response(
            success=True,
            data={
                **result,
                "sent_by": current_user.get('uid'),
                "sent_by_email": current_user.get('email')
            },
            message=f"Broadcast sent to {result.get('sent', 0)} users"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Broadcast notification endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send broadcast notification"
        )


@router.get("/health", tags=["Authentication"])
async def auth_health_check():
    """
    Check authentication service health.
    
    Returns Firebase and MongoDB connection status.
    """
    try:
        from Utils.firebase_config import is_firebase_enabled
        
        firebase_status = is_firebase_enabled()
        
        return create_response(
            success=True,
            data={
                "firebase_enabled": firebase_status,
                "service": "authentication"
            },
            message="Authentication service is running"
        )
        
    except Exception as e:
        logger.error(f"Auth health check error: {str(e)}")
        return create_response(
            success=False,
            message=f"Authentication service health check failed: {str(e)}"
        )
