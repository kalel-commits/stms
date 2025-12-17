"""
Firebase Firestore Database Operations for Traffic Management System
====================================================================
This module handles all database operations using Firebase Firestore.
Replaces SQLite with cloud-based Firebase for scalable data storage.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
_db = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    global _db
    
    if _db is None:
        # Get Firebase credentials path from environment variable or use default
        # Users should set FIREBASE_CREDENTIALS_PATH in .env file with their own credentials
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        
        # If not set in env, try common default names (users should use their own)
        if not cred_path:
            # Check for common Firebase credential file patterns
            default_names = [
                'firebase-credentials.json',
                'firebase-adminsdk.json',
                'serviceAccountKey.json'
            ]
            
            for name in default_names:
                if os.path.exists(name):
                    cred_path = name
                    break
            
            if not cred_path:
                raise FileNotFoundError(
                    "Firebase credentials file not found. "
                    "Please set FIREBASE_CREDENTIALS_PATH in .env file or place your credentials file in project root. "
                    "See FIREBASE_SETUP_INSTRUCTIONS.md for setup guide."
                )
        
        # Check if credentials file exists
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}. Please set FIREBASE_CREDENTIALS_PATH in .env file or place credentials file in project root.")
        
        # Initialize Firebase Admin SDK
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _db = firestore.client()
            print("Firebase initialized successfully")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise
    return _db

def get_db():
    """Get Firestore database instance"""
    if _db is None:
        return initialize_firebase()
    return _db

def get_connection():
    """
    Compatibility function - returns database instance for consistency with old code.
    Returns Firestore client instead of SQLite connection.
    """
    return get_db()

def close_connection(*args):
    """
    Compatibility function - no-op for Firebase (no connection to close).
    Firebase manages connections automatically.
    """
    pass

def create_database():
    """Initialize Firebase - collections are created automatically when first document is added"""
    try:
        db = initialize_firebase()
        print("Firebase database initialized")
        return db
    except Exception as e:
        print(f"Error initializing Firebase database: {e}")
        raise

def add_road(name: str, green_time: int, vehicle_count: int, capacity: int, 
             total_time: int, has_emergency_vehicle: bool, file_path: Optional[str] = None) -> str:
    """
    Adds a new road record to Firestore.
    Returns the document ID of the created road.
    """
    db = get_db()
    road_data = {
        'name': name,
        'green_time': green_time,
        'vehicle_count': vehicle_count,
        'capacity': capacity,
        'total_time': total_time,
        'hasEmergencyVehicle': has_emergency_vehicle,
        'filePath': file_path if file_path else None
    }
    
    # Add document to 'roads' collection
    # Firestore add() returns a tuple: (timestamp, DocumentReference)
    _, doc_ref = db.collection('roads').add(road_data)
    road_id = doc_ref.id  # Get document ID from DocumentReference
    return road_id

def update_hasEmergencyVehicle(road_id: str, has_emergency_vehicle: bool):
    """Updates the emergency vehicle presence for a specific road by id."""
    db = get_db()
    db.collection('roads').document(road_id).update({
        'hasEmergencyVehicle': has_emergency_vehicle
    })

def update_green_time(road_id: str, green_time: int):
    """Updates the green light duration for a specific road by id."""
    db = get_db()
    db.collection('roads').document(road_id).update({
        'green_time': green_time
    })

def update_vehicle_count(road_id: str, vehicle_count: int):
    """Updates the vehicle count for a specific road by id."""
    db = get_db()
    db.collection('roads').document(road_id).update({
        'vehicle_count': vehicle_count
    })

def update_file_path(road_id: str, file_path: str):
    """Updates the file path for the traffic data source of a specific road by id."""
    db = get_db()
    db.collection('roads').document(road_id).update({
        'filePath': file_path
    })

def get_green_time(road_id: str) -> Optional[int]:
    """Retrieves the green light duration for a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('green_time')
    return None

def get_vehicle_count(road_id: str) -> Optional[int]:
    """Retrieves the vehicle count for a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('vehicle_count')
    return None

def get_capacity(road_id: str) -> Optional[int]:
    """Retrieves the capacity for a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('capacity')
    return None

def get_total_time(road_id: str) -> Optional[int]:
    """Retrieves the total time data for a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('total_time')
    return None

def get_name(road_id: str) -> Optional[str]:
    """Retrieves the name of a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('name')
    return None

def get_file_path(road_id: str) -> Optional[str]:
    """Retrieves the file path for the traffic data source of a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('filePath')
    return None

def get_hasEmergencyVehicle(road_id: str) -> Optional[bool]:
    """Retrieves the emergency vehicle presence status for a specific road by id."""
    db = get_db()
    doc = db.collection('roads').document(road_id).get()
    if doc.exists:
        return doc.to_dict().get('hasEmergencyVehicle')
    return None

def get_all_roads():
    """Get all roads from Firestore"""
    db = get_db()
    roads = db.collection('roads').stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in roads]

def delete_road(road_id: str):
    """Delete a road document from Firestore"""
    db = get_db()
    db.collection('roads').document(road_id).delete()
