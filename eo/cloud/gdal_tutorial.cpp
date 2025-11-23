#include <iostream>
using namespace std;
#include "gdal_priv.h"

std::string getSRID(const GDALDataset *inDataset) { // INput is not just inDataset but a pointer to that dataset because of GDALDatasetUniquePtr poDataset;
    const OGRSpatialReference *poSRS = inDataset->GetSpatialRef(); // Create a pointer to the SRID object where it's like tif_obj.GetSpatialRef()
    char *pszWKT = nullptr; // Create a pointer again before computing it
    poSRS->exportToPrettyWkt(&pszWKT); // Points to the pointer

    std::string result(pszWKT); // Pass the spatialreference object to a string object
    CPLFree(pszWKT); // Close/delete
    
    return result;
}

void printRasterInfo(GDALDataset *inDataset) { // Not anymore a const GDALDataset because GetDriver() is not a const method
    double adfGeoTransform[6];

    printf("Driver : %s/%s\n",
            inDataset->GetDriver()->GetDescription(),
            inDataset->GetDriver()->GetMetadataItem(GDAL_DMD_LONGNAME)
    );
    printf(
        "Size is %dx%dx%d\n",
        inDataset->GetRasterXSize(), 
        inDataset->GetRasterYSize(),
        inDataset->GetRasterCount()
    );

    // if (poDataset->GetProjectionRef() != NULL)
    //     printf("Projection is '%s'\n", poDataset->GetProjectionRef());
        
    if (inDataset->GetGeoTransform(adfGeoTransform) == CE_None)
    {
        printf("Origin = (%.6f,%.6f)\n", adfGeoTransform[0], adfGeoTransform[3]);
        printf("Pixel Size = (%.6f,%.6f)\n", adfGeoTransform[1], adfGeoTransform[5]);
    }
}

GDALDriver* getDriverFromFormatStr(const char *fileFormat) {
    GDALDriver *poDriver;
    poDriver = GetGDALDriverManager()->GetDriverByName(fileFormat);

    if (poDriver == NULL)
        exit (1);

    return poDriver;
}

void printCreateSupport(const char *pszFormat) {
    GDALDriver *inPoDriver;
    inPoDriver = getDriverFromFormatStr(pszFormat);
    
    char **papszMetadata;
    inPoDriver = GetGDALDriverManager()->GetDriverByName(pszFormat);
    if (inPoDriver ==  NULL)
        exit (1);
    papszMetadata = inPoDriver->GetMetadata();
    if( CSLFetchBoolean( papszMetadata, GDAL_DCAP_CREATE, FALSE ) )
        printf( "Driver %s supports Create() method.\n", pszFormat );
    if( CSLFetchBoolean( papszMetadata, GDAL_DCAP_CREATECOPY, FALSE ) )
        printf( "Driver %s supports CreateCopy() method.\n", pszFormat );
}

void copyDS(GDALDataset *inDataset, const char *outFileName, GDALDriver *fileDriver) {
    GDALDataset *poDestDataset;

    fileDriver = getDriverFromFormatStr("GTiff");
    poDestDataset = fileDriver->CreateCopy(outFileName, inDataset, FALSE, NULL, NULL, NULL);

    if (poDestDataset != NULL)
        GDALClose((GDALDatasetH) poDestDataset);
}

void createDS(const char *outFileName, GDALDriver *fileDriver, int rowSize, int colSize, double adfGeoTransform[6], int utmZone, const char *datumString) {
    GDALDataset *poDestDataset; // Create a GDALDataset object
    OGRSpatialReference oSRS; // SRID object
    char **papszOptions = NULL; // NULL, required for Create()
    char *pszSRS_WKT = NULL; // String to store the SRID as WKT
    GDALRasterBand *poOutBand; // Band where the info will be written
    GByte abyRaster[rowSize*colSize]; // Flat array e.g. 512*512=262144 bytes

    poDestDataset = fileDriver->Create(outFileName, rowSize, colSize, 1, GDT_Byte, papszOptions);
    poDestDataset->SetGeoTransform(adfGeoTransform);

    oSRS.SetUTM(utmZone, TRUE);
    oSRS.SetWellKnownGeogCS(datumString);
    oSRS.exportToWkt(&pszSRS_WKT);

    poDestDataset->SetProjection(pszSRS_WKT);
    CPLFree(pszSRS_WKT); // Since pszSRS_WKT is already used, clear memory allocated for this object

    poOutBand = poDestDataset->GetRasterBand(1);

    CPLErr outFileErr = poOutBand->RasterIO(GF_Write, 0, 0, rowSize, colSize, abyRaster, rowSize, colSize, GDT_Byte, 0, 0);

    if (outFileErr == CE_None)
        printf("Successfuly wrote new file");

    GDALClose((GDALDatasetH) poDestDataset);
}

