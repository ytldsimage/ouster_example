cmake_minimum_required(VERSION 3.1.0)

project(simple_example)

set(CMAKE_CXX_STANDARD 11)

find_package(Eigen3 REQUIRED)

if(WIN32)
  # Coming soon...
elseif(APPLE)
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(jsoncpp REQUIRED jsoncpp)
else()
  find_package(jsoncpp REQUIRED)
endif()

  include_directories(
  include
  ${EIGEN3_INCLUDE_DIR}
  ${jsoncpp_INCLUDE_DIRS}
  )

link_directories(
  lib
  )

add_executable(example
  simple.cpp
  )

target_link_libraries(example
  ouster_client
  ouster_client_version
  ${json_LIBRARIES}
  )
