import os
import sys
import subprocess
__author__ = 'Shane Rogers'

num_cons = 0
ports = []
data = []

class ControllerMan():

#    def get_container_ids(self):
#   		data.append(sys.stdin.readline())
#   		subprocess.call("sudo docker ps -q", shell=True)
#   		sys.stdin.close() ##need something here to tell readlines() to stop. 

    def __init__(self, num_cons):
    	for i in range (num_cons):
    		new_port = int(6630 + i)
        	ports.append(new_port)

    		start_command = 'sudo docker run -d -t -i -p=%s:6633 controller distribution-karaf-0.2.1-Helium-SR1/bin/karaf'%str(new_port) 

    		os.system(start_command)
    		proc = subprocess.Popen(['sudo', 'docker', 'ps', '-q'], stdout=subprocess.PIPE)
    		while True:
    			this_id = proc.stdout.readline()
    			if this_id != '':
    				print this_id
    				data.append(this_id)
		    		stop_command = 'sudo docker stop %s'%str(this_id)
    				os.system(stop_command)
    			else:
    				break


#        self.get_container_ids()
        
        


    def get_next(self):
        print 'here '
        #this will unpause the next container and return a port number
        #it will also rmove the container ID from the array
        #will eventually start a new container and add it to the back of array

    def kill_all(self):
    	os.system("docker stop $(docker ps -a -q)")
    	os.system("docker rm $(docker ps -a -q)")

def main():
	num_cons = int(sys.argv[1])
	cm = ControllerMan(num_cons)

	for i in range (num_cons):
		print "Container with port number",
		print ports[i],
		print "has container id",
		print data[i]
	#cm.kill_all()
	#cm.get_next()
    
if __name__ == "__main__":
    main()



