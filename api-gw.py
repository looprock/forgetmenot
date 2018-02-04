#!/usr/bin/env python
from bottle import Bottle, request, abort
import time
import json
import logging
import os
import sys
import urlparse
import pymongo
from pymongo import MongoClient
from optparse import OptionParser
import yaml
from bson import ObjectId

cmd_parser = OptionParser(version="%prog 0.1")
cmd_parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debug mode")
cmd_parser.add_option("-c", "--config", action="store", dest="config", help="override config file", default="/etc/api-gw.yaml")
(cmd_options, cmd_args) = cmd_parser.parse_args()

# set up app
if cmd_options.debug:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    print("Debug enabled")
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    print("Debug disabled")

with open(cmd_options.config, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        sys.exit(exc)

req = ['server','username','password', 'allowed']
for i in req:
    if i not in config:
        logging.critical("required item %s not in config!" % i)
        sys.exit()

allowed = {}
for i in config['allowed']:
    logging.debug(i)
    allowed.update(i)
logging.debug(config['allowed'])
logging.debug(allowed)

app = Bottle()

server = "mongodb+srv://%s:%s@%s" % (config['username'], config['password'], config['server'])
client = MongoClient(server)

logging.debug(server)
logging.debug(allowed)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

# this is just a test route to see what's getting posted
@app.route('/todo', method=['POST', 'PUT'])
@app.get('/todo/<username>', method=['GET'])
@app.get('/todo/<username>/<id>', method=['GET'])
def postprint(username=None, id=None):
    print(request.get_header('content-type'))
    if request.method == 'POST':
        if request.get_header('content-type') == 'application/x-www-form-urlencoded':
            postdata = request.body.read()
            # data = json.loads(postdata)
            logging.debug(postdata)
            params_dict = urlparse.parse_qsl(postdata)
            postdate = time.strftime('%Y-%m-%dT%H:%M:%S%Z',time.localtime(time.time()))
            twoweeks = time.strftime('%Y-%m-%dT%H:%M:%S%Z',time.localtime(time.time() + 1209600))
            params = dict(params_dict)
            ndict = {}
            if params['From'] in allowed.keys():
                dbname = "todo-%s" % (allowed[params['From']])
                db = client[dbname]
                todos = db.todos
                ndict['author'] = allowed[params['From']]
                ndict['created'] = postdate
                ndict['content'] = params['Body']
                ndict['status'] = 'new'
                ndict['due'] = twoweeks
                ndict['topics'] = []
                ndict['links'] = []
                ndict['level'] = '1'
                ndict['priority'] = '1'
                logging.debug(ndict)
                try:
                    # result = todos.insert_one(ndict)
                    logging.debug("inserting:")
                    logging.debug(ndict)
                except:
                    logging.critical("Unable to post to %s" % server)
                # logging.info('One post: {0}'.format(result.inserted_id))
                logging.debug("worked!")
            else:
                logging.warning("Invalid number: %s" % params['From'])
        if request.get_header('content-type') == 'application/json':
            postdata = request.body.read()
            return json.loads(postdata)
    if request.method == 'GET':
        # return "username: %s" % (username)
        dbname = "todo-%s" % (username)
        db = client[dbname]
        todos = db.todos
        result = {}
        if id:
            # return "username: %s, id: %s" % (username,id)
            items = todos.find({"_id": ObjectId(id)})
            for item in items:
                tmp = {}
                nid = str(item['_id'])
                item.pop('_id', None)
                tmp[nid] = item
                logging.debug(item)
                result.update(tmp)
        else:
            items = todos.find()
            for item in items:
                tmp = {}
                nid = str(item['_id'])
                item.pop('_id', None)
                tmp[nid] = item
                result.update(tmp)
        # print(result)
        return result

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='18080', server='tornado', reloader=False)
