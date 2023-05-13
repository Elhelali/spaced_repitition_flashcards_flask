from flask import Blueprint, request, render_template, make_response
from decorators import mongo
import os
import uuid
import time
from pymongo import ReturnDocument
from .utils import *

flashcards = Blueprint(
    "flashcards", __name__, static_folder="build/static", template_folder="build"
)


@flashcards.route("/get_words")
@mongo
def get_words(db):
    words = list(db["words"].find())
    return {"words": words[::-1]}


@flashcards.route("/add_word", methods=["POST"])
@mongo
def add_word(db):
    data = request.json
    success = insert_word_into_db(db, data)
    return {"success": success}


@flashcards.route("/delete_word", methods=["POST"])
@mongo
def delete_word(db):
    word = request.json["word"]
    success = delete_word_from_db(db, word)
    return {"success": success}



# Create a new user. Sets a cookie to remember the user.
@flashcards.route("/create_user", methods=["POST"])
@mongo
def create_user(db):
    _id = str(uuid.uuid4())
    resp = make_response("Setting cookie")
    words = get_words()["words"]
    user_words = []
    for word in words:
        user_words.append(
            {
                "name": "",
                "word": word["_id"],  # word id = the word itself
                "definition": word["definition"],  # word definition
                "bin": 0,  # bins go from 0 to 11, higher bins represent higher competence
                "wrong_count": 0,  # Life time wrong count to determine unusually difficult words
                "last_answer": time.time(),  # initial setting allows word to appears
            }
        )
    db["users"].insert_one(
        {
            "name":"",
            "_id": _id,
            "words": user_words,
            "admin": True,  # In this simple implementation, there are no safeguards for admin page
        }
    )
    resp.set_cookie("_id", _id)
    return resp


# Get a user based on their cookie.
@flashcards.route("/get_user")
@mongo
def get_user(db):
    try:
        id = request.cookies.get("_id")
        user = db["users"].find_one({"_id": id})
        return {"user": user, "success": True}
    except Exception as E:
        return {"success": False}


@flashcards.route("/get_all_users")
@mongo
def get_all_users(db):
    try:
        users = list(db["users"].find())
        return {"users": users, "success": True}
    except Exception as E:
        return {"success": False}


# Submit a user's answer and update their progress.
@flashcards.route("/submit_result", methods=["POST"])
@mongo
def submit_result(db):
    data = request.json
    success, user = process_user_submission(db, data)
    return {"success": success, "user": user}

# This function exists to synchronize user words with the words database
@flashcards.route("/update_user_words", methods=["POST"])
@mongo
def update_user_words(db):
    try:
        if request.json.get('user_id'):  # would confirm admin token in secure set up
            user_id = request.json["user_id"]
        else:
            user_id = request.cookies.get("_id")
        user = db["users"].find_one({"_id": user_id})
        user_words = user["words"]
        # Get all words as an array for easier comparison
        user_word_ids = {word["word"] for word in user_words}
        # Get all words in words/admin db (source of truth)
        admin_words = list(db["words"].find())
        # Create a list of new user words, which will be used to update user
        new_user_words = []
        # First loop is used to remove any user words no longer in words/admin db
        for user_word in user_words:
            for word in admin_words:
                if word["_id"] == user_word["word"]:
                    new_user_words.append(user_word)

        # Second loop is to add any words in words db not in user words
        for word in admin_words:
            if word["_id"] not in user_word_ids:
                new_user_words.append(
                    {
                        "word": word["_id"],
                        "definition": word["definition"],
                        "bin": 0,
                        "last_answer": time.time(),
                        "wrong_count": 0,
                    }
                )
        # Run user db update, return updated user using Return Document
        user = db["users"].find_one_and_update(
            {"_id": user_id},
            {
                "$set": {"words": new_user_words},
            },
            return_document=ReturnDocument.AFTER,
        )
        return {"success": True, "user": user}
    except Exception as E:
        print(E)
        return {"success": False}


@flashcards.route("/update_name", methods=["POST"])
@mongo
def update_name(db):
    try:
        id = request.cookies.get("_id")
        db["users"].update_one({"_id": id}, {"$set": {"name": request.json["name"]}})
        return {"success": True}
    except Exception as E:
        print(E)
        return {"success": False}
