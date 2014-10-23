__author__ = 'Shane Rogers'

from mininet.topo import Topo

class FatTree(Topo):

    def __init__(self):

        Topo.__init__(self)

        num_bottom_switches = int(raw_input("Enter number of bottom switches:"))
        num_hosts_per_switch = int(raw_input("Enter # of hosts/switch:"))
        num_middle_switches = int(raw_input("Enter number of middle switches:"))
        max_bottoms_per_middle = 2 * ((num_bottom_switches +(-num_bottom_switches%num_middle_switches))/(num_middle_switches - 1)) + 1
        first_open_index = 0 #to keep track of where to start.
        print "Maximum bottom switches per middle switch is " + str(max_bottoms_per_middle)

        top_switches = []
        middle_switches = []
        bottom_switches = []
        #full_middle_switches = []  #boolean array: if fms[0] == 1, ms[0] is full
        bottoms_attached_to_middles = [0] * num_middle_switches # max = bottoms_per_middle

        #  Add switches and hosts under them


        for j in range(num_middle_switches):
            curr_middle_switch = self.addSwitch("ms" + str(j))
            middle_switches.append(curr_middle_switch)

        for k in range(num_bottom_switches):
            curr_bottom_switch = self.addSwitch("bs" + str(k))
            bottom_switches.append(curr_bottom_switch)

            for l in range(num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(k) + str(l))
                self.addLink(curr_bottom_switch, curr_switch_host)

        for i in range(2):
            curr_top_switch = self.addSwitch("ts" + str(i))
            top_switches.append(curr_top_switch)

            for m in range(num_middle_switches):
                self.addLink(top_switches[i], middle_switches[m])

        for n in range(num_bottom_switches):
            self.addLink(bottom_switches[n], middle_switches[first_open_index])
            print "Attaching bottom switch " + str(n) + " to middle switch " + str(first_open_index)
            self.addLink(bottom_switches[n], middle_switches[(first_open_index + 1)])
            print "Attaching bottom switch " + str(n) + " to middle switch " + str(first_open_index + 1)
            bottoms_attached_to_middles[first_open_index] = bottoms_attached_to_middles[first_open_index] + 1
            bottoms_attached_to_middles[first_open_index + 1] = bottoms_attached_to_middles[first_open_index + 1] + 1
            if bottoms_attached_to_middles[first_open_index] >= max_bottoms_per_middle:
                first_open_index += 1
            if bottoms_attached_to_middles[first_open_index] >= max_bottoms_per_middle:
                first_open_index += 1

        #  Add links between switches
            #if num_switches > 1:
             #   for i in range(num_switches - 1):
              #      print switches[i], type(switches[i])
               #     self.addLink(switches[i], switches[i+1])

                #  Form a ring only when there are more than two switches
                #if num_switches > 2:
                 #   self.addLink(switches[0], switches[-1])


topos = {"fattreetopo": (lambda: FatTree())}
