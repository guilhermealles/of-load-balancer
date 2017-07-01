from pox.core import core
import datetime
from collections import deque
class HostProperties (object):

    def __init__(self):
        self.log = core.getLogger()
        self.reachableThroughPorts = deque()
        self.lastPort = None
        self._knownIPsTimeout = {}
        self.lastMile = False

    def addUniquePort(self, port):
        if port not in self.reachableThroughPorts:
            self.reachableThroughPorts.append(port)

    def addUniqueIP(self, ipAddress):
        self._updateIPsTimeout(ipAddress)
        if ipAddress not in self._knownIPsTimeout:
            self._knownIPsTimeout[ipAddress] = datetime.datetime.now()

    def isIPKnown(self, ipAddress):
        self._updateIPsTimeout(ipAddress)
        return ipAddress in self._knownIPsTimeout

    def getKnownIPsList(self):
        ipList = []
        for ip in self._knownIPsTimeout:
            self._updateIPsTimeout(ip)
            if ip in self._knownIPsTimeout:
                ipList.append(ip)
        return ipList

    def _updateIPsTimeout(self, ipAddress):
        if ipAddress in self._knownIPsTimeout:
            now = datetime.datetime.now()
            if (now - self._knownIPsTimeout[ipAddress]).seconds >= 1:
                del self._knownIPsTimeout[ipAddress]
