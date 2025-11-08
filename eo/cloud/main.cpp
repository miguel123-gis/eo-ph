#include <iostream>
#include <string>
#include <sstream>

#include "gdal_priv.h"
// #include "/opt/homebrew/Cellar/gdal/3.11.0_2/include/cpl_conv.h"
// #include "/opt/homebrew/Cellar/gdal/3.11.0_2/include/gdalwarper.h"

int main(int argc, char* argv[]) {
    if (argc > 1) {
        std::cout << "Received " << argv[1] << std::endl;
        GDALAllRegister();

    } else {
        std::cout << "No TIF received." << std::endl;
    }
    return 0;
}