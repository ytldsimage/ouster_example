#!/bin/bash
set -x

#OSdriver @~/myOSROS
cd ~ && sudo dpkg --configure -a &&  sudo apt update -y &&  sudo apt upgrade -y && sudo apt autoremove -y && sudo apt --fix-broken -y install && sudo apt update --fix-missing && sudo apt -y install unzip   git   cmake build-essential libglfw3-dev libglew-dev libeigen3-dev libjsoncpp-dev libtclap-dev && git clone https://github.com/ytldsimage/ouster_example && source /opt/ros/*/setup.bash && cd ~ && sudo mkdir -p myOSROS/src && cd myOSROS && ln -s ~/ouster_example ./src/ && catkin_make -DCMAKE_BUILD_TYPE=Release  