'''
This module initializes Firebase Admin SDK and provides functions for
authentication and Firestore database operations such as creating users,
managing user profiles, and handling conversations.

'''
import firebase_admin
from firebase_admin import credentials, auth, firestore
import json
import os
from datetime import datetime

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    
    # Check if Firebase is already initialized
    try:
        firebase_admin.get_app()
    except ValueError:
        # Firebase not initialized, so initialize it
        import os
        config_path = os.path.join(os.path.dirname(__file__), 'firebase_config.json')
        cred = credentials.Certificate(config_path)
        firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    db = firestore.client()
    return db


# Authentication Functions
def create_user(email, password):
    """Create a new user with email and password"""
    try:
        user = auth.create_user(email=email, password=password)
        return {"success": True, "uid": user.uid, "message": "User created successfully"}
    except auth.EmailAlreadyExistsError:
        return {"success": False, "message": "Email already exists"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def login_user(email, password):
    """Verify user credentials (basic check, real auth happens in Streamlit)"""
    try:
        # In a real app, you'd use Firebase REST API or custom tokens
        # For now, we just verify the user exists
        user = auth.get_user_by_email(email)
        return {"success": True, "uid": user.uid, "message": "Login successful"}
    except auth.UserNotFoundError:
        return {"success": False, "message": "User not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# Firestore Functions
def create_user_profile(uid, email, username):
    """Create a user profile in Firestore"""
    db = firestore.client()
    try:
        user_data = {
            "uid": uid,
            "email": email,
            "username": username,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        db.collection("users").document(uid).set(user_data)
        return {"success": True, "message": "User profile created"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_user_profile(uid):
    """Get user profile from Firestore"""
    db = firestore.client()
    try:
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return {"success": True, "data": doc.to_dict()}
        else:
            return {"success": False, "message": "User not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def save_conversation(uid, conversation_title, messages):
    """Save a conversation to Firestore"""
    db = firestore.client()
    try:
        conv_data = {
            "uid": uid,
            "title": conversation_title,
            "messages": messages,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        # Add to conversations collection and get the document ID
        doc_ref = db.collection("conversations").add(conv_data)
        return {"success": True, "conv_id": doc_ref[1].id, "message": "Conversation saved"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_user_conversations(uid):
    """Get all conversations for a user"""
    db = firestore.client()
    try:
        docs = db.collection("conversations").where("uid", "==", uid).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        conversations = []
        for doc in docs:
            conv = doc.to_dict()
            conv["conv_id"] = doc.id
            conversations.append(conv)
        return {"success": True, "data": conversations}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_conversation(conv_id):
    """Get a specific conversation by ID"""
    db = firestore.client()
    try:
        doc = db.collection("conversations").document(conv_id).get()
        if doc.exists:
            return {"success": True, "data": doc.to_dict()}
        else:
            return {"success": False, "message": "Conversation not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def update_conversation(conv_id, messages):
    """Update a conversation with new messages"""
    db = firestore.client()
    try:
        db.collection("conversations").document(conv_id).update({
            "messages": messages,
            "updated_at": datetime.now()
        })
        return {"success": True, "message": "Conversation updated"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def delete_conversation(conv_id):
    """Delete a conversation"""
    db = firestore.client()
    try:
        db.collection("conversations").document(conv_id).delete()
        return {"success": True, "message": "Conversation deleted"}
    except Exception as e:
        return {"success": False, "message": str(e)}