#! python3
import os
import threading
import json
import importlib

class TextServiceInfo:
    def __init__(self):
        self.dirName = ""
        self.name = ""
        self.moduleName = ""
        self.serviceName = ""
        self.guid = ""
        self.textServiceClass = None
        self.modulPrefix = ""
        self.configModule = ""
        self.configHandlerName = ""
        self.configHandlerClass = None

    def loadFromJson(self, jsonFile):
        dirName = os.path.dirname(jsonFile)
        self.dirName = os.path.basename(dirName)
        self.modulePrefix = os.path.relpath(dirName).replace(os.sep, ".")
        # Read the moduleName(xxx.py) & serviceName(class name) from JSON
        jsonData = None
        with open(jsonFile, encoding = "UTF-8") as dataFile:
            jsonData = json.load(dataFile)
        if jsonData:
            self.name = jsonData.get("name", "")
            # text service module
            moduleName = jsonData.get("moduleName", "")
            if moduleName:
                self.moduleName = "%s.%s" % (self.modulePrefix, moduleName)
                print(self.moduleName)
            self.serviceName = jsonData.get("serviceName", "")
            self.guid = jsonData.get("guid", "").lower()

            # config module
            # FIXME: is it really a good idea to load all config modules 
            # at the same time?
            configModule = jsonData.get("configModule", "")
            self.configHandlerName = jsonData.get("configHandlerName", "")
            if configModule:
                self.configModule = "%s.%s" % (self.modulePrefix, configModule)
                # import the module
                mod = importlib.import_module(self.configModule)
                if self.configHandlerName:
                    self.configHandlerClass = getattr(mod, self.configHandlerName)


    def createInstance(self, client):
        if not self.moduleName or not self.serviceName or not self.guid:
            return None
        if not self.textServiceClass: # constructor is not yet imported
            # import the module
            mod = importlib.import_module(self.moduleName)
            self.textServiceClass = getattr(mod, self.serviceName)
            if not self.textServiceClass:
                return None
        return self.textServiceClass(client) # create a new instance for this text service


class TextServiceManager:
    def __init__(self):
        self.__lock = threading.Lock()
        self.services = {}
        self.enumerateServices()

    def enumerateServices(self):
        # To enumerate currently installed Input Method
        currentDir = os.path.dirname(os.path.abspath(__file__))
        input_methods_dir = os.path.join(currentDir, "input_methods")
        for subdir in os.listdir(input_methods_dir):
            filename = os.path.join(input_methods_dir, subdir, "ime.json")
            if os.path.exists(filename):
                info = TextServiceInfo()
                info.loadFromJson(filename)
                print(info.guid)
                if info.guid:
                    self.services[info.guid] = info

    def createService(self, client, guid):
        guid = guid.lower()
        if guid in self.services:
            info = self.services[guid]
            return info.createInstance(client)
        return None


textServiceMgr = TextServiceManager()