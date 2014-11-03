__author__ = 'Shane Rogers'

from mininet.topo import Topo

class FatTree(Topo):

    def __init__(self):

        Topo.__init__(self)

        num_bottom_switches = int(raw_input("Enter number of bottom switches:"))
        num_hosts_per_switch = int(raw_input("Enter # of hosts/switch:"))
        num_middle_switches = int(raw_input("Enter number of middle switches:"))

        max_bottoms_per_middle = 2 * ((num_bottom_switches
                                       + (-num_bottom_switches%num_middle_switches))/(num_middle_switches - 1)) + 1
        first_open_index = 0

        print "Maximum bottom switches per middle switch is " + str(max_bottoms_per_middle)

        top_switches = []
        middle_switches = []
        bottom_switches = []

        bottoms_attached_to_middles = [0] * num_middle_switches # max = bottoms_per_middle

        #  Add switches and hosts under them

        for j in range(num_middle_switches):
            curr_middle_switch = self.addSwitch("ms" + str(j+1))
            middle_switches.append(curr_middle_switch)

        for k in range(num_bottom_switches):
            curr_bottom_switch = self.addSwitch("bs" + str(k+1))
            bottom_switches.append(curr_bottom_switch)

            for l in range(num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(k+1) + str(l+1))
                self.addLink(curr_bottom_switch, curr_switch_host)

        for i in range(2):
            curr_top_switch = self.addSwitch("ts" + str(i+1))
            top_switches.append(curr_top_switch)

            for m in range(num_middle_switches):
                self.addLink(top_switches[i], middle_switches[m])

        for n in range(num_bottom_switches):
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
