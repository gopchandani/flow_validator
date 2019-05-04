
load("@build_stack_rules_proto//cpp:cpp_grpc_library.bzl", "cpp_grpc_library")
#load("@build_stack_rules_proto//cpp:cpp_grpc_compile.bzl", "cpp_grpc_compile")

proto_library(
    name = "sdnsim_proto",
    srcs = ["proto/sdnsim.proto"],
    deps = [],
    
)

cpp_grpc_library(
    name = "sdnsim_proto_cpp",
    deps = [":sdnsim_proto"],
    visibility = ["//visibility:public"],
    
)

cc_library(
    name="sdnsim_lib",
    hdrs=[
        "src/sdnsim/thread_pool.h",
        "src/sdnsim/of_constants.h",
        "src/sdnsim/common_types.h",
        "src/sdnsim/sdnsim.h",
        "src/sdnsim/rule_effect.h",
        "src/sdnsim/group_effect.h",
        "src/sdnsim/rule.h",
        "src/sdnsim/analysis_graph_node.h",
        "src/sdnsim/analysis_graph.h"
        ],
    srcs=[
        "src/sdnsim/sdnsim.cc",
        "src/sdnsim/rule_effect.cc",
        "src/sdnsim/group_effect.cc",
        "src/sdnsim/rule.cc",
        "src/sdnsim/analysis_graph_node.cc",
        "src/sdnsim/analysis_graph.cc"
        ],

    # deps = ["@boost//:algorithm",
    #         "@boost//:lexical_cast",
    #         "@boost//:program_options",
    #         "@boost//:exception",
    #         ":sdnsim_proto_cpp"],

    deps = [":sdnsim_proto_cpp"],
    copts = ["-fpermissive -Wno-reorder"],
    visibility = ["//visibility:public"],
    alwayslink = True,
)
cc_binary (
    name="sdnsim",
    srcs=[
        "src/main.cc",
    ],
    deps = [":sdnsim_lib"]
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