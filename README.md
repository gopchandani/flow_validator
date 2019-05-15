### What does this tool do? ###
The set of tools in this repository serve a common purpose: the analysis of Software Defined Networks with a particular focus on those using the fast-failover mechanism that is part of the recent OpenFlow standards. There are two parts of this repository:

* The python frontend is used to synthesize various network configuration and specify the type and details of analysis that is to be performed. This code is located under the ```src``` folder.
* The C++ backend (SDNSim) simulates the network and allows rapid, parallel analysis. This code is located under the ```sdnsim``` folder.


### How do I setup? ###

* This project been tested with Ubuntu 16.04 LTS (ISO available here: http://releases.ubuntu.com/16.04/). 
* If you want to install it on a VM, make sure you have at least 4 GB RAM and 2 CPU cores assigned to the VM. You can get VirtualBox here: https://www.virtualbox.org/wiki/Downloads)
* After the Ubuntu installation, clone this repo in your home folder:\
```pushd ~/```\
```git clone https://github.com/gopchandani/flow_validator.git```
* Make sure you have openvswitch 2.3.0 or higher. The version can be checked using:\
```ovs-ofctl --version```
* Install mininet version 2.2 from the source by following instructions here: http://mininet.org/download/
* Get RYU version 4.3 from their repo at: http://osrg.github.io/ryu/
* Install Ubuntu Python package dependencies:\
``` sudo apt install python-pip python-scipy python-numpy python-matplotlib ```
* Install pip packages:\
``` sudo pip install sortedcontainers networkx netaddr httplib2 ```
* Setup PYTHONPATH to src folder by adding following line to your ~/.bashrc: \
```export PYTHONPATH=${PYTHONPATH}:/home/flow/flow_validator/src/```
* Allow PYTHONPATH to be retained by sudo by modifying sudoers configuration using visudo and adding the following line:\
```sudo visudo```\
```Defaults env_keep += "PYTHONPATH"```
* Install bazel version 0.22, here: https://docs.bazel.build/versions/master/install.html
* Generate the proto files for the python code\
```pushd ~/flow_validator/src/rpc/```\
```sudo python -m grpc_tools.protoc -I../../sdnsim/proto --python_out=. --grpc_python_out=. ../../sdnsim/proto/sdnsim.proto```

### How do I try some examples? ###
* First the C++ backend (i.e. SDNSim) needs to be started. In order to do so, follow these steps:\
```cd ~/flow_validator/sdnsim```\
```bazel run :sdnsim```
* Try the Python frontend Playground module. In order to run it, follow these steps:\
```cd ~/flow_validator/src```\
```sudo mn -c; sudo killall ryu-manager```\
```sudo python experiments/playground.py```
* Try a more complex network with a random topology:\
```cd ~/flow_validator/src```\
```sudo mn -c; sudo killall ryu-manager```\
```sudo python experiments/wsc_experiment.py --input_file experiments/failovers_64_switch.json --output_file experiments/output.json```
