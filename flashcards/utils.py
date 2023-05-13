from pymongo import ReturnDocument
import time

def insert_word_into_db(db, data):
    try:
        db_entry = {"_id": data["word"].lower(), "definition": data["definition"]}
        db["words"].insert_one(db_entry)
        return True
    except Exception as E:
        print(E)
        return False


def delete_word_from_db(db, word):
    try:
        db_entry = {"_id": word}
        db["words"].delete_one(db_entry)
        return True
    except Exception as E:
        print(E)
        return False


# Function to standardize/DRY user submission update queries
def build_update_query(inc=1, successful=True):
    db_query = {
        "$set": {"words.$[elem].last_answer": time.time()},
    }
    if successful:
        db_query["$inc"] = {"words.$[elem].bin": inc}
    else:
        db_query["$inc"] = {
            "words.$[elem].wrong_count": 1
        }
        db_query["$set"]["words.$[elem].bin"] = 1
    return db_query

# Function to standardize/DRY user submission update queries
# returns an updated query
def determine_bin_increment(bin,successful):
    if successful:  # If answered correctly
        query = build_update_query(1)  # Move up 1 in bin/competence
    else:
        query = build_update_query(successful=False)
    return query


def process_user_submission(db, data):
    try:
        successful = data["result"]
        query = determine_bin_increment(data['bin'],successful)
        # Query to perform necessary updates
        user = db["users"].find_one_and_update(
            {"_id": data["user"]},
            query,
            array_filters=[{"elem.word": data["word"]}],
            return_document=ReturnDocument.AFTER,
        )
        return True, user
    except Exception as E:
        print(E)
        return False, None