#include <iostream>
using namespace std;
#include "gdal_priv.h"
#include "cpl_string.h"

int main() {
    const char *pszFormat = "GTiff";
    GDALDriver *poDriver;
    int driverCount;
    char **papszMetadata;
    GDALAllRegister();
    poDriver = GetGDALDriverManager()->GetDriverByName(pszFormat);
    driverCount = GetGDALDriverManager()->GetDriverCount();

    if (poDriver == NULL)
        printf("Driver is NULL");
        exit(1);

    papszMetadata = poDriver->GetMetadata();
    if (CSLFetchBoolean(papszMetadata, GDAL_DCAP_CREATE, FALSE))
        printf( "Driver %s supports Create() method.\n", pszFormat);


    if (CSLFetchBoolean(papszMetadata, GDAL_DCAP_CREATECOPY, FALSE))
        printf( "Driver %s supports CreateCopy() method.\n", pszFormat );
}