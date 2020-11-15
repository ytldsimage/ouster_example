#!/bin/bash
set -x


#if without ROS kinetic @Ubuntu 16.04
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' && sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654 && sudo apt update && sudo apt install -y ros-kinetic-desktop ros-kinetic-pcl-ros ros-kinetic-tf2-geometry-msgs ros-kinetic-gazebo-ros-control ros-kinetic-controller-interface ros-kinetic-hardware-interface ros-kinetic-hector-gazebo-plugins ros-kinetic-hector-pose-estimation ros-kinetic-hector-sensors-description ros-kinetic-message-to-tf && echo "source /opt/ros/kinetic/setup.bash" >> ~/.bashrc && source ~/.bashrc && sudo apt install -y python-rosdep python-rosinstall python-rosinstall-generator python-wstool build-essential && sudo rosdep init && rosdep update