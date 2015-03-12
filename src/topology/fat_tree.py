__author__ = 'Shane Rogers'

from mininet.topo import Topo
from math import ceil

class FatTree(Topo):

    def __init__(self, num_switches=3, num_hosts_per_switch=1):

        Topo.__init__(self)

        self.num_bottom_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.num_middle_switches = int(ceil(num_switches*1.0/2))

        max_bottoms_per_middle = 2 * ((self.num_bottom_switches
                                       + (-self.num_bottom_switches%self.num_middle_switches))/(self.num_middle_switches - 1)) + 1
        first_open_index = 0

        switch_name_index = 1

        print "Maximum bottom switches per middle switch is " + str(max_bottoms_per_middle)

        top_switches = []
        middle_switches = []
        bottom_switches = []

        bottoms_attached_to_middles = [0] * self.num_middle_switches # max = bottoms_per_middle

        #  Add switches and hosts under them
        for k in range(self.num_bottom_switches):
            curr_bottom_switch = self.addSwitch("s" + str(switch_name_index), protocols="OpenFlow13")
            bottom_switches.append(curr_bottom_switch)

            for l in range(self.num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(switch_name_index) + str(l+1))
                self.addLink(curr_bottom_switch, curr_switch_host)

            switch_name_index += 1

        for j in range(self.num_middle_switches):
            curr_middle_switch = self.addSwitch("s" + str(switch_name_index), protocols="OpenFlow13")
            switch_name_index += 1
            middle_switches.append(curr_middle_switch)


        for i in range(2):
            curr_top_switch = self.addSwitch("s" + str(switch_name_index), protocols="OpenFlow13")
            top_switches.append(curr_top_switch)
            switch_name_index += 1

            for m in range(self.num_middle_switches):
                self.addLink(top_switches[i], middle_switches[m])

        for n in range(self.num_bottom_switches):
            self.addLink(bottom_switches[n], middle_switches[first_open_index])

            print "Attaching bottom switch: " + bottom_switches[n] + \
                  " to middle switch: " + middle_switches[first_open_index]

            self.addLink(bottom_switches[n], middle_switches[(first_open_index + 1)])

            print "Attaching bottom switch: " + bottom_switches[n] + \
                  " to middle switch: " + middle_switches[first_open_index + 1]

            bottoms_attached_to_middles[first_open_index] = bottoms_attached_to_middles[first_open_index] + 1
            bottoms_attached_to_middles[first_open_index + 1] = bottoms_attached_to_middles[first_open_index + 1] + 1

            if bottoms_attached_to_middles[first_open_index] >= max_bottoms_per_middle:
                first_open_index += 1
            if bottoms_attached_to_middles[first_open_index] >= max_bottoms_per_middle:
                first_open_index += 1

topos = {"fattreetopo": (lambda: FatTree())}
