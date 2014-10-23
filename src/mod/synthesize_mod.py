__author__ = 'Rakesh Kumar'

from model.model import Model


class SynthesizeMod():

    def __init__(self):
        self.model = Model()


    def _populate_switch(self):
        pass

    def trigger(self):

        #  First figure out what switches exist in the current topology
        #  Each switch needs the same thing (logically) inside it

        for n in self.model.graph.nodes():

            if self.model.graph.node[n]["node_type"] == "switch":
                print "We are in business here at n:", self.model.graph.node[n]["node_type"], n



def main():
    sm = SynthesizeMod()

    sm.trigger()

if __name__ == "__main__":
    main()

