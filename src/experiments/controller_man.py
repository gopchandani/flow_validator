import subprocess


class ControllerMan(object):
    def __init__(self,  controller):
        self.controller = controller

        if controller == "ryu":
            self.ryu_proc = None

    def get_next_ryu(self):

        ryu_cmd = ["ryu-manager", "--observe-links", "ryu.app.ofctl_rest", "ryu.app.rest_topology"]
        self.ryu_proc = subprocess.Popen(ryu_cmd, stdout=subprocess.PIPE)
        return 6633

    def start_controller(self):
        if self.controller == "odl":
            raise NotImplemented
        elif self.controller == "ryu":
            return self.get_next_ryu()

    def stop_controller(self):

        if self.controller == "ryu":
            self.ryu_proc.kill()
            subprocess.Popen.wait(self.ryu_proc)
        else:
            raise NotImplemented


