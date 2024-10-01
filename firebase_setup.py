import firebase_admin
from firebase_admin import credentials, firestore

# Provide the path to your Firebase JSON credentials file
cred = credentials.Certificate("/Users/rayansmacbook/Documents/Python Project/Crypto_Scout_Project/firebase_credentials.json")

# Initialize Firebase App with credentials
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()