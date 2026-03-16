# Install script for directory: /home/raju/igv/src/depthai-ros/depthai_examples

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/raju/igv/install/depthai_examples")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE DIRECTORY FILES "/home/raju/igv/src/depthai-ros/depthai_examples/params")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE DIRECTORY FILES "/home/raju/igv/src/depthai-ros/depthai_examples/rviz")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE DIRECTORY FILES "/home/raju/igv/src/depthai-ros/depthai_examples/resources")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/launch" TYPE DIRECTORY FILES "/home/raju/igv/src/depthai-ros/depthai_examples/launch/" FILES_MATCHING REGEX "/[^/]*\\.py$")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/crop_control_service")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/crop_control_service")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/crop_control_service.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/mobilenet_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/mobilenet_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/mobilenet_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/rgb_stereo_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/rgb_stereo_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/rgb_stereo_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/stereo_inertial_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_inertial_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/stereo_inertial_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/stereo_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/stereo_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/stereo_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/yolov4_spatial_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_spatial_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/yolov4_spatial_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/yolov4_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/yolov4_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/yolov4_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/feature_tracker")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/feature_tracker")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/feature_tracker.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/tracker_yolov4_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/tracker_yolov4_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node"
         RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/depthai_examples" TYPE EXECUTABLE FILES "/home/raju/igv/build/depthai_examples/tracker_yolov4_spatial_node")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node"
         OLD_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib:"
         NEW_RPATH "/home/raju/igv/install/depthai_bridge/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:/home/raju/igv/install/depthai_ros_msgs/lib:/opt/ros/jazzy/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/depthai_examples/tracker_yolov4_spatial_node")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/raju/igv/build/depthai_examples/CMakeFiles/tracker_yolov4_spatial_node.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/package_run_dependencies" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_index/share/ament_index/resource_index/package_run_dependencies/depthai_examples")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/parent_prefix_path" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_index/share/ament_index/resource_index/parent_prefix_path/depthai_examples")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/environment" TYPE FILE FILES "/opt/ros/jazzy/share/ament_cmake_core/cmake/environment_hooks/environment/ament_prefix_path.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/environment" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/ament_prefix_path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/environment" TYPE FILE FILES "/opt/ros/jazzy/share/ament_cmake_core/cmake/environment_hooks/environment/path.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/environment" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/local_setup.bash")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/local_setup.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/local_setup.zsh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/local_setup.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_environment_hooks/package.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/packages" TYPE FILE FILES "/home/raju/igv/build/depthai_examples/ament_cmake_index/share/ament_index/resource_index/packages/depthai_examples")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples/cmake" TYPE FILE FILES
    "/home/raju/igv/build/depthai_examples/ament_cmake_core/depthai_examplesConfig.cmake"
    "/home/raju/igv/build/depthai_examples/ament_cmake_core/depthai_examplesConfig-version.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/depthai_examples" TYPE FILE FILES "/home/raju/igv/src/depthai-ros/depthai_examples/package.xml")
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/raju/igv/build/depthai_examples/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
