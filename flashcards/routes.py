from flask import Blueprint, request, render_template, make_response
from decorators import mongo
import os
import uuid
import time
from pymongo import ReturnDocument

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
    try:
        data = request.json
        db_entry = {"_id": data["word"].lower(), "definition": data["definition"]}
        db["words"].insert_one(db_entry)
        return {"success": True}
    except Exception as E:
        print(E)
        return {"success": False}


@flashcards.route("/delete_word", methods=["POST"])
@mongo
def delete_word(db):
    try:
        word = request.json["word"]
        db_entry = {"_id": word}
        db["words"].delete_one(db_entry)
        return {"success": True}
    except Exception as E:
        print(E)
        return {"success": False}


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
    try:
        data = request.json
        successful = data["result"]

        # Function to standardize/DRY update queries
        def increment_query(inc=1, successful=True):
            db_query = {
                "$set": {"words.$[elem].last_answer": time.time()},
            }
            if successful:
                db_query["$inc"] = {"words.$[elem].bin": inc}
            else:
                db_query["$inc"] = {
                    "words.$[elem].bin": inc,
                    "words.$[elem].wrong_count": 1,
                }
            return db_query

        if successful:  # If answered correctly
            query = increment_query(1)  # Move up 1 in bin/competence
        else:
            if data["bin"] == 0:
                query = increment_query(1, successful=False)
            elif data["bin"] == 1:
                query = increment_query(0, successful=False)
            else:
                query = increment_query(-1, successful=False)
        # Query to perform necessary updates
        user = db["users"].find_one_and_update(
            {"_id": data["user"]},
            query,
            array_filters=[{"elem.word": data["word"]}],
            return_document=ReturnDocument.AFTER,
        )
        return {"success": True, "user": user}
    except Exception as E:
        print(E)
        return {"success": False}


# This function exists to synchronize user words with the words database
@flashcards.route("/update_user_words", methods=["POST"])
@mongo
def update_user_words(db):
    try:
        if request.json[
            "user_id"
        ]:  # would confirm admin privilege to do so in secure set up
            user_id = request.json["user_id"]
        else:
            user_id = request.cookies.get("_id")
        # Get the user
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
        return {"success": False, "user": user}


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
