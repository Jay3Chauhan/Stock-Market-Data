"""
Firebase Authentication Service
================================
Handles Firebase token verification and user authentication.

This service provides:
- Firebase ID token verification
- User information extraction from tokens
- Token decoding and validation

Usage:
    from Services.firebase_auth import FirebaseAuthService
    
    auth_service = FirebaseAuthService()
    user_info = await auth_service.verify_token(token)
"""

from typing import Dict, Optional, Any
from firebase_admin import auth
from Utils.logger import get_logger
from Utils.firebase_config import get_firebase_app, is_firebase_enabled

logger = get_logger(__name__)


class FirebaseAuthService:
    """Service for Firebase authentication operations"""
    
    def __init__(self):
        """Initialize Firebase Auth Service"""
        self.firebase_app = get_firebase_app()
        self.enabled = is_firebase_enabled()
        
        if not self.enabled:
            logger.warning("Firebase is not enabled - authentication features will be limited")
    
    async def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token and return user information.
        
        Args:
            id_token: Firebase ID token to verify
            
        Returns:
            dict: User information from token if valid
                {
                    'uid': 'user_unique_id',
                    'email': 'user@example.com',
                    'phone_number': '+1234567890',
                    'email_verified': True/False,
                    'name': 'User Name',
                    'picture': 'https://...',
                    ...
                }
            None: If token is invalid or verification failed
        """
        if not self.enabled:
            logger.error("Firebase is not enabled - cannot verify token")
            return None
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'phone_number': decoded_token.get('phone_number'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'firebase_claims': decoded_token
            }
            
            logger.info(f"Token verified successfully for user: {user_info['uid']}")
            return user_info
            
        except auth.ExpiredIdTokenError:
            logger.warning("Firebase token has expired")
            return None
            
        except auth.RevokedIdTokenError:
            logger.warning("Firebase token has been revoked")
            return None
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase token")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying Firebase token: {str(e)}")
            return None
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Firebase by UID.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            dict: User information if found
            None: If user not found or error occurred
        """
        if not self.enabled:
            logger.error("Firebase is not enabled")
            return None
        
        try:
            user_record = auth.get_user(uid)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'phone_number': user_record.phone_number,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'metadata': {
                    'creation_timestamp': user_record.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp
                }
            }
            
            return user_info
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found with UID: {uid}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by UID: {str(e)}")
            return None
    
    async def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Firebase by phone number.
        
        Args:
            phone_number: Phone number in E.164 format (e.g., +919876543210)
            
        Returns:
            dict: User information if found
            None: If user not found or error occurred
        """
        if not self.enabled:
            logger.error("Firebase is not enabled")
            return None
        
        try:
            user_record = auth.get_user_by_phone_number(phone_number)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'phone_number': user_record.phone_number,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled
            }
            
            return user_info
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found with phone: {phone_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by phone: {str(e)}")
            return None
    
    async def decode_token_without_verify(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Decode Firebase token without verification (for debugging only).
        
        Args:
            id_token: Firebase ID token to decode
            
        Returns:
            dict: Decoded token claims
            None: If decoding failed
        """
        try:
            # This bypasses verification - use only for debugging
            decoded_token = auth.verify_id_token(id_token, check_revoked=False)
            return decoded_token
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}")
            return None
    
    async def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> Optional[str]:
        """
        Create a custom Firebase token for testing.
        
        Args:
            uid: User UID
            additional_claims: Additional claims to add to token
            
        Returns:
            str: Custom token
            None: If creation failed
        """
        if not self.enabled:
            logger.error("Firebase is not enabled")
            return None
        
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating custom token: {str(e)}")
            return None
