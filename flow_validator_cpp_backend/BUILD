
load("@build_stack_rules_proto//cpp:cpp_grpc_library.bzl", "cpp_grpc_library")
#load("@build_stack_rules_proto//cpp:cpp_grpc_compile.bzl", "cpp_grpc_compile")

proto_library(
    name = "flow_validator_proto",
    srcs = ["proto/flow_validator.proto"],
    deps = [],
    
)

cpp_grpc_library(
    name = "flow_validator_proto_cpp",
    deps = [":flow_validator_proto"],
    visibility = ["//visibility:public"],
    
)

cc_library(
    name="flow_validator_lib",
    hdrs=[
        "src/flow_validator/of_constants.h",
        "src/flow_validator/flow_validator.h",
        "src/flow_validator/rule.h",
        "src/flow_validator/analysis_graph_node.h",
        "src/flow_validator/analysis_graph.h"
        ],
    srcs=[
        "src/flow_validator/flow_validator.cc",
        "src/flow_validator/rule.cc",
        "src/flow_validator/analysis_graph_node.cc",
        "src/flow_validator/analysis_graph.cc"
        ],

    deps = ["@boost//:algorithm",
            "@boost//:lexical_cast",
            "@boost//:program_options",
            "@boost//:exception",
            ":flow_validator_proto_cpp"],
    
    copts = ["-fpermissive -Wno-reorder"],
    visibility = ["//visibility:public"],
    alwayslink = True,
)
cc_binary (
    name="flow_validator_cpp_backend",
    srcs=[
        "src/main.cc",
    ],
    deps = [":flow_validator_lib"]
)


# cc_test(
#     name = "datatype_test",
#     srcs = ["src/pc_emulator/tests/datatype_tests/datatype_test.cc"],
#     copts = ["-Iexternal/gtest/include -fpermissive -Wno-reorder"],
#     deps = [":pc_emulator_lib",
#            "@gtest//:main"],
#     linkstatic = 1,
# )

# cc_test(
#     name = "variable_test",
#     srcs = ["src/pc_emulator/tests/variable_tests/variable_test.cc"],
#     copts = ["-Iexternal/gtest/include -fpermissive -Wno-reorder"],
#     deps = [":pc_emulator_lib",
#            "@gtest//:main"],
#     linkstatic = 1,
# )