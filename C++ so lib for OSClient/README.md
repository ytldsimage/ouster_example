# Simple Ouster Example

This is a simple application which shows how to use the ouster_client API to
retrieve data from the sensor and write it to a PLY file. The file may be viewed
in CloudCompare.

* http://cloudcompare.org/

# Install

* Using Ubuntu: `sudo apt-get install libeigen3-dev libjsoncpp-dev`

# Build

* `mkdir build`
* `cd build`
* `cmake .. -DCMAKE_BUILD_TYPE=Release`
* `cmake --build .`

# Run

Collect 5 frames of LIDAR data:

` ./example os1-122009000183.Local 10.10.10.10 output.ply 5`

where:
* device hostname: os1-122009000183.local
* local IP adddress: 10.10.10.10
* output file: output.ply
* frame count: 5
