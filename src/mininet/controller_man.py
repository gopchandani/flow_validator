__author__ = 'Shane Rogers'


class ControllerMan(num_cons):

    def __init__(self, num_cons):
    	for i in range num_cons:
    		port = 6630 + i
    		sudo docker run -d -t -i -p=port:6633 controller distribution-karaf-0.2.1-Helium-SR1/bin/karaf
        	sudo docker stop $(sudo docker ps -q)
        	return port

    def get_next(self):
        print 'here '

def main():
    cm = ControllerMan(argv)
    cm.get_next()
    
if __name__ == "__main__":
    main()