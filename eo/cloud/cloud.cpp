#include <iostream>
#include <string>
#include <sstream>

int main(int argc, char* argv[]) {
    if (argc > 1) {
        std::cout << "Received " << argv[1] << std::endl;
    } else {
        std::cout << "No TIF received." << std::endl;
    }
    return 0;
}