import StringIO


class LocalBackend(object):

    def __init__(self, metaInfoEnv, fileOut=StringIO.StringIO()):
        self.__metaInfoEnv = metaInfoEnv
        self.fileOut = fileOut
        self.__gIndex = -1
        self.__openSections = set()
        self.__writeComma = False
        self.__lastIndex = {}
        self.results = {}
        self.stats = {}

    def openSection(self, metaName):
        """opens a new section and returns its new unique gIndex"""
        newIndex = self.__lastIndex.get(metaName, -1) + 1
        self.openSectionWithGIndex(metaName, newIndex)
        return newIndex

    def openSectionWithGIndex(self, metaName, gIndex):
        """opens a new section where gIndex is generated externally
        gIndex should be unique (no reopening of a closed section)"""
        self.__lastIndex[metaName] = gIndex
        self.__openSections.add((metaName, gIndex))
        self.__jsonOutput({"event":"openSection", "metaName":metaName, "gIndex":gIndex})

    def __jsonOutput(self, dic):
        pass

    def closeSection(self, metaName, gIndex):
        self.__openSections.remove((metaName, gIndex))

    def addValue(self, metaName, value, gIndex=-1):
        if self.results.get(metaName) is None:
            self.results[metaName] = Result()
        self.results[metaName].values.append(value)

    def addRealValue(self, metaName, value, gIndex=-1):
        if self.results.get(metaName) is None:
            self.results[metaName] = Result()
        self.results[metaName].values.append(value)

    def addArrayValues(self, metaName, values, gIndex=-1):
        if self.results.get(metaName) is None:
            self.results[metaName] = Result()
        self.results[metaName].arrayValues.append(values)

    def metaInfoEnv(self):
        return self.__metaInfoEnv

    def startedParsingSession(self, mainFileUri, parserInfo, parsingStatus = None, parsingErrors = None):
        pass

    def finishedParsingSession(self, parsingStatus, parsingErrors, mainFileUri = None, parserInfo = None):
        pass


class Result(object):
    def __init__(self):
        self.values = []
        self.arrayValues = []
