#https://gis.stackexchange.com/questions/28583/gdal-perform-simple-least-cost-path-analysis
#https://gis.stackexchange.com/users/15607/ustroetz
#http://scikit-image.org/docs/dev/api/skimage.graph.html#route-through-array
#

# create slope with
#gdaldem slope -s 1111200 D:\DATA\Altai\srtm_54_03.tif D:\DATA\Altai\LCPA\srtm_54_03_slope.tif

#reclass slope with
# gdal_calc.py -A srtm_54_03_slope.tif --outfile=srtm_54_03_slope_reclass.tif --calc="0.0001*(A==0)+ A*(A>0)"

# run main.py


import gdal, osr
from skimage.graph import route_through_array
from skimage.graph._mcp import MCP
import numpy as np


def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array

def coord2pixelOffset(rasterfn,x,y):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    xOffset = int((x - originX)/pixelWidth)
    yOffset = int((y - originY)/pixelHeight)
    return xOffset,yOffset

def createPath(CostSurfacefn,costSurfaceArray,startCoord,stopCoord):

    # coordinates to array index
    startCoordX = startCoord[0]
    startCoordY = startCoord[1]
    startIndexX,startIndexY = coord2pixelOffset(CostSurfacefn,startCoordX,startCoordY)

    stopCoordX = stopCoord[0]
    stopCoordY = stopCoord[1]
    stopIndexX,stopIndexY = coord2pixelOffset(CostSurfacefn,stopCoordX,stopCoordY)

    # create path
    indices, weight = route_through_array(costSurfaceArray, (startIndexY,startIndexX), (stopIndexY,stopIndexX),geometric=False,fully_connected=True)
    #mcp_init = MCP(costSurfaceArray, offsets=None, fully_connected=True, sampling=None)
    #indices, weight = mcp_init.find_costs(costSurfaceArray, (startIndexY,startIndexX), (stopIndexY,stopIndexX))
    indices = np.array(indices).T
    path = np.zeros_like(costSurfaceArray)
    path[indices[0], indices[1]] = 1
    return path

def array2raster(newRasterfn,rasterfn,array):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

def main(CostSurfacefn,outputPathfn,startCoord,stopCoord):

    costSurfaceArray = raster2array(CostSurfacefn) # creates array from cost surface raster

    pathArray = createPath(CostSurfacefn,costSurfaceArray,startCoord,stopCoord) # creates path array

    array2raster(outputPathfn,CostSurfacefn,pathArray) # converts path array to raster


if __name__ == "__main__":
    CostSurfacefn = r'srtm_54_03_slope_reclass.tif'
    startCoord = (86.5929,48.9655)
    stopCoord = (87.4866,48.737)
    outputPathfn = r'srtm_54_03_slope_reclass_path_001.tif'
    main(CostSurfacefn,outputPathfn,startCoord,stopCoord)
