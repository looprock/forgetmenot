#!/usr/bin/env python
from bottle import Bottle, request, abort
import time
import logging
import os
import sys
import urlparse
import pymongo
from pymongo import MongoClient
from optparse import OptionParser
import yaml

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

# this is just a test route to see what's getting posted
@app.post('/todo', method='POST')
def postprint():
    postdata = request.body.read()
    # data = json.loads(postdata)
    logging.debug(postdata)
    params_dict = urlparse.parse_qsl(postdata)
    postdate = time.strftime('%Y-%m-%dT%H:%M:%S%Z', time.localtime())
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
            result = todos.insert_one(ndict)
            logging.debug("inserting:")
            logging.debug(ndict)
        except:
            logging.critical("Unable to post to %s" % server)
        logging.info('One post: {0}'.format(result.inserted_id))
    else:
        logging.warning("Invalid number: %s" % params['From'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='18080', server='tornado', reloader=False)
