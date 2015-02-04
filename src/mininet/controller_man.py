import os
import sys
import subprocess
__author__ = 'Shane Rogers'

num_cons = 0
ports = []

class ControllerMan():

    def __init__(self, num_cons):

    	for i in range (num_cons):
    		new_port = int(6630 + i)
    		command = 'sudo docker run -d -t -i -p=%s:6633 controller distribution-karaf-0.2.1-Helium-SR1/bin/karaf'%str(new_port) 
    		os.system(command)
        	subprocess.call("sudo docker ps -q", shell=True)
        	ports.append(new_port)
        	#print p
        	#need array of container ids too



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
	cm.kill_all()
	#cm.get_next()
    
if __name__ == "__main__":
    main()



