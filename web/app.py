from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SentencesDatabase
users = db["Users"]

class Register(Resource):
    def post(self):
        #Step 1 is to get posted data by the user
        postedData = request.get_json()

        #Get the data
        username = postedData["username"] or None
        password = postedData["password"] or None #"123xyz"

        if not username or not password:
            retJson = {
                "status": 301,
                "msg": "Enter Username and Password correctly"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        #Store username and pw into the database
        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Sentence": "",
            "Tokens":6
        })

        retJson = {
            "status": 200,
            "msg": "You successfully signed up for the API"
        }
        return jsonify(retJson)

def verifyPw(username, password):
    user = users.find_one({"Username": username})  # Finde den Benutzer

    if user is None:
        return False  # Benutzer nicht gefunden

    hashed_pw = user["Password"]  # Greife direkt auf das Passwort zu
    return bcrypt.checkpw(password.encode('utf8'), hashed_pw)  # Überprüfe das Passwort

def countTokens(username):
    tokens = users.find_one({
        "Username":username
    })["Tokens"]
    return tokens

class Store(Resource):
    def post(self):
        #Step 1 get the posted data
        postedData = request.get_json()

        #Step 2 is to read the data
        username = postedData["username"]
        password = postedData["password"]
        sentence = postedData["sentence"]

        #Step 3 verify the username pw match
        correct_pw = verifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status":302
            }
            return jsonify(retJson)
        #Step 4 Verify user has enough tokens
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = {
                "status": 301
            }
            return jsonify(retJson)

        #Step 5 store the sentence, take one token away  and return 200OK
        users.update_one({
            "Username":username
        }, {
            "$set":{
                "Sentence":sentence,
                "Tokens":num_tokens-1
                }
        })

        retJson = {
            "status":200,
            "msg":"Sentence saved successfully"
        }
        return jsonify(retJson)

class Get(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        #Step 3 verify the username pw match
        correct_pw = verifyPw(username, password)
        if not correct_pw:
            retJson = {
                "status":302
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = {
                "status": 301
            }
            return jsonify(retJson)

        #MAKE THE USER PAY!
        users.update_one({
            "Username":username
        }, {
            "$set":{
                "Tokens":num_tokens-1
                }
        })



        sentence = users.find_one({
            "Username": username
        })["Sentence"]
        retJson = {
            "status":200,
            "sentence": str(sentence)
        }

        return jsonify(retJson)




api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(Get, '/get')


if __name__=="__main__":
    app.run(host='0.0.0.0')
