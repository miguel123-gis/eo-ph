#include <iostream>
using namespace std;
#include "gdal_priv.h"

std::string getSRID(const GDALDataset *inDataset) {
    const OGRSpatialReference *poSRS = inDataset->GetSpatialRef(); // Create a pointer to the SRID object where it's like tif_obj.GetSpatialRef()
    char *pszWKT = nullptr; // Create a pointer again before computing it
    poSRS->exportToPrettyWkt(&pszWKT); // Points to the pointer

    std::string result(pszWKT); // Pass the spatialreference object to a string object
    CPLFree(pszWKT); // Close/delete
    
    return result;
}

int main(int argc, const char* argv[]) {
    if (argc != 2) {    // If more than 2 args e.g. test some.tif another.tif
        return EINVAL;  // Common way to signal an error
    }
    const char* pszFilename = argv[1]; // Constant variable and points to the filename 
    GDALDatasetUniquePtr poDataset; // GDAL-provided pointer (like const char*) that manages the lifetime (e.g. closing) of a dataset
    GDALAllRegister(); // Register all drivers, done after declaring variables
    const GDALAccess eAccess = GA_ReadOnly; // Set to read-only mode
    poDataset = GDALDatasetUniquePtr(   // Takes ownership of the dataset object
        GDALDataset::FromHandle( // "Convert a GDALDatasetH to a GDALDataset*." - https://gdal.org/en/stable/doxygen/classGDALDataset.html
            GDALOpen(pszFilename, eAccess) // Open the provided TIF as read only - returns a GDALDataset object - https://gdal.org/en/stable/api/gdaldataset_cpp.html#_CPPv411GDALDataset
        )
    );

    std::cout << getSRID(poDataset.get()); // Just gets the object, does not transfer ownership
    
    return 0;
}