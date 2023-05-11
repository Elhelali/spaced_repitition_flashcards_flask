from flask import jsonify, Blueprint,request,send_from_directory,make_response
from decorators import mongo
import os
import uuid
import time
from pymongo import ReturnDocument

flashcards = Blueprint("flashcards", __name__, template_folder="templates",static_folder="build/static")

@flashcards.route('/get_words')
@mongo
def get_words(db):
    words = list(db['words'].find())
    return {"words":words[::-1]}

@flashcards.route('/add_word',methods=['POST'])
@mongo
def add_word(db):
    try:
        data = request.json
        db_entry={
            "_id":data['word'].lower(),
            "definition":data['definition']
        }
        db['words'].insert_one(db_entry)
        return {"success":True}
    except Exception as E:
        print(E)
        return {"success":False}
        
@flashcards.route('/delete_word',methods=['POST'])
@mongo
def delete_word(db):
    try:
        word = request.json['word']
        db_entry={
            "_id":word
        }
        db['words'].delete_one(db_entry)
        return {"success":True}
    except Exception as E:
        print(E)
        return {"success":False}
    
@flashcards.route('/create_user',methods=['POST'])
@mongo
def create_user(db):
    _id = str(uuid.uuid4())
    resp = make_response("Setting cookie")
    words = get_words()['words']
    user_words=[]
    for word in words:
        user_words.append({
            "word":word['_id'],
            "definition":word['definition'],
            "bin":0,
            "wrong_count":0,
            "last_answer":time.time() - 5  # so it appears now, not in 5 seconds
        })
    db['users'].insert_one({
        "_id":_id,
        "words":user_words
    })
    resp.set_cookie('_id', _id)
    return resp

@flashcards.route('/get_user')
@mongo
def get_user(db):
    try:
        id=(request.cookies.get("_id"))
        user=db['users'].find_one({"_id":id})
        return {'user':user,'success':True}
    except Exception as E:
        return {'success':False}
    
@flashcards.route('/submit_result',methods=['POST'])
@mongo
def submit_result(db):
    try:
        data = request.json
        successful = data['result']
        #user= db['users'].find_one({'user':data['user']})
        def increment_query(inc=1):
            db_query = {
                '$set': { 'words.$[elem].last_answer' : time.time()},
                }
            if inc>0:
                db_query['$inc'] = { 'words.$[elem].bin' : inc }
            elif inc ==0:
                pass
            else:
                db_query['$inc'] = { 'words.$[elem].bin' : inc, 'words.$[elem].wrong_count':1 }
            return db_query
        if successful: #answered correctly
            query = increment_query(1)
        else:
            if data['bin']==0:
                query = increment_query(0)
            else:
                query = increment_query(-1)
        #Query to perform necessary updates   
        user = db['users'].find_one_and_update(
        { '_id': data['user'] },
        query,
        array_filters=[ { 'elem.word': data['word'] } ],
        return_document=ReturnDocument.AFTER
        )
        return {'success' : True,"user":user}
    except Exception as E:
        print(E)
        return {'success' : False}