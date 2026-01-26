"""
Push Notification Service
==========================
Handles Firebase Cloud Messaging (FCM) push notifications.

This service provides:
- Send notifications to individual users
- Send notifications to multiple users
- Send data-only messages
- Send notification + data messages

Usage:
    from Services.push_notification import PushNotificationService
    
    service = PushNotificationService()
    await service.send_to_user(
        user_uid="user123",
        title="Market Alert",
        body="NIFTY crossed 22,000!"
    )
"""

from typing import Dict, List, Optional, Any
from firebase_admin import messaging
from Utils.logger import get_logger
from Utils.firebase_config import get_firebase_app, is_firebase_enabled
from Utils.user_db import UserDatabase
from Utils.config_reader import configure

logger = get_logger(__name__)


class PushNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    def __init__(self):
        """Initialize Push Notification Service"""
        self.firebase_app = get_firebase_app()
        self.enabled = is_firebase_enabled()
        self.fcm_enabled = configure.getboolean('FIREBASE', 'FCM_ENABLED', fallback=True)
        self.user_db = UserDatabase()
        
        if not self.enabled or not self.fcm_enabled:
            logger.warning("Push notifications are disabled")
    
    async def send_to_user(
        self,
        user_uid: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a specific user by UID.
        
        Args:
            user_uid: Firebase user UID
            title: Notification title
            body: Notification body
            data: Optional data payload
            image_url: Optional image URL for rich notification
            
        Returns:
            dict: Result with success status and message ID or error
        """
        if not self.enabled or not self.fcm_enabled:
            logger.error("Push notifications are disabled")
            return {"success": False, "error": "Push notifications disabled"}
        
        try:
            # Get user's FCM token from database
            user = await self.user_db.get_user_by_uid(user_uid)
            
            if not user:
                logger.error(f"User not found: {user_uid}")
                return {"success": False, "error": "User not found"}
            
            fcm_token = user.get('fcm_token')
            
            if not fcm_token:
                logger.error(f"User {user_uid} does not have FCM token")
                return {"success": False, "error": "FCM token not found"}
            
            # Send notification
            result = await self.send_to_token(fcm_token, title, body, data, image_url)
            
            if result['success']:
                logger.info(f"Notification sent to user {user_uid}: {title}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending notification to user: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_to_token(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a specific FCM token.
        
        Args:
            fcm_token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional data payload
            image_url: Optional image URL
            
        Returns:
            dict: Result with success status and message ID or error
        """
        if not self.enabled or not self.fcm_enabled:
            return {"success": False, "error": "Push notifications disabled"}
        
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        priority='high'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Notification sent successfully: {response}")
            return {"success": True, "message_id": response}
            
        except messaging.UnregisteredError:
            logger.warning(f"FCM token is invalid or unregistered: {fcm_token}")
            return {"success": False, "error": "Invalid FCM token"}
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_to_multiple_users(
        self,
        user_uids: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple users.
        
        Args:
            user_uids: List of Firebase user UIDs
            title: Notification title
            body: Notification body
            data: Optional data payload
            image_url: Optional image URL
            
        Returns:
            dict: Results with success/failure counts
        """
        if not self.enabled or not self.fcm_enabled:
            return {"success": False, "error": "Push notifications disabled"}
        
        results = {
            "total": len(user_uids),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for user_uid in user_uids:
            result = await self.send_to_user(user_uid, title, body, data, image_url)
            
            if result['success']:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    "user_uid": user_uid,
                    "error": result.get('error')
                })
        
        logger.info(f"Batch notification sent: {results['sent']}/{results['total']} successful")
        return results
    
    async def send_to_multiple_tokens(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple FCM tokens (batch send).
        
        Args:
            fcm_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Optional data payload
            image_url: Optional image URL
            
        Returns:
            dict: Batch send results
        """
        if not self.enabled or not self.fcm_enabled:
            return {"success": False, "error": "Push notifications disabled"}
        
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build multicast message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=fcm_tokens,
                android=messaging.AndroidConfig(
                    priority='high'
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default')
                    )
                )
            )
            
            # Send multicast
            response = messaging.send_multicast(message)
            
            logger.info(f"Batch notification sent: {response.success_count}/{len(fcm_tokens)} successful")
            
            return {
                "success": True,
                "total": len(fcm_tokens),
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [
                    {
                        "success": resp.success,
                        "message_id": resp.message_id if resp.success else None,
                        "error": str(resp.exception) if not resp.success else None
                    }
                    for resp in response.responses
                ]
            }
            
        except Exception as e:
            logger.error(f"Error sending batch notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_data_message(
        self,
        fcm_token: str,
        data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Send data-only message (silent push) to FCM token.
        
        Args:
            fcm_token: FCM device token
            data: Data payload (must be dict of strings)
            
        Returns:
            dict: Result with success status
        """
        if not self.enabled or not self.fcm_enabled:
            return {"success": False, "error": "Push notifications disabled"}
        
        try:
            message = messaging.Message(
                data=data,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high'
                )
            )
            
            response = messaging.send(message)
            
            logger.info(f"Data message sent successfully: {response}")
            return {"success": True, "message_id": response}
            
        except Exception as e:
            logger.error(f"Error sending data message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_topic_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send notification to a topic (for broadcast messages).
        
        Args:
            topic: Topic name
            title: Notification title
            body: Notification body
            data: Optional data payload
            
        Returns:
            dict: Result with success status
        """
        if not self.enabled or not self.fcm_enabled:
            return {"success": False, "error": "Push notifications disabled"}
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )
            
            response = messaging.send(message)
            
            logger.info(f"Topic notification sent to '{topic}': {response}")
            return {"success": True, "message_id": response}
            
        except Exception as e:
            logger.error(f"Error sending topic notification: {str(e)}")
            return {"success": False, "error": str(e)}
