"""
Firebase Configuration Module
=============================
Initializes Firebase Admin SDK for the NSE Scraper application.

This module handles:
- Firebase Admin SDK initialization from service account JSON
- Singleton pattern for Firebase app instance
- Configuration from config.ini

Usage:
    from Utils.firebase_config import get_firebase_app
    
    app = get_firebase_app()
    if app:
        # Firebase is enabled and initialized
        ...
"""

import os
import firebase_admin
from firebase_admin import credentials
from typing import Optional
from Utils.logger import get_logger
from Utils.config_reader import configure

logger = get_logger(__name__)

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None
_firebase_enabled: bool = False


def initialize_firebase() -> Optional[firebase_admin.App]:
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Returns:
        firebase_admin.App: Initialized Firebase app instance
        None: If Firebase is disabled or initialization failed
    """
    global _firebase_app, _firebase_enabled
    
    # Check if already initialized
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Check if Firebase is enabled
        _firebase_enabled = configure.getboolean('FIREBASE', 'ENABLED', fallback=False)
        
        if not _firebase_enabled:
            logger.info("Firebase is disabled in configuration")
            return None
        
        # Get service account JSON path
        admin_sdk_path = configure.get('FIREBASE', 'ADMIN_SDK_PATH', fallback='firebase-admin-sdk.json')
        
        # Convert to absolute path if relative
        if not os.path.isabs(admin_sdk_path):
            # Assume relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            admin_sdk_path = os.path.join(project_root, admin_sdk_path)
        
        # Check if file exists
        if not os.path.exists(admin_sdk_path):
            logger.error(f"Firebase Admin SDK JSON file not found: {admin_sdk_path}")
            logger.error("Please place firebase-admin-sdk.json in the project root or update ADMIN_SDK_PATH in config.ini")
            return None
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(admin_sdk_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        
        logger.info(f"Firebase Admin SDK initialized successfully from: {admin_sdk_path}")
        logger.info(f"Firebase Project ID: {_firebase_app.project_id}")
        
        return _firebase_app
        
    except ValueError as e:
        # Firebase app already initialized
        if "The default Firebase app already exists" in str(e):
            logger.info("Firebase app already initialized, using existing instance")
            _firebase_app = firebase_admin.get_app()
            return _firebase_app
        else:
            logger.error(f"Firebase initialization error: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        logger.error("Firebase authentication features will be disabled")
        return None


def get_firebase_app() -> Optional[firebase_admin.App]:
    """
    Get the Firebase app instance (initializes if not already done).
    
    Returns:
        firebase_admin.App: Firebase app instance
        None: If Firebase is disabled or initialization failed
    """
    global _firebase_app
    
    if _firebase_app is None:
        _firebase_app = initialize_firebase()
    
    return _firebase_app


def is_firebase_enabled() -> bool:
    """
    Check if Firebase is enabled and initialized.
    
    Returns:
        bool: True if Firebase is enabled and initialized successfully
    """
    return get_firebase_app() is not None


# Initialize Firebase when module is imported (if enabled)
initialize_firebase()
