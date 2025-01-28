import pymongo
from pymongo import MongoClient

import os
from dotenv import load_dotenv

load_dotenv()
# Define which cluster
mongo_link = os.getenv("MONGODB_LINK")
cluster = MongoClient("mongodb+srv://password:SMU@smubia-hackathon.zpcu3.mongodb.net/?retryWrites=true&w=majority&appName=SMUBIA-Hackathon")

# Define database & collection
db = cluster["storage"]
collection = db["test"]

# # Sample create
# # Will have a default _id tag
# test_format = {"name":"timmer", "score":5}
# collection.insert_one(test_format)

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

# Counting documents in collection
post_count = collection.count_documents({}) # Searching for everything
print(post_count)



# pdf_name, date&time, json result, status: (running, completed, failed)
# function to create the entry 


# param to get the status
# function to update the entry