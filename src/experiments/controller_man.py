import os
import sys
import subprocess
import time
__author__ = 'Shane Rogers'

# controllerMan will spin up the number of containers you pass as a parameter.
#  command line usage: python controller_man X   where X is an integer.
#  cm = ControllerMan(X) as an import function
#  you can then retrieve one of the containers with 
#  cm.get_next(), which returns the port the container will be listening on.
#  You can kill all containers by running cm.kill_all()
#  WARNING
#  This function does not currently sanitize user input in any way, so if you
#  give it a funny value for the number of containers or try to pull more containers
#  than you spin up, it will break.  Send questions or comments to shane@shanerogers.info


class ControllerMan():
    def __init__(self, num_cons, verbose=False):
        self.num_cons = num_cons
        self.data = []
        self.ports = []
        self.a_container_is_running = False
        self.verbose = False

        print "Initializing, number of containers:", self.num_cons

        for i in range(self.num_cons):
            new_port = int(6630 + i)
            self.ports.append(new_port)

            start_command = 'sudo docker run -d -t -i -p=%s:6633 -p=8181:8181 opendaylight distribution-karaf-0.2.1-Helium-SR1/bin/karaf' % str(
                new_port)

            os.system(start_command)
            proc = subprocess.Popen(['sudo', 'docker', 'ps', '-q'], stdout=subprocess.PIPE)
            while True:
                this_id = proc.stdout.readline()
                if this_id != '':

                    if verbose:
                        print this_id

                    self.data.append(this_id)
                    stop_command = 'sudo docker stop %s' % str(this_id)
                    os.system(stop_command)
                else:
                    break

    def start_container(self):
        self.a_container_is_running = True
        next_container = str(self.data[0])
        os.system("docker start %s" % next_container)
        return self.ports[0]

    def stop_container(self):
        this_id = self.data.pop(0)
        self.ports.pop(0)
        os.system("docker stop --time=30 %s" % str(this_id))
        os.system("docker rm %s" % str(this_id))

    def get_next(self):
        this_port = 0

        if self.a_container_is_running:
            self.stop_container()
            this_port = self.start_container()
            return this_port
        else:
            this_port = self.start_container()
            return this_port

    def kill_all(self):

        print "Killing all containers..."

        os.system("docker stop --time=30 $(docker ps -a -q)")
        os.system("docker rm $(docker ps -a -q)")

    def __del__(self):
        print "Docker cleanup..."
        self.kill_all()

def main():

    num_cons = int(sys.argv[1])
    cm = ControllerMan(num_cons)

    for i in range(num_cons):
        print "Container with port number",
        print cm.ports[i],
        print "has container id",
        print cm.data[i]

    new_port = cm.get_next()
    print "This thing says there is a controller with port %s open!" % str(new_port)

if __name__ == "__main__":
    main()


