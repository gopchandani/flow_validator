echo "--- s1"
ovs-ofctl dump-flows s1 -O OpenFlow13
ovs-ofctl dump-groups s1 -O OpenFlow13
echo "--- s2"
ovs-ofctl dump-flows s2 -O OpenFlow13
ovs-ofctl dump-groups s2 -O OpenFlow13
echo "--- s3"
ovs-ofctl dump-flows s3 -O OpenFlow13
ovs-ofctl dump-groups s3 -O OpenFlow13
echo "--- s4"
ovs-ofctl dump-flows s4 -O OpenFlow13
ovs-ofctl dump-groups s4 -O OpenFlow13
echo "--- s5"
ovs-ofctl dump-flows s5 -O OpenFlow13
ovs-ofctl dump-groups s5 -O OpenFlow13
echo "--- s6"
ovs-ofctl dump-flows s6 -O OpenFlow13
ovs-ofctl dump-groups s6 -O OpenFlow13

