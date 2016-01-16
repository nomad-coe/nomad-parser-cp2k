import os
import json


def open_config_file():
    return open(os.path.join(os.path.dirname(__file__), "config.json"), "r+")


def open_config_json():
    configfile = open_config_file()
    contents = configfile.read()
    jsonobject = json.loads(contents)
    return jsonobject


def set_config(name, value):
    configfile = open_config_file()
    contents = configfile.read()
    jsonobject = json.loads(contents)
    jsonobject[name] = value
    configfile.seek(0)
    configfile.truncate()
    configfile.write(json.dumps(jsonobject, configfile))


def get_config(name):
    jsonobj = open_config_json()
    return jsonobj.get(name)
