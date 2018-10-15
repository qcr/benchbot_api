cmake_minimum_required(VERSION 2.8.9)
project(benchbot)


set(INSTALL_LIB_DIR "${CMAKE_INSTALL_PREFIX}/lib" CACHE PATH "Installation directory for libraries")
set(INSTALL_INC_DIR "${CMAKE_INSTALL_PREFIX}/include" CACHE PATH "Installation directory for headers")
set(INSTALL_MAN_DIR "${CMAKE_INSTALL_PREFIX}/share/man" CACHE PATH "Installation directory for manual pages")
set(INSTALL_PKGCONFIG_DIR "${CMAKE_INSTALL_PREFIX}/share/pkgconfig" CACHE PATH "Installation directory for pkgconfig (.pc) files")

set (benchbot_VERSION_MAJOR 1)
set (benchbot_VERSION_MINOR 0)

include(GNUInstallDirs)

#set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")

# Setup dependencies
find_package(PkgConfig REQUIRED)

pkg_check_modules(JSONCPP jsoncpp)
link_libraries(${JSONCPP_LIBRARIES})

find_package(CURL REQUIRED)
find_package(OpenCV REQUIRED opencv_core opencv_highgui opencv_imgcodecs)

# Set up include directory
include_directories(include)

# Build program
add_library(benchbot SHARED src/benchbot.cpp src/grid_map.cpp)

target_link_libraries(benchbot ${JSONCPP_LIBRARIES} ${CURL_LIBRARIES} ${OpenCV_LIBS})

configure_file( ${CMAKE_CURRENT_SOURCE_DIR}/benchbot.pc.cmakein
		        ${CMAKE_CURRENT_BINARY_DIR}/benchbot.pc @ONLY)

if(NOT SKIP_INSTALL_FILES AND NOT SKIP_INSTALL_ALL )
    install(TARGETS benchbot LIBRARY DESTINATION ${INSTALL_LIB_DIR})
    install(DIRECTORY include/ DESTINATION ${INSTALL_INC_DIR})
    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/benchbot.pc DESTINATION "${INSTALL_PKGCONFIG_DIR}")
endif()
