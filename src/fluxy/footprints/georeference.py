from osgeo.osr import SpatialReference


def get_bounding_box(center: tuple[int, int]):
    ...


def get_spatial_reference_system(lat: float, lon: float):
    ...


def get_utm_epsg(lat: float, lon: float):
    zone_num = (lon + 180) / 6 + 1
    if lat < 0: epsg = 32700 + zone_num
    else: epsg = 32600 + zone_num
    return epsg
