# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

log = core.getLogger()

controller_macToIps = {}


class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}
    self.arp_cache = {}

  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)

  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """
    log.debug("Controller received a packet from switch:")
    log.debug("MAC src: " + str(packet.src))
    log.debug("MAC dst: " + str(packet.dst))
    
    arp_packet = packet.find('arp')
    if arp_packet is not None and arp_packet.opcode == 1:
        log.debug("Type is ARP REQUEST!")
        # Find out whether this is the last mile or not
        if arp_packet.hwsrc not in controller_macToIps:
            log.debug("MAC Address " + str(arp_packet.hwsrc) + " is new on controller_macToIps")
            last_mile = True
            controller_macToIps[arp_packet.hwsrc] = [arp_packet.protodst]
        elif arp_packet.protodst not in controller_macToIps[arp_packet.hwsrc]:
            log.debug("MAC Address " + str(arp_packet.hwsrc) + "isn't new, but ARP request to IP " + str(arp_packet.protodst) + " is.")
            last_mile = True
            controller_macToIps[arp_packet.hwsrc].append(arp_packet.protodst)
        else:
            log.debug("MAC Address " + str(arp_packet.hwsrc) + " and IP " + str(arp_packet.protodst) + " already existed.")
            last_mile = False

        if arp_packet.hwsrc not in self.arp_cache:
            cache_parameters = [[arp_packet.protodst], [packet_in.in_port], last_mile]
            self.arp_cache[arp_packet.hwsrc] = cache_parameters
            self.resend_packet(packet_in, of.OFPP_ALL)
        elif arp_packet.protodst not in self.arp_cache[arp_packet.hwsrc][0]:
            self.arp_cache[arp_packet.hwsrc][0].append(arp_packet.protodst)
            if packet_in.in_port not in self.arp_cache[arp_packet.hwsrc][1]:
                self.arp_cache[arp_packet.hwsrc][1].append(packet_in.in_port)
            self.resend_packet(packet_in, of.OFPP_ALL)
            # TODO last_mile is always the same for a given Host and Switch. I can keep it the same, can't I?
        else:
            if not last_mile:
                if packet_in.in_port not in self.arp_cache[arp_packet.hwsrc][1]:
                    self.arp_cache[arp_packet.hwsrc][1].append(packet_in.in_port)
        return
        
    if packet.src not in self.mac_to_port:
        log.debug("Learning source MAC address...")
        self.mac_to_port[packet.src] = packet_in.in_port
        log.debug("Installing flow...")
        log.debug("MAC dst: " + str(packet.src) + ", output port: " + str(packet_in.in_port))

    if packet.dst in self.mac_to_port:
        log.debug("Destination already learned!")
        log.debug("Sending packet to port " + str(self.mac_to_port[packet.dst]))
        self.resend_packet(packet_in, self.mac_to_port[packet.dst])
        log.debug("Installing flow...")
        log.debug("MAC dst: " + str(packet.dst))
        log.debug("Output port: " + str(self.mac_to_port[packet.dst]))

        msg = of.ofp_flow_mod()
        # Set fields to match received packet
        msg.match = of.ofp_match()
        msg.match.dl_dst = packet.dst
        #< Add an output action, and send -- similar to resend_packet() >
        action = of.ofp_action_output(port = self.mac_to_port[packet.dst])
        msg.actions.append(action)
        self.connection.send(msg)
    else:
        # Flood the packet out everything but the input port
        # This part looks familiar, right?
        log.debug("Could not find known destination. Flooding packet...")
        self.resend_packet(packet_in, of.OFPP_ALL)

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    #self.act_like_hub(packet, packet_in)
    self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
