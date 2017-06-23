from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from GlobalARPEntry import GlobalARPEntry

log = core.getLogger()
globalARPEntry = GlobalARPEntry()

class SwitchOFController (object):

    def __init__(self, connection):
        self.connection = connection
        self.switchId = str(connection)
        connection.addListeners(self)
        log.debug("Switch ID " + self.switchId + ": controller started!")

    # Instructs the switch to resent a packet that was sent to the controller.
    # "packet_in" is the OpenFlow pabket that was sent to the controller because of a table-miss
    def resendPacket(self, packetIn, outPort):
        msg = of.ofp_packet_out()
        msg.data = packet_in

        action = of.ofp_action_output(port = outPort)
        msg.actions.append(action)

        self.connection.send(msg)

    def handlePacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packetIn = event.ofp
        self.actLikeSwitch(packet, packetIn)

    def actLikeSwitch(self, packet, packetIn):
        pass

    def actLikeL2Learning(self, packet, packetIn):
        pass

    def packetIsArp(self, packet):
        return (packet.find('arp') is not None)

    def packetIsArpRequest (self, packet):
        return self.packetIsArp(packet) and packet.find('arp').opcode == 1

    # Assuming that the packet is guaranteed to be an ARP Request
    def handleARPRequest(self, packet, packetIn):
        if not packetIsArpRequest(packet):
            log.error("ERROR: Called handleArp on a non-arp packet!!")
            return
        arpPacket = packet.find('arp')
        lastMile = self.getLastMileAndUpdateGlobalARPEntry(arpPacket)

    def getLastMileAndUpdateGlobalARPEntry(self, arpPacket):
        requestorMAC = arpPacket.hwsrc
        requestedIP = arpPacket.protodst
        if not globalARPEntry.macExists(requestorMAC):
            globalARPEntry.createNewEntryForMAC(requestorMAC)
            globalARPEntry.addUniqueIPForMAC(requestorMAC, requestedIP)
            lastMile = True
        elif not globalARPEntry.ipIsKnownForMAC(requestorMAC, requestedIP):
            globalARPEntry.addUniqueIPForMAC(requestorMAC, requesterIP)
            lastMile = True
        else:
            lastMile = False
        return lastMile

# Starts the component
def launch():
    
    def startSwitch(event):
        SwitchOFController(event.connection)
    core.openflow.addListenerByName("ConnectionUp", startSwitch)
