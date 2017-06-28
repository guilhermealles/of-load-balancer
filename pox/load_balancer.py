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
        self.switchID = str(connection)
        self.learningTable = LearningTable()
        connection.addListeners(self)
        log.debug("Switch ID " + self.switchID + ": controller started!")

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
            log.warning("Switch ID "+self.switchID+" >>> Ignoring incomplete packet")
            return

        packetIn = event.ofp
        if self.packetIsARP(packet):
            self.handleARPPacket(packet, packetIn)
        else:
            log.debug("Switch ID "+self.switchID+" >>> received regular packet")
            self.logLearningTable()
            self.actLikeL2Learning(packet, packetIn)

    def learnDataFromPacket(self, packet, packetIn, lastMile = False):
        sourceMAC = packet.src
        if self.learningTable.macIsKnown(sourceMAC):
            self.learningTable.appendReachableThroughPort(sourceMAC, packetIn.in_port)
            if lastMile == False and self.learningTable.isLastMile:
                lastMile = True
            self.learningTable.setLastMile(sourceMAC, lastMile)
        else:
            self.learningTable.createNewEntryWithProperties(sourceMAC, packetIn.in_port, lastMile)

    def actLikeL2Learning(self, packet, packetIn):
        destinationMAC = packet.dst
        if self.learningTable.macIsKnown(destinationMAC):
            outPort = self.learningTable.getAnyPortToReachHost(destinationMAC)
            log.info("Switch ID "+self.switchID+" >>> Sending packet to MAC " + str(destinationMAC) + " through port " + str(outPort))
            self.resendPacket(packetIn, outPort)
        else:
            log.error("Switch ID "+self.switchID+" >>> ERROR: Trying to send a packet to an unknown host")

    def packetIsARP(self, packet):
        return (packet.find('arp') is not None)

    def packetIsARPRequest (self, arpPacket):
        return arpPacket.opcode == 1

    def handleARPPacket(self, packet, packetIn):
        arpPacket = packet.find('arp')
        if self.packetIsARPRequest(arpPacket):
            log.debug("Switch ID "+self.switchID+" >>> received ARP Request")
            self.handleARPRequest(packet, packetIn)
        else:
            log.debug("Switch ID "+self.switchID+" >>> received ARP Reply")
            self.handleARPReply(packet, packetIn)

    def handleARPReply(self, packet, packetIn):
        arpPacket = packet.find('arp')
        lastMile = globalARPEntry.isNewARPFlow(arpPacket)
        log.debug("Switch ID "+self.switchID+" >>> ARP Reply with lastMile = "+str(lastMile))
        globalARPEntry.update(arpPacket)
        self.learnDataFromPacket(packet, packetIn, lastMile)
        outPort = self.learningTable.getAnyPortToReachHost(packet.dst)
        log.debug("Switch ID "+self.switchID+" >>> Sending ARP Reply to " + str(packet.dst) + " on port " + str(outPort))
        self.resendPacket(packetIn, outPort)

    def handleARPRequest(self, packet, packetIn):
        arpPacket = packet.find('arp')
        lastMile = globalARPEntry.isNewARPFlow(arpPacket)
        log.debug("Switch ID "+self.switchID+" >>> ARP Request with lastMile = "+str(lastMile))
        globalARPEntry.update(arpPacket)
        sourceMAC = packet.src
        destinationIP = arpPacket.protodst
        log.debug("Switch ID "+self.switchID+" >>> MAC "+str(sourceMAC)+" asking who has IP "+str(destinationIP))
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
            if self.learningTable.macIsKnown(requestorMAC):
                lastMile = self.learningTable.isLastMile(requestorMAC)
            else:
                lastMile = False
        return lastMile

    def logLearningTable(self):
        log.debug("Switch ID "+self.switchID+" >>> <<<<<LEARNING TABLE BEGIN>>>>>"+str(self.switchID))
        for recordedMAC in self.learningTable.macMap:
            log.debug("==== ["+str(recordedMAC)+"] ====")
            #log.debug(">>>> Known IPs: "+str(self.learningTable.macMap[recordedMAC].getKnownIPsList()))
            log.debug(">>>> Host reachable through ports: "+str([str(port) for port in self.learningTable.macMap[recordedMAC].reachableThroughPorts]))
            log.debug(">>>> Last mile: "+str(self.learningTable.macMap[recordedMAC].lastMile))
        log.debug("<<<<<LEARNING TABLE END>>>>>")

# Starts the component
def launch():

    def startSwitch(event):
        SwitchOFController(event.connection)
    core.openflow.addListenerByName("ConnectionUp", startSwitch)
