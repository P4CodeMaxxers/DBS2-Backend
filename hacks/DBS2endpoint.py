from flask import Blueprint, jsonify  # jsonify creates an endpoint response object
from flask_restful import Api, Resource # used for REST API building
import requests  # used for testing 
import random

from hacks.DBS2data import *

DBS2_api = Blueprint('DBS2_api', __name__,
                   url_prefix='/api/DBS2')

# API generator https://flask-restful.readthedocs.io/en/latest/api.html#id1
api = Api(DBS2_api)

class DBS2API:
    # not implemented
    class _Create(Resource):
        def post(self, item):
            pass
            
    # getDBS2Items()
    class _Read(Resource):
        def get(self):
            return jsonify(getDBS2Items())

    # getDBS2Item(id)
    class _ReadID(Resource):
        def get(self, id):
            return jsonify(getDBS2Item(id))

    # getRandomDBS2Item()
    class _ReadRandom(Resource):
        def get(self):
            return jsonify(getRandomDBS2Item())
    
    # countDBS2Items()
    class _ReadCount(Resource):
        def get(self):
            count = countDBS2Items()
            countMsg = {'count': count}
            return jsonify(countMsg)

    # put method: addDBS2Like
    # Like/dislike endpoints removed (not used by frontend)

    # building RESTapi resources/interfaces, these routes are added to Web Server
    api.add_resource(_Create, '/create/<string:item>', '/create/<string:item>/')
    api.add_resource(_Read, "", '/')
    api.add_resource(_ReadID, '/<int:id>', '/<int:id>/')
    api.add_resource(_ReadRandom, '/random', '/random/')
    api.add_resource(_ReadCount, '/count', '/count/')


if __name__ == "__main__": 
    # server = "http://127.0.0.1:5000" # run local
    server = 'https://flask.opencodingsociety.com' # run from web
    url = server + "/api/DBS2"
    responses = []  # responses list

    # get count of items on server
    count_response = requests.get(url+"/count")
    count_json = count_response.json()
    count = count_json['count']

    # update likes/dislikes test sequence

    num = str(random.randint(0, count-1)) # test a random record
    responses.append(
        requests.get(url+"/"+num)  # read item by id
    )

    # obtain a random item
    responses.append(
        requests.get(url+"/random")  # read a random item
    )

    # cycle through responses
    for response in responses:
        print(response)
        try:
            print(response.json())
        except:
            print("unknown error")
            print("unknown error")