from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from GlobalARPEntry import GlobalARPEntry
from LearningTable import LearningTable

log = core.getLogger()
globalARPEntry = GlobalARPEntry()

class SwitchOFController (object):

    def __init__(self, connection):
        self.connection = connection
        self.switchId = str(connection)
        self.learningTable = LearningTable()
        connection.addListeners(self)
        log.debug("Switch ID " + self.switchId + ": controller started!")

    # Instructs the switch to resent a packet that was sent to the controller.
    # "packet_in" is the OpenFlow pabket that was sent to the controller because of a table-miss
    def resendPacket(self, packetIn, outPort):
        msg = of.ofp_packet_out()
        msg.data = packetIn
        action = of.ofp_action_output(port = outPort)
        msg.actions.append(action)
        self.connection.send(msg)

    def dropPacket(self, packetIn):
        msg = of.ofp_packet_out()
        msg.data = packetIn
        action = of.ofp_action_output(port = of.OFPP_NONE)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packetIn = event.ofp
        if self.packetIsARPRequest(packet):
            log.debug("Controller received ARP Request")
            self.handleARPRequest(packet, packetIn)
        else:
            log.debug("Controller received regular packet")
            self.actLikeL2Learning(packet, packetIn)

    def learnDataFromPacket(self, packet, packetIn, lastMile = False):
        sourceMAC = packet.src
        if self.learningTable.macIsKnown(sourceMAC):
            self.learningTable.appendReachableThroughPort(sourceMAC, packetIn.in_port)
            self.learningTable.setLastMile(sourceMAC, lastMile)
        else:
            self.learningTable.createNewEntryWithProperties(sourceMAC, packetIn.in_port, lastMile)

    def actLikeL2Learning(self, packet, packetIn):
        self.learnDataFromPacket(packet, packetIn)
        destinationMAC = packet.dst
        if self.learningTable.macIsKnown(destinationMAC):
            outPort = self.learningTable.getFirstReachableThroughPort(destinationMAC)
            self.resendPacket(packetIn, outPort)

    def packetIsARP(self, packet):
        return (packet.find('arp') is not None)

    def packetIsARPRequest (self, packet):
        return self.packetIsARP(packet) and packet.find('arp').opcode == 1

    # Assuming that the packet is guaranteed to be an ARP Request
    def handleARPRequest(self, packet, packetIn):
        if not self.packetIsARPRequest(packet):
            log.error("ERROR: Called handleArp on a non-arp packet!!")
            return
        arpPacket = packet.find('arp')
        lastMile = self.getLastMileAndUpdateGlobalARPEntry(arpPacket)
        sourceMAC = packet.src
        destinationIP = arpPacket.protodst
        if not self.learningTable.macIsKnown(sourceMAC):
            # This is a totally new host to the eyes of this switch
            self.learnDataFromPacket(packet, packetIn, lastMile)
            self.learningTable.appendKnownIPForMAC(sourceMAC, destinationIP)
            self.resendPacket(packetIn, of.OFPP_ALL)
        elif not self.learningTable.isIPKnownForMAC(sourceMAC, destinationIP):
            # This is a known host making a brand new ARP Request
            self.learnDataFromPacket(packet, packetIn, lastMile)
            self.learningTable.appendKnownIPForMAC(sourceMAC, destinationIP)
            self.resendPacket(packetIn, of.OFPP_ALL)
        else:
            # This is a known switch receiving the same ARP packet, probably due to a loop
            if not lastMile:
                self.learnDataFromPacket(packet, packetIn, lastMile)
            self.dropPacket(packetIn)

    def getLastMileAndUpdateGlobalARPEntry(self, arpPacket):
        requestorMAC = arpPacket.hwsrc
        requestedIP = arpPacket.protodst
        if not globalARPEntry.macExists(requestorMAC):
            globalARPEntry.createNewEntryForMAC(requestorMAC)
            globalARPEntry.addUniqueIPForMAC(requestorMAC, requestedIP)
            lastMile = True
        elif not globalARPEntry.isIPKnownForMAC(requestorMAC, requestedIP):
            globalARPEntry.addUniqueIPForMAC(requestorMAC, requestedIP)
            lastMile = True
        else:
            lastMile = False
        return lastMile

# Starts the component
def launch():
    
    def startSwitch(event):
        SwitchOFController(event.connection)
    core.openflow.addListenerByName("ConnectionUp", startSwitch)
