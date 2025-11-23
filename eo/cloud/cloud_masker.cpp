#include <iostream>
#include <string>
#include "gdal_priv.h"
#include "cpl_conv.h"
#include "gdalwarper.h"

class CloudRemover {
    private:
        const char* geotifFile;
        GDALDataset *geotifDataset;

    public:
        CloudRemover(const char* geotifFilename) { // Constructor???
            geotifFile = geotifFilename;
            GDALAllRegister();

            // Set pointer to Geotiff dataset as class member???
            geotifDataset = (GDALDataset*) GDALOpen(geotifFile, GA_ReadOnly);

        }

        // Define destructor function to close dataset, 
        // for when object goes out of scope or is removed
        // from memory???
        ~CloudRemover() {
            GDALClose(geotifDataset);
            GDALDestroyDriverManager();
        }
};