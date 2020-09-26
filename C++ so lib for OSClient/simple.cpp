#include <iostream>
#include <fstream>
#include <memory>
#include <thread>
#include <vector>

#include <Eigen/Eigen>

#include "ouster/client.h"
#include "ouster/lidar_scan.h"
#include "ouster/packet.h"
#include "ouster/types.h"

namespace sensor = ouster::sensor;


// PLY file implementaiton (see below)
void ply_write_header(std::ostream& os, int W, int H, int frame_count);
void ply_write_pixel(std::ostream& os,
		     Eigen::Array<double, Eigen::Dynamic, 3> xyz,
		     Eigen::Array<ouster::LidarScan::raw_t, Eigen::Dynamic, 4> pix);

/*
  With the exception of PLY file construction, the code below illustrates how to
  use the ouster_client API to construct 3D points from a live sensor.
 */
int
main(int argc, char** argv)
{
  if(argc < 4) {
    std::cout << "usage: " << argv[0]
	      << " <sensor hostname> <udp receiver> <points.ply> <frame_count [min 5 or -1 for infinite]>"
	      << std::endl;
    return 0;
  }

  // Connect to the sensor given hostname and receiver IP
  auto client = sensor::init_client(argv[1], argv[2]);

  if(!client) {
    std::cerr << "error: client failed to initialize" << std::endl;
    return -1;
  }

  // Query the sensor for config information
  auto metadata = sensor::get_metadata(*client);
  auto info = sensor::parse_metadata(metadata);
  auto pf = sensor::get_format(info);

  // Grab specific sensor config parameters
  int W = info.format.columns_per_frame;
  int H = info.format.pixels_per_column;

  // Allocate a buffer for a single spin
  ouster::LidarScan ls(W, H);
  auto xyz_lut = ouster::make_xyz_lut(info);

  // Create the PLY file to store data
  std::ofstream ply_file(argv[3]);

  if(!ply_file.is_open()) {
    std::cerr << "error: can't write to " << argv[3] << std::endl;
    return -1;
  }

  // Write the PLY file header
  int frame_count = std::atoi(argv[4]);
  ply_write_header(ply_file, W, H, frame_count);

  // handle_single_scan is called for each full revolation of the sensor
  bool running = true;
  
  auto handle_single_scan =
    [&](std::chrono::nanoseconds scan_ts) mutable
    {
      std::cout << "[" << scan_ts.count() << "] new scan" << std::endl;

      // Convert the sensor image to 3D points
      auto points = ouster::cartesian(ls, xyz_lut);

      // Write each point and pixel data to the PLY file, done by row and column
      // for illutrattive purposes
      for (auto u = 0; u < ls.h; u++) {
	for (auto v = 0; v < ls.w; v++) {

	  // 'points' and 'data' are containers for accessing point and point
	  // property data
	  const auto xyz = points.row(u * ls.w + v);
	  const auto pix = ls.data.row(u * ls.w + v);

	  // Do the actual write to the PLY file
	  ply_write_pixel(ply_file, xyz, pix);
	}
      }

      // Flush everything to disk
      ply_file.flush();
      
      if(--frame_count == 0) {
	running = false;
      }
    };

  // Convert handle_single_scan function to a function that can process
  // lidar packets from the sensor
  auto batch_and_update = sensor::batch_to_scan(W, pf, handle_single_scan);

  uint8_t lidar_buf[pf.lidar_packet_size + 1];
  uint8_t imu_buf[pf.lidar_packet_size + 1];

  // Mainloop for processing data packets from the sensor
  while (running) {
    // Poll the client for data and add to our lidar scan
    sensor::client_state st = sensor::poll_client(*client);
      
    if(st & sensor::client_state::CLIENT_ERROR) break;

    // It's a lidar packet, add it to the partial scan
    if (st & sensor::client_state::LIDAR_DATA
	&& sensor::read_lidar_packet(*client, lidar_buf, pf)) {
      batch_and_update(lidar_buf, ls);
    }

    // It's an IMU packet, ignore for now.
    if (st & sensor::client_state::IMU_DATA) {
      sensor::read_imu_packet(*client, imu_buf, pf);
    }
  }

  // close the PLY file
  ply_file.close();

  return -1;
}

/*
  The following are helper functions that format the PLY file.
 */

// Write a PLY file header
void ply_write_header(std::ostream& os, int W, int H, int frame_count)
{
  auto pixel_count = W * H * frame_count;
  
  os << "ply" << std::endl
     << "format binary_little_endian 1.0" << std::endl
     << "comment Created by simple.cpp from Ouster (c) 2020" << std::endl
     << "element vertex " << pixel_count << std::endl
     << "property float x" << std::endl
     << "property float y" << std::endl
     << "property float z" << std::endl
     << "property uint intensity" << std::endl
     << "property uint reflectivity" << std::endl
     << "property uint noise" << std::endl
     << "end_header" << std::endl
    ;
}

// Write a PLY file pixel
void ply_write_pixel(std::ostream& os,
		     Eigen::Array<double, Eigen::Dynamic, 3> xyz,
		     Eigen::Array<ouster::LidarScan::raw_t, Eigen::Dynamic, 4> pix)
{
  float val;

  for(int i = 0; i < 3; ++i) {
    val = xyz(i);
    os.write((char*)&val, sizeof(val));
  }

  // Index the 'pix' array
  std::vector< ouster::LidarScan::LidarScanIndex > pix_types =
    {
     ouster::LidarScan::INTENSITY,
     ouster::LidarScan::REFLECTIVITY,
     ouster::LidarScan::NOISE,
    };

  std::uint32_t t_val;

  for(auto t : pix_types) {
    t_val = pix(t);
    os.write((char*)&t_val, sizeof(t_val));
  }    
}
