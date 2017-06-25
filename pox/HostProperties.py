from pox.core import core

class HostProperties (object):
    
    def __init__(self):
        self.log = core.getLogger()
        self.knownIPs = []
        self.reachableThroughPorts = []
        self.lastMile = False

    def addUniqueIP(self, ipAddress):
        if ipAddress not in self.knownIPs:
            self.knownIPs.append(ipAddress)

    def addUniquePort(self, port):
        if port not in self.reachableThroughPorts:
            self.reachableThroughPorts.append(port)

    def hostKnowsIP(self, ipAddress):
        return ipAddress in self.knownIPs
