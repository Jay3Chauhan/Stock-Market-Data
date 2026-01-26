"""
User Database Operations
=========================
MongoDB CRUD operations for user management.

This module handles:
- User creation and registration
- User retrieval by UID, phone, email
- User updates (FCM token, profile)
- User deletion
- User listing with filters

Collection: users
Database: NSE_SCRAPER (from config.ini)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from pymongo import ASCENDING, DESCENDING
from Utils.logger import get_logger
from Utils.db import DatabaseManager

logger = get_logger(__name__)

# IST timezone offset
IST_OFFSET = timedelta(hours=5, minutes=30)


def get_ist_timestamp() -> str:
    """Get current timestamp in IST"""
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + IST_OFFSET
    return ist_now.isoformat()


class UserDatabase:
    """Database operations for user management"""
    
    def __init__(self):
        """Initialize User Database with MongoDB connection"""
        self.db_manager = DatabaseManager()
        self.collection_name = "users"
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for users collection"""
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            # Drop old phone_number index if it exists (from when it was unique)
            try:
                existing_indexes = collection.index_information()
                if 'phone_number_1' in existing_indexes:
                    old_index = existing_indexes['phone_number_1']
                    # Check if it's the old unique index
                    if old_index.get('unique', False):
                        logger.info("Dropping old unique phone_number index")
                        collection.drop_index('phone_number_1')
            except Exception as drop_error:
                logger.warning(f"Could not drop old phone_number index: {str(drop_error)}")
            
            # Create indexes
            collection.create_index([("uid", ASCENDING)], unique=True)
            collection.create_index([("email", ASCENDING)], unique=True, sparse=True)
            collection.create_index([("phone_number", ASCENDING)], sparse=True)  # Not unique - optional field
            collection.create_index([("created_at", DESCENDING)])
            collection.create_index([("last_login", DESCENDING)])
            
            logger.info(f"Indexes created for collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    async def create_user(
        self,
        uid: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        phone_number: Optional[str] = None,
        fcm_token: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user in the database.
        
        Args:
            uid: Firebase user UID (required)
            email: Email address
            display_name: User's display name
            photo_url: Profile photo URL
            phone_number: Phone number (optional, for display only, not used for auth)
            fcm_token: FCM device token
            metadata: Additional metadata
            
        Returns:
            dict: Created user document
            None: If creation failed
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            # Check if user already exists
            existing_user = collection.find_one({"uid": uid})
            if existing_user:
                logger.warning(f"User already exists with UID: {uid}")
                return None
            
            # Build user document
            current_time = get_ist_timestamp()
            
            user_doc = {
                "uid": uid,
                "email": email,
                "display_name": display_name,
                "photo_url": photo_url,
                "phone_number": phone_number,
                "fcm_token": fcm_token,
                "is_active": True,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": current_time,
                "metadata": metadata or {}
            }
            
            # Insert user
            result = collection.insert_one(user_doc)
            
            if result.inserted_id:
                user_doc['_id'] = str(result.inserted_id)
                logger.info(f"User created successfully: {uid}")
                return user_doc
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user by Firebase UID.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            dict: User document if found
            None: If user not found
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            user = collection.find_one({"uid": uid})
            
            if user:
                user['_id'] = str(user['_id'])
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by UID: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            dict: User document if found
            None: If user not found
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            user = collection.find_one({"email": email})
            
            if user:
                user['_id'] = str(user['_id'])
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def update_user(
        self,
        uid: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            uid: Firebase user UID
            update_data: Fields to update
            
        Returns:
            dict: Updated user document
            None: If update failed
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            # Add updated_at timestamp
            update_data['updated_at'] = get_ist_timestamp()
            
            # Update user
            result = collection.update_one(
                {"uid": uid},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"User updated successfully: {uid}")
                return await self.get_user_by_uid(uid)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return None
    
    async def update_fcm_token(self, uid: str, fcm_token: str) -> bool:
        """
        Update user's FCM token.
        
        Args:
            uid: Firebase user UID
            fcm_token: New FCM device token
            
        Returns:
            bool: True if updated successfully
        """
        try:
            result = await self.update_user(uid, {"fcm_token": fcm_token})
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating FCM token: {str(e)}")
            return False
    
    async def update_last_login(self, uid: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            bool: True if updated successfully
        """
        try:
            result = await self.update_user(uid, {"last_login": get_ist_timestamp()})
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            return False
    
    async def delete_user(self, uid: str) -> bool:
        """
        Delete user from database.
        
        Args:
            uid: Firebase user UID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            result = collection.delete_one({"uid": uid})
            
            if result.deleted_count > 0:
                logger.info(f"User deleted successfully: {uid}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status (None = all users)
            
        Returns:
            list: List of user documents
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            # Build query
            query = {}
            if is_active is not None:
                query['is_active'] = is_active
            
            # Get users
            users = list(
                collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return []
    
    async def get_all_users(self, is_active: Optional[bool] = True) -> List[Dict[str, Any]]:
        """
        Get all users (without pagination).
        
        Args:
            is_active: Filter by active status (True = active only, None = all users)
            
        Returns:
            list: List of all user documents
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            # Build query
            query = {}
            if is_active is not None:
                query['is_active'] = is_active
            
            # Get all users
            users = list(collection.find(query))
            
            # Convert ObjectId to string
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []
    
    async def count_users(self, is_active: Optional[bool] = None) -> int:
        """
        Count total users.
        
        Args:
            is_active: Filter by active status (None = all users)
            
        Returns:
            int: Total user count
        """
        try:
            collection = self.db_manager.mongo_db[self.collection_name]
            
            query = {}
            if is_active is not None:
                query['is_active'] = is_active
            
            return collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}")
            return 0
