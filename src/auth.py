import pyrebase
from datetime import datetime

config = {
    "apiKey": "AIzaSyDNA-U6J2iHUGQ9PVEG4uZvGP6rZ7oY1k4",
    "authDomain": "competencygenie.firebaseapp.com",
    "databaseURL": "https://competencygenie-default-rtdb.firebaseio.com",
    "projectId": "competencygenie",
    "storageBucket": "competencygenie.appspot.com",
    "messagingSenderId": "725011772033",
    "appId": "1:725011772033:web:6977e7536cca949c4f5380",
    "measurementId": "G-8D047KXTM8"
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

def save_user(user,name):
    return db.child("users").child(user["localId"]).set({
        "full_name": name,
        "email": user["email"],
        "profilePic": "",
        "timestamp": str(datetime.now())
    })

# save prediction to firebase database
def save_prediction(pred_type,text,prediction):
    return db.child("questions").child(pred_type).push({
        "text": text,
        "prediction": prediction,
        "timestamp": str(datetime.now())
    })

def get_user(id):
    return dict(db.child("users").child(id).get().val())