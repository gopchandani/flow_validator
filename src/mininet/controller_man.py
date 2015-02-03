import os
import sys
__author__ = 'Shane Rogers'

num_cons = 0

class ControllerMan():

    def __init__(self, num_cons):
    	print num_cons
    	for i in range (num_cons):
    		port = 6630 + i
    		os.system('sudo docker run -d -t -i -p=port:6633 controller distribution-karaf-0.2.1-Helium-SR1/bin/karaf')
        	os.system('sudo docker stop $(sudo docker ps -q)')
        	return port

    def get_next(self):
        print 'here '

def main():
	num_cons = sys.argv[1]
	print num_cons
	#cm = ControllerMan(num_cons)
	#cm.get_next()
    
if __name__ == "__main__":
    main()