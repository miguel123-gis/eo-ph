#include <iostream>
#include <string>
#include <sstream>

#include "gdal_priv.h"

int main(int argc, char* argv[]) {
    if (argc > 1) {
        std::cout << "Received " << argv[1] << std::endl;
        GDALAllRegister();

    } else {
        std::cout << "No TIF received." << std::endl;
    }
    return 0;
}