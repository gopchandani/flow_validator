__author__ = 'Rakesh Kumar'



class Switch():

    def __init__(self, sw_id):

        self.switch_id = sw_id
        self.flow_tables = None
        self.group_table = None
        self.ports = None

