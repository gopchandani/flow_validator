__author__ = 'Rakesh Kumar'

from mininet.topo import Topo


class MicrogridsTopo(Topo):
    def __init__(self, params):

        Topo.__init__(self)

        self.params = params
        self.total_switches = self.params["num_switches"]

    def __str__(self):
        params_str = ''
        for k, v in self.params.items():
            params_str += "_" + str(k) + "_" + str(v)
        return self.__class__.__name__ + params_str
