import pymongo
from pymongo import MongoClient

import os
from dotenv import load_dotenv

from flask import request

from datetime import datetime
from bson.objectid import ObjectId

import json


load_dotenv()
# Define which cluster
mongo_link = os.getenv("MONGODB_LINK")
cluster = MongoClient(mongo_link)

# Define database & collection
db = cluster["storage"]
collection = db["pdf_collection"]

def createDocument(file_name):
    try:
        date = datetime.now()
        # formatted_date = date.strftime('%Y-%m-%dT%H:%M:%S')
        format = {
            "name":file_name,
            "datetime": date,
            "status":"Pending"
        }
        result = collection.insert_one(format)
        return result.inserted_id
    except Exception as e:
        print(f"Error in createDocument: {e}")
        return None

def updateDocument(list_of_dicts,document_id,status):
    try:
        result = collection.update_one({"_id":ObjectId(document_id)},{"$set":{"entity_relationship":list_of_dicts,"status":status}})
        return True
    except Exception as e:
        print(f"Error in updateDocument: {e}")
        return False

def getNumberOfDocuments():
    number = collection.count_documents({})
    return number

def getJsonWithId(object_id):
    try:
        currentDocument = collection.find({"_id":ObjectId(object_id)})

        if not currentDocument:
            print(f"Document with ID {object_id} not found")
            return None
        
        if "entity_relationship" not in currentDocument[0]:
            print("Entity relationships not found in the document")
            return None

        result = currentDocument[0]["entity_relationship"]
        return result
    except Exception as e:
        print(f"Error in updateDocument: {e}")
        return None


# updateDocument(sample_list,"679a01f484a2603e7058b1db","Confirmed")

# # Sample create
# # Will have a default _id tag
# test_format = {"name":"huzzer123", "score":56}
# yuur = collection.insert_one(test_format)
# print(yuur.inserted_id)


# # Sample Get
# results = collection.find({"name":"timmer"})
# print(results[0])
# print(results[0]["_id"])

# one_result = collection.find_one({"name":"timmer"})
# print(one_result)

# # Sample Update
# # first param is the WHERE condition, 2nd param is operator and the value u want to update
# result = collection.update_one({"name":"timmer"},{"$set":{"score":69}})
# # adding a new field
# result = collection.update_one({"name":"timmer"},{"$set":{"lmao":"defuq"}})

# # Counting documents in collection
# post_count = collection.count_documents({}) # Searching for everything
# print(post_count)



# pdf_name, date&time, json result, status: (running, completed, failed)
# function to create the entry 


# param to get the status
# function to update the entry