GDALRasterBand* printRasterBandInfo(GDALDataset *inDataset) {
    GDALRasterBand  *poBand;
    int             nBlockXSize, nBlockYSize;
    int             bGotMin, bGotMax;
    double          adfMinMax[2];

    poBand = inDataset->GetRasterBand(1);
    poBand->GetBlockSize (&nBlockXSize, &nBlockYSize);

    printf(
        "Block=%dx%d Type=%s, ColorInterp=%s\n",
        nBlockXSize, nBlockYSize,
        GDALGetDataTypeName(poBand->GetRasterDataType()),
        GDALGetColorInterpretationName(
            poBand->GetColorInterpretation()
        )
    );

    adfMinMax[0] = poBand->GetMinimum(&bGotMin);
    adfMinMax[1] = poBand->GetMinimum(&bGotMax);

    if (!(bGotMin && bGotMax))
        GDALComputeRasterMinMax((GDALRasterBandH)poBand, TRUE, adfMinMax);
    printf("Min=%.3f, Max=%.3f\n", adfMinMax[0], adfMinMax[1]);

    if (poBand->GetOverviewCount() > 0)
        printf("Band has %d overviews.\n", poBand->GetOverviewCount());
    if (poBand->GetColorTable() != NULL)
        printf(
            "Band has a color table with %d entries.\n",
            poBand->GetColorTable()->GetColorEntryCount()
        );

    return poBand;
}

void readRasterData(GDALRasterBand *poBand) {
    float   *pafScanline;
    int     nXSize = poBand->GetXSize();
    pafScanline = (float *) CPLMalloc(sizeof(float)*nXSize);
    CPLErr err = poBand->RasterIO(GF_Read, 0,0, nXSize, 1, pafScanline, nXSize, 1, GDT_Float32, 0, 0);

    if (err == CE_None) // Need to put the output of RasterIO into a variable to avoid warn_unused_result error
        printf("Succesfully read raster\n");
}

int main(int argc, const char* argv[]) {
    if (argc < 1) {    
        return EINVAL;  // Common way to signal an error
    }
    const char *pszSrcFilename = argv[1]; // Constant variable and points to the filename 
    const char *pszDestFilename = argv[2];

    GDALDatasetUniquePtr poSrcDataset; // GDAL-provided pointer (like const char*) that manages the lifetime (e.g. closing) of a dataset
    GDALAllRegister(); // Register all drivers, done after declaring variables
    const GDALAccess eAccess = GA_ReadOnly; // Set to read-only mode

    poSrcDataset = GDALDatasetUniquePtr(   // Takes ownership of the dataset object
        GDALDataset::FromHandle( // "Convert a GDALDatasetH to a GDALDataset*." - https://gdal.org/en/stable/doxygen/classGDALDataset.html
            GDALOpen(pszSrcFilename, eAccess) // Open the provided TIF as read only - returns a GDALDataset object - https://gdal.org/en/stable/api/gdaldataset_cpp.html#_CPPv411GDALDataset
        )
    );

    // 01 Get SRID
    std::cout << getSRID(poSrcDataset.get()) << "\n"; // Just gets the object, does not transfer ownership
    
    // 02 Get Dataset information
    printRasterInfo(poSrcDataset.get());

    // 03 Fetching a raster band
    GDALRasterBand *poBand;
    poBand = printRasterBandInfo(poSrcDataset.get());
    readRasterData(poBand);

    // GDALClose(); // No need for this because GDALDatasetUniquePtr handles closing

    // 04 Check support for creating files
    printCreateSupport("GTiff");    

    // 05 Create file using CreateCopy()
    GDALDriver *inPoDriver;
    inPoDriver = getDriverFromFormatStr("GTiff");
    // copyDS(poSrcDataset.get(), pszDestFilename, inPoDriver);

    // 06 Create file using Create() - when creating totally new rasters
    double adfGeoTransform[6] = { 444720, 30, 0, 3751320, 0, -30 };
    const char *datumString = "NAD27";
    createDS(pszDestFilename, inPoDriver, 512, 512, adfGeoTransform, 11, datumString);

    return 0;
}