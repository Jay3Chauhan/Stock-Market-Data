"""
User Controller
===============
Business logic for user management operations.

Handles:
- User registration with Firebase
- User login
- FCM token management
- User profile operations
"""

from typing import Dict, Optional, Any
from Services.firebase_auth import FirebaseAuthService
from Utils.user_db import UserDatabase
from Utils.logger import get_logger

logger = get_logger(__name__)


class UserController:
    """Controller for user management operations"""
    
    def __init__(self):
        """Initialize User Controller"""
        self.firebase_auth = FirebaseAuthService()
        self.user_db = UserDatabase()
    
    async def register_user(
        self,
        firebase_token: str,
        phone_number: Optional[str] = None,
        fcm_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user.
        
        Workflow:
        1. Verify Firebase token
        2. Check if user already exists in MongoDB
        3. Create user in MongoDB if new
        4. Update FCM token if provided
        
        Args:
            firebase_token: Firebase ID token
            phone_number: Phone number (optional, can be from token)
            fcm_token: FCM device token for push notifications
            
        Returns:
            dict: Registration result with user info
        """
        try:
            # Verify Firebase token
            firebase_user = await self.firebase_auth.verify_token(firebase_token)
            
            if not firebase_user:
                logger.error("Invalid Firebase token during registration")
                return {
                    "success": False,
                    "message": "Invalid Firebase token",
                    "error": "TOKEN_INVALID"
                }
            
            uid = firebase_user['uid']
            
            # Check if user already exists
            existing_user = await self.user_db.get_user_by_uid(uid)
            
            if existing_user:
                # User exists, update FCM token if provided
                if fcm_token:
                    await self.user_db.update_fcm_token(uid, fcm_token)
                
                await self.user_db.update_last_login(uid)
                
                logger.info(f"User already registered: {uid}")
                return {
                    "success": True,
                    "message": "User already registered",
                    "data": {
                        "user": self._format_user_response(existing_user),
                        "is_new_user": False
                    }
                }
            
            # Create new user
            # Use phone from parameter or fallback to Firebase token
            user_phone = phone_number or firebase_user.get('phone_number')
            
            new_user = await self.user_db.create_user(
                uid=uid,
                phone_number=user_phone,
                email=firebase_user.get('email'),
                display_name=firebase_user.get('name'),
                photo_url=firebase_user.get('picture'),
                fcm_token=fcm_token
            )
            
            if not new_user:
                logger.error(f"Failed to create user in database: {uid}")
                return {
                    "success": False,
                    "message": "Failed to create user",
                    "error": "DATABASE_ERROR"
                }
            
            logger.info(f"New user registered successfully: {uid}")
            return {
                "success": True,
                "message": "User registered successfully",
                "data": {
                    "user": self._format_user_response(new_user),
                    "is_new_user": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            return {
                "success": False,
                "message": "Registration failed",
                "error": str(e)
            }
    
    async def login_user(
        self,
        firebase_token: str,
        fcm_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Login existing user.
        
        Workflow:
        1. Verify Firebase token
        2. Get user from MongoDB
        3. Update FCM token and last login
        
        Args:
            firebase_token: Firebase ID token
            fcm_token: FCM device token (optional)
            
        Returns:
            dict: Login result with user info
        """
        try:
            # Verify Firebase token
            firebase_user = await self.firebase_auth.verify_token(firebase_token)
            
            if not firebase_user:
                logger.error("Invalid Firebase token during login")
                return {
                    "success": False,
                    "message": "Invalid Firebase token",
                    "error": "TOKEN_INVALID"
                }
            
            uid = firebase_user['uid']
            
            # Get user from database
            user = await self.user_db.get_user_by_uid(uid)
            
            if not user:
                # User not in MongoDB, register them
                logger.info(f"User not found in database, registering: {uid}")
                return await self.register_user(firebase_token, fcm_token=fcm_token)
            
            # Update FCM token if provided
            if fcm_token:
                await self.user_db.update_fcm_token(uid, fcm_token)
            
            # Update last login
            await self.user_db.update_last_login(uid)
            
            # Refresh user data
            user = await self.user_db.get_user_by_uid(uid)
            
            logger.info(f"User logged in successfully: {uid}")
            return {
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": self._format_user_response(user)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during user login: {str(e)}")
            return {
                "success": False,
                "message": "Login failed",
                "error": str(e)
            }
    
    async def get_user_profile(self, uid: str) -> Dict[str, Any]:
        """
        Get user profile by UID.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            dict: User profile data
        """
        try:
            user = await self.user_db.get_user_by_uid(uid)
            
            if not user:
                return {
                    "success": False,
                    "message": "User not found",
                    "error": "USER_NOT_FOUND"
                }
            
            return {
                "success": True,
                "message": "User profile retrieved",
                "data": self._format_user_response(user)
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get user profile",
                "error": str(e)
            }
    
    async def update_fcm_token(
        self,
        uid: str,
        fcm_token: str
    ) -> Dict[str, Any]:
        """
        Update user's FCM token.
        
        Args:
            uid: Firebase user UID
            fcm_token: New FCM device token
            
        Returns:
            dict: Update result
        """
        try:
            success = await self.user_db.update_fcm_token(uid, fcm_token)
            
            if success:
                logger.info(f"FCM token updated for user: {uid}")
                return {
                    "success": True,
                    "message": "FCM token updated successfully"
                }
            
            return {
                "success": False,
                "message": "Failed to update FCM token",
                "error": "UPDATE_FAILED"
            }
            
        except Exception as e:
            logger.error(f"Error updating FCM token: {str(e)}")
            return {
                "success": False,
                "message": "Failed to update FCM token",
                "error": str(e)
            }
    
    async def verify_token_only(self, firebase_token: str) -> Dict[str, Any]:
        """
        Verify Firebase token without database operations.
        
        Args:
            firebase_token: Firebase ID token
            
        Returns:
            dict: Token verification result
        """
        try:
            firebase_user = await self.firebase_auth.verify_token(firebase_token)
            
            if not firebase_user:
                return {
                    "success": False,
                    "message": "Invalid Firebase token",
                    "error": "TOKEN_INVALID"
                }
            
            return {
                "success": True,
                "message": "Token is valid",
                "data": {
                    "uid": firebase_user['uid'],
                    "email": firebase_user.get('email'),
                    "phone_number": firebase_user.get('phone_number'),
                    "email_verified": firebase_user.get('email_verified', False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return {
                "success": False,
                "message": "Token verification failed",
                "error": str(e)
            }
    
    def _format_user_response(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format user data for API response (remove sensitive fields).
        
        Args:
            user: User document from database
            
        Returns:
            dict: Formatted user data
        """
        # Remove sensitive fields
        safe_user = {
            "uid": user.get('uid'),
            "phone_number": user.get('phone_number'),
            "email": user.get('email'),
            "display_name": user.get('display_name'),
            "photo_url": user.get('photo_url'),
            "is_active": user.get('is_active'),
            "created_at": user.get('created_at'),
            "last_login": user.get('last_login')
        }
        
        # Remove None values
        return {k: v for k, v in safe_user.items() if v is not None}
