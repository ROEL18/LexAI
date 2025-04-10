"""
Firebase configuration for LexAI application.
This module initializes Firebase services and provides helper functions.
"""

import os
import json
import logging
import importlib.util

# Firebase configuration for client-side use
firebase_config = {
    "apiKey": "AIzaSyB6d6Guvapg7UZjMWCenUolKT0Kf_UXh0A",
    "authDomain": "lexai-1e745.firebaseapp.com",
    "databaseURL": "https://lexai-1e745-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "lexai-1e745",
    "storageBucket": "lexai-1e745.firebasestorage.app",
    "messagingSenderId": "307364280189",
    "appId": "1:307364280189:web:ee2688482a912d09673e14",
    "measurementId": "G-WZ3PJ6JHVE"
}

# Global variables
firebase_app = None
db = None
bucket = None
firebase_initialized = False
client_side_only_mode = False

def initialize_firebase():
    """Initialize Firebase services for the application."""
    global firebase_app, db, bucket, firebase_initialized, client_side_only_mode
    
    if firebase_initialized:
        return firebase_app, db, bucket
    
    # Check if firebase_admin is installed
    if importlib.util.find_spec("firebase_admin") is None:
        logging.warning("firebase_admin package not installed. Using client-side only mode.")
        client_side_only_mode = True
        return None, None, None
        
    try:
        from firebase_admin import credentials, initialize_app, firestore, auth, storage
        
        # Check if we have a service account key file
        if os.path.exists('serviceAccountKey.json'):
            try:
                # Validate the service account key file
                with open('serviceAccountKey.json', 'r') as f:
                    service_account_data = json.load(f)
                
                # Check for complete private key
                if len(service_account_data.get('private_key', '')) < 100:
                    logging.warning("Service account private key appears to be truncated. Using client-side only mode.")
                    client_side_only_mode = True
                    return None, None, None
                    
                cred = credentials.Certificate('serviceAccountKey.json')
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Invalid service account key file: {e}")
                client_side_only_mode = True
                return None, None, None
        else:
            # Try to use application default credentials
            try:
                cred = credentials.ApplicationDefault()
            except Exception as e:
                logging.error(f"Failed to get application default credentials: {e}")
                client_side_only_mode = True
                return None, None, None
        
        # Initialize Firebase app
        firebase_app = initialize_app(cred, {
            'storageBucket': firebase_config['storageBucket'],
            'databaseURL': firebase_config['databaseURL']
        })

        # Initialize Firestore
        db = firestore.client()
        
        # Initialize Storage
        bucket = storage.bucket()
        
        firebase_initialized = True
        logging.info("Firebase initialized successfully with server-side admin SDK")
        return firebase_app, db, bucket
        
    except Exception as e:
        logging.error(f"Error initializing Firebase: {e}")
        client_side_only_mode = True
        return None, None, None

# Try to initialize Firebase
firebase_app, db, bucket = initialize_firebase()

def get_firestore_db():
    """Get Firestore database instance."""
    global db
    if not firebase_initialized and not client_side_only_mode:
        _, db, _ = initialize_firebase()
    return db

def get_storage_bucket():
    """Get Firebase Storage bucket instance."""
    global bucket
    if not firebase_initialized and not client_side_only_mode:
        _, _, bucket = initialize_firebase()
    return bucket

def get_firebase_auth():
    """Get Firebase Auth instance."""
    if not firebase_initialized and not client_side_only_mode:
        initialize_firebase()
    
    try:
        from firebase_admin import auth
        return auth
    except ImportError:
        logging.error("Firebase auth not available")
        return None

def is_firebase_initialized():
    """Check if Firebase has been successfully initialized with server-side SDK."""
    global firebase_initialized
    return firebase_initialized

def is_client_side_only_mode():
    """Check if Firebase is in client-side only mode."""
    global client_side_only_mode
    return client_side_only_mode

def get_firebase_config():
    """Get Firebase configuration for client-side use."""
    return firebase_config