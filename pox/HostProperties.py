from pox.core import core

class HostProperties (object):
    
    def __init__(self):
        self.log = core.getLogger()
        self.reachableThroughPorts = []
        self.knownIPs = []
        self.lastMile = False

    def addUniquePort(self, port):
        if port not in self.reachableThroughPorts:
            self.reachableThroughPorts.append(port)

    def addUniqueIP(self, ipAddress):
        if ipAddress not in self.knownIPs:
            self.knownIPs.append(ipAddress)

    def isIPKnown(self, ipAddress):
        return ipAddress in self.knownIPs
