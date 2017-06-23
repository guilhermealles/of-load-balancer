from pox.core import core

class GlobalARPEntry (object):

    def __init__(self):
        self.log = core.getLogger()
        self.globalARPEntry = {}
        self.log.info("GlobalARPEntry initialized")

    def macExists(self, macAddress):
        return macAddress in self.globalARPEntry

    def createNewEntryForMAC(self, macAddress):
        if self.macExists(macAddress):
            self.log.warning("createNewEntryForMAC called with existant MAC ADDRESS: " + str(macAddress))
            return
        else:
            self.globalARPEntry[macAddress] = []

    def addUniqueIPForMAC(self, macAddress, ipAddress):
        if not self.macExists(macAddress):
            self.log.error("addUniqueIPForMac called with non existant MAC ADDRESS: " + str(macAddress))
            return
        else:
            if ipAddress not in self.globalARPEntry[macAddress]:
                self.globalARPEntry.append(ipAddress)

    def isIPKnownForMAC(self, macAddress, ipAddress):
        return self.macExists(macAddress) and ipAddress in self.globalARPEntry[macAddress]
