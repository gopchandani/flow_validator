import os
import sys
__author__ = 'Shane Rogers'

num_cons = 0
ports = []

class ControllerMan():

    def __init__(self, num_cons):
    	print num_cons
    	for i in range (num_cons):
    		port = 6630 + i
    		os.system('sudo docker run -d -t -i -p=port:6633 controller distribution-karaf-0.2.1-Helium-SR1/bin/karaf')
        	os.system('sudo docker stop $(sudo docker ps -q)')
        	ports.append(port)
        	#need array of container ids too

    def get_next(self):
        print 'here '
        #this will unpause the next container and return a port number
        #it will also rmove the container ID from the array
        #will eventually start a new container and add it to the back of array

def main():
	num_cons = int(sys.argv[1])
	print num_cons
	cm = ControllerMan(num_cons)
	#cm.get_next()
    
if __name__ == "__main__":
    main()