from pox.core import core

class LearningTable (object):

    def __init__(self):
        self.log = core.getLogger()
        self.macMap = {}

    def getPropertiesForMAC(self, macAddress):
        if macAddress not in self.macMap:
            log.error("ERROR: Called getProperties for non existent MAC Address: ".join(macAddress)
            return None
        else:
            return self.macMap[macAddress]

    def createNewEntryForMAC(self, macAddress):
        if macAddress in self.macMap:
            log.error("ERROR: Called createNewEntry for existent MAC Address: ".join(macAddress)
        else:
            self.macMap[macAddress] = HostProperties()
        return self.getPropertiesForMAC(macAddress)

    def createNewEntryWithProperties(self, macAddress, knownIP, reachableThroughPort, lastMile):
        hostProperties = self.createNewEntryForMAC(macAddress)
        hostProperties.addUniqueIP(knownIP)
        hostProperties.addUniquePort(reachableThroughPort)
        hostProperties.lastMile = lastMile


    def appendKnownIP(self, macAddress, knownIP):
        self.getPropertiesForMAC(macAddress).addUniqueIP(knownIP)

    def appendReachableThroughPort(self, macAddress, port):
        self.getPropertiesForMAC(macAddress).addUniquePort(port)

    def setLastMile(self, macAddress, lastMile):
        self.getPropertiesForMAC(macAddress).lastMile = lastMile

    def isLastMile(self, macAddress):
        return self.getPropertiesForMAC(macAddress).lastMile

    def isIPKnown(self, macAddress, ipAddress):
        return ipAddress in self.getPropertiesForMAC(macAddress).knownIPs
