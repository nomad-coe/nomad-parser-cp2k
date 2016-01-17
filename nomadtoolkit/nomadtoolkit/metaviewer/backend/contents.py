import json
import os
from nomadtoolkit.utils.config import get_config
from nomadcore.local_meta_info import loadJsonFile
import logging
from collections import defaultdict
logger = logging.getLogger(__name__)


def load_metainfo():
    path = get_config("metaInfoPath") + "/cp2k.nomadmetainfo.json"
    env, warnings = loadJsonFile(path)
    return env


def get_metainfos():
    env = load_metainfo()
    return reorganize_metainfos(env)


def reorganize_metainfos(env):

    metas = {}
    roots = {}

    for meta in env.infoKinds.values():
        metaobj = create_metainfo_object(meta)
        metas[metaobj.name] = metaobj

    for meta in metas.itervalues():
        parentNames = meta.superNames
        if len(parentNames) == 0:
            roots[meta.name] = meta
        else:
            for parentName in parentNames:
                parent = metas[parentName]
                parent.children.append(meta)

    section_run = roots["section_run"]
    jsonobject = json.dumps(section_run, default=lambda o: o.__dict__)

    return jsonobject


def create_metainfo_object(meta):
    metaobj = MetaInfo()
    metaobj.name = meta.name
    metaobj.description = meta.description
    if meta.shape:
        metaobj.shape = meta.shape
    else:
        metaobj.shape = None
    metaobj.units = meta.units
    metaobj.dtypeStr = meta.dtypeStr
    metaobj.kindStr = meta.kindStr
    metaobj.superNames = meta.superNames
    return metaobj


class MetaInfo(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.shape = None
        self.kindStr = None
        self.units = None
        self.dtypeStr = None
        self.repeats = None
        self.children = []
        self.superNames = []

# def print_children(meta, level=0):
    # for child in meta.children:
        # print "  "*level + child.name
        # print_children(child, level+1)


# def get_results():
    # results = load_results()
    # reorganized_results = reorganize_results(results)
    # return reorganized_results


# def load_results():
    # """Load the parsed results from a json file and return them as a JSON
    # object.
    # """

    # config = open_config_json()
    # resultpath = config["outputpath"]

    # resultfile = open(resultpath, "r")
    # resultjson = json.load(resultfile)

    # return resultjson


# def reorganize_results(jsonobject):

    # metainfoenv = load_metainfo()
    # events = jsonobject[0]["events"]
    # sectionStack = []
    # rootSection = None
    # lastRepeated = None
    # parent = None

    # for event in events:
        # eventName = event["event"]
        # metaName = event["metaName"]
        # metainfo = metainfoenv[metaName]
        # repeats = metainfo.get("repeats", False)

        # # Add new section
        # if eventName == "openSection":
            # section = Section()
            # section.name = metaName
            # section.metainfo = metainfo
            # if repeats and lastRepeated is None:
                # lastRepeated = section
                # print "Repeating found: " + metaName
            # if lastRepeated and lastRepeated.name != metaName:
                # print "Closing repeated: " + metaName
                # lastRepeated = None
                # try:
                    # parentSection = sectionStack[-2]
                # except IndexError:
                    # parentSection = None
                # childSection = sectionStack[-1]

                # if parentSection:
                    # print "Popping " + metaName
                    # parentSection.subSections.append(childSection)
                    # childSection.values = childSection.valueDict.values()
                    # childSection.arrayValues = childSection.arrayDict.values()
                    # childSection.valueDict = None
                    # childSection.arrayDict = None
                    # childSection.subSectionDict = None
                    # sectionStack.pop()
            # if not(lastRepeated and lastRepeated.name == metaName):
                # sectionStack.append(section)
                # parent = section

        # # Add value
        # elif eventName == "addValue":
            # value = parent.valueDict.get(metaName)
            # if value is None:
                # value = Value()
                # value.name = metaName
                # value.metainfo = metainfo
            # value.values.append(event["value"])
            # parent.valueDict[metaName] = value

        # # Add array value
        # elif eventName == "addArrayValues":
            # arrayValue = ArrayValue()
            # arrayValue.name = metaName
            # arrayValue.metainfo = metainfo
            # arrayValue.flatValues.append(event["flatValues"])
            # arrayValue.valuesShape.append(event["valuesShape"])
            # section = sectionStack[-1]
            # section.arrayDict[metaName].append(arrayValue)
        # # Close section
        # elif eventName == "closeSection":
            # if lastRepeated and lastRepeated.name == metaName:
                # # print "Skipping repeated close"
                # continue
            # try:
                # parentSection = sectionStack[-2]
            # except IndexError:
                # parentSection = None
            # childSection = sectionStack[-1]

            # if parentSection:
                # parentSection.subSections.append(childSection)
                # print "Popping " + metaName
                # childSection.values = childSection.valueDict.values()
                # childSection.arrayValues = childSection.arrayDict.values()
                # childSection.valueDict = None
                # childSection.arrayDict = None
                # childSection.subSectionDict = None
                # sectionStack.pop()

    # rootSection = sectionStack[0]
    # rootSection.values = rootSection.valueDict.values()
    # rootSection.arrayValues = rootSection.arrayDict.values()
    # rootSection.valueDict = None
    # rootSection.arrayDict = None
    # rootSection.subSectionDict = None
    # print rootSection.subSections
    # # print sectionStack[1]
    # jsonobject = json.dumps(rootSection, default=lambda o: o.__dict__)
    # return jsonobject


# class Result(object):
    # def __init__(self, name=None, metainfo=None):
        # self.name = name
        # self.metainfo = metainfo





# class Section(Result):
    # def __init__(self, name=None):
        # self.name = name
        # self.subSections = []
        # self.valueDict = defaultdict(list)
        # self.arrayDict = defaultdict(list)


# class Value(Result):
    # def __init__(self, name=None, value=None):
        # self.values = []


# class ArrayValue(Result):
    # def __init__(self, name=None):
        # self.flatValues = []
        # self.valuesShape = []


# if __name__ == "__main__":
    # print get_metainfos()
    # # get_results()
