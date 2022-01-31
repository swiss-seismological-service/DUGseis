from dug_seis.coordinate_transforms import local_to_global, global_to_local

point = [0, 0, -30]


global_coords = local_to_global(
    local_crs="LV95",
    global_crs="WGS84",
    translation_vector=[
        2679720.696,  # LV95 easting origin of local coordinate system
        1151600.128,  # LV95 northing origin of local coordinate system
        1480,
    ],  # elevation of origin of local coordinate system,
    point=point,
)

point = global_to_local(
    local_crs="LV95",
    global_crs="WGS84",
    translation_vector=[
        2679720.696,  # LV95 easting origin of local coordinate system
        1151600.128,  # LV95 northing origin of local coordinate system
        1480,
    ],  # elevation of origin of local coordinate system
    point=global_coords,
)
