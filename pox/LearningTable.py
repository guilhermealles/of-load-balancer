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

    def learnDataFromPacket(self, packet, packetIn, lastMile = False):
        sourceMAC = packet.dst
        if self.macIsKnown(sourceMAC):
            self.appendReachableThroughPort(sourceMAC, packetIn.in_port)
            if lastMile == False and self.isLastMile(sourceMAC):
                lastMile = True
            self.setLastMile(sourceMAC, lastMile)
        else:
            self.createNewEntryWithProperties(sourceMAC, packetIn.in_port, lastMile)

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

    def getFirstReachableThroughPort(self, macAddress):
        return self.getPropertiesForMAC(macAddress).reachableThroughPorts[0]

    def getRandomReachableThroughPort(self, macAddress, excludePort):
        candidatePorts = list(self.getPropertiesForMAC(macAddress).reachableThroughPorts)
        if excludePort in candidatePorts:
            candidatePorts.remove(excludePort)
        return random.choice(candidatePorts)

    def getAnyPortToReachHost(self, macAddress, excludePort):
        return self.getRandomReachableThroughPort(macAddress, excludePort)
