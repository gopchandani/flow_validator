clear
echo "Going to invoke" $1

if [ "$1" == "line" ]
  then
    sudo mn -c; sudo mn --custom line_topo.py --topo linetopo --controller remote,ip=127.0.0.1,port=6633 --switch ovsk,protocols=OpenFlow13
elif [ "$1" == "ring" ]
  then
    sudo mn -c; sudo mn --custom ring_topo.py --topo ringtopo --controller remote,ip=127.0.0.1,port=6633 --switch ovsk,protocols=OpenFlow13
elif [ "$1" == "fat_tree" ]
  then
    sudo mn -c; sudo mn --custom fat_tree.py --topo fattreetopo --controller remote,ip=127.0.0.1,port=6633 --switch ovsk,protocols=OpenFlow13
fi

