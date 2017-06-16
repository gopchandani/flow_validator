### How do I get set up? ###

* This project been tested to run fine on Ubuntu 14.04 and 16.04 LTS. 
* Install openvswitch 2.3.0 or higher.
* Install mininet version 2.2 by following instructions here: http://mininet.org/download/
* Get RYU version 4.0 from their repo at: http://osrg.github.io/ryu/
* If you don't have pip installed, then install the python package manager. (Ubuntu package: python-pip)
* sudo pip install sortedcontainers
* sudo pip install networkx
* sudo pip install netaddr
* sudo pip install httplib2
* sudo apt-get install python-scipy
* sudo apt-get install python-numpy
* sudo apt-get install python-matplotlib
* Setup PYTHONPATH to src folder by adding following to ~/.bashrc: export PYTHONPATH=${PYTHONPATH}:/home/flow/flow_validator/src/ 
* Allow PYTHONPATH to be retained by sudo by modifying sudoers configuration using visudo: Defaults env_keep += "PYTHONPATH"
* Take a look at the simple example of validation in the file: flow_validator/src/experiments/playground.py
* To run cd into flow_validator/src and run: sudo python experiments/playground.py
