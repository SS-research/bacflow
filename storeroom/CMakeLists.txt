cmake_minimum_required(VERSION 3.12)
project(widmark_bindings)

set(CMAKE_CXX_STANDARD 14)

find_package(pybind11 REQUIRED)

add_library(widmark_bindings MODULE coefficient.pybind11.cpp)

target_link_libraries(widmark_bindings PRIVATE pybind11::module)
