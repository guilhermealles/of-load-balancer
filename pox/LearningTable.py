from pox.core import core
from HostProperties import HostProperties
import random

class LearningTable (object):

    def __init__(self):
        self.log = core.getLogger()
        self.macMap = {}

    def getPropertiesForMAC(self, macAddress):
        if macAddress not in self.macMap:
            self.log.error("ERROR: Called getProperties for non existent MAC Address: ".join(macAddress))
            return None
        else:
            return self.macMap[macAddress]

    def macIsKnown(self, macAddress):
        return macAddress in self.macMap

    def createNewEntryForMAC(self, macAddress):
        if macAddress in self.macMap:
            self.log.error("ERROR: Called createNewEntry for existent MAC Address: ".join(macAddress))
        else:
            self.macMap[macAddress] = HostProperties()
        return self.getPropertiesForMAC(macAddress)

    def createNewEntryWithProperties(self, macAddress, reachableThroughPort, lastMile):
        hostProperties = self.createNewEntryForMAC(macAddress)
        hostProperties.addUniquePort(reachableThroughPort)
        hostProperties.lastMile = lastMile

    def appendKnownIPForMAC(self, macAddress, ipAddress):
        self.getPropertiesForMAC(macAddress).addUniqueIP(ipAddress)

    def appendReachableThroughPort(self, macAddress, port):
        self.getPropertiesForMAC(macAddress).addUniquePort(port)

    def setLastMile(self, macAddress, lastMile):
        self.getPropertiesForMAC(macAddress).lastMile = lastMile

    def isIPKnownForMAC(self, macAddress, ipAddress):
        return self.getPropertiesForMAC(macAddress).isIPKnown(ipAddress)

    def isLastMile(self, macAddress):
        return self.getPropertiesForMAC(macAddress).lastMile

    def getCandidatePorts(self, macAddress, excludePort):
        candidatePorts = list(self.getPropertiesForMAC(macAddress).reachableThroughPorts)
        if excludePort in candidatePorts:
            candidatePorts.remove(excludePort)
        return candidatePorts

    def getFirstReachableThroughPort(self, macAddress, excludePort):
        return self.getCandidatePorts(macAddress, excludePort)[0]

    def getRandomReachableThroughPort(self, macAddress, excludePort):
        candidatePorts = self.getCandidatePorts(macAddress, excludePort)
        return random.choice(candidatePorts)

    def getUnusedPortToHost(self, macAddress, excludePort):
        candidatePorts = self.getCandidatePorts(macAddress, excludePort)
        lastPort = self.getPropertiesForMAC(macAddress).lastPort
        if len(candidatePorts) > 1 and (lastPort not None) and (lastPort in candidatePorts):
            candidatePorts.remove(lastPort)
        chosenPort = random.choice(candidatePorts)

    def getAnyPortToReachHost(self, macAddress, excludePort):
        return self.getUnusedPortToHost(macAddress, excludePort)
