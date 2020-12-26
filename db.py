import pymongo
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo import errors
import datetime

class Mongo:

    def __init__(self, dbString, dbName):
        self.client:MongoClient = MongoClient(dbString)
        self.db:MongoClient = self.client[dbName]
        

    def insert(self, block, collectionName):
        try:
            collection = self.db[collectionName]
            print(f'len of the block :: {len(block)}')
            if len(block) == 1:
                return True, collection.insert_one(block[0]).inserted_id
            else:
                return True, collection.insert_many(block)
        except Exception as e:
            print("An exception ocurred ::", e)
            return False, None

    
    def get_doc(self, block, collectionName):
        collection = self.db[collectionName]
        return collection.find_one(block)

    def get_docById(self, docId, collectionName):
        collection = self.db[collectionName]
        return collection.find_one({"_id" : ObjectId(docId)})


    def get_docs(self, block, collectionName, sortVar = None):
        collection = self.db[collectionName]
        return collection.find(block) if sortVar == None else collection.find(block).sort(sortVar)

    def isDocExists(self, block, collectionName):
        ret = self.get_doc(block, collectionName)
        return False if ret == None else True

    def isDocExistsById(self, docId, collectionName):
        ret = self.get_docById(docId, collectionName)
        return False if ret == None else True






    

        


'''x:Mongo = Mongo('mongodb://localhost:27017/', 'test')

block = {
    "_id" : "5fdee8e175152ddc9e49a509"
}

ret = x.get_docs({}, 'hello')

for item in ret:
    print(item.get('name'))'''
