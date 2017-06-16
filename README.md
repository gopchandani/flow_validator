### How do I get set up? ###

* This project been tested to run fine on Ubuntu 14.04 and 16.04 LTS. 
* Get RYU version 4.0 from their repo at: http://osrg.github.io/ryu/
* Ensure that openvswitch version is at least 2.3.0
* If you don't have pip installed, then install the python package manager. (Ubuntu package: python-pip)
* sudo apt-get install python-oslo.config
* sudo pip install sortedcontainers
* sudo pip install networkx
* sudo pip install netaddr
* sudo pip install httplib2
* Install mininet version 2.2 by following instructions here: http://mininet.org/download/
* sudo apt-get install python-scipy
* sudo apt-get install python-numpy
* sudo apt-get install python-matplotlib
* Setup PYTHONPATH to src folder by adding following to ~/.bashrc: export PYTHONPATH=${PYTHONPATH}:/home/flow/flow_validator/src/ and allow PYTHONPATH to be retained by sudo by adding following to /etc/sudoers: Defaults env_keep += "PYTHONPATH"
* For running, go under src/experiments and run: sudo python experiment_module_name.py
