ovs-ofctl dump-flows s0 -O OpenFlow13
ovs-ofctl dump-flows s1 -O OpenFlow13
ovs-ofctl dump-flows s2 -O OpenFlow13
ovs-ofctl dump-flows s3 -O OpenFlow13


ovs-ofctl del-flows s0 -O OpenFlow13
ovs-ofctl del-flows s1 -O OpenFlow13
ovs-ofctl del-flows s2 -O OpenFlow13
ovs-ofctl del-flows s3 -O OpenFlow13
