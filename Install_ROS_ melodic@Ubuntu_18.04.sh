#!/bin/bash
set -x


#if without ROS melodic @Ubuntu 18.04
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' && sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654 && sudo apt-get update && sudo apt install -y ros-melodic-desktop ros-melodic-pcl-ros ros-melodic-tf2-geometry-msgs && echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc && source ~/.bashrc && sudo apt install -y python-rosdep python-rosinstall python-rosinstall-generator python-wstool build-essential && sudo rosdep init && rosdep update