import numpy as np


def hour2rad(hms):
    hms_split = hms.split("h")
    h = float(hms_split[0])
    ms_split = hms_split[1].split("m")
    m = float(ms_split[0])
    s = float(ms_split[1].split("s")[0])
    deg = 360 - (h * 15 + m / 4 + s / 240)
    return np.deg2rad(deg)


def angle2rad(dms):
    dms_split = dms.split("°")
    d = float(dms_split[0])
    ms_split = dms_split[1].split("'")
    m = float(ms_split[0])
    s = float(ms_split[1].split('"')[0])
    t = m / 60 + s / 3600
    deg = d
    if d < 0:
        deg -= t
    else:
        deg += t
    return np.deg2rad(deg)


def lnglat2xyz(lng, lat):
    t = np.cos(lat)
    x = np.cos(lng) * t
    y = np.sin(lng) * t
    z = np.sin(lat)
    return x, y, z


def calc_pixel_zenith_angle(pixel_obj, pixel_zenith, sight_distance):
    v1 = [*pixel_zenith, sight_distance]
    v2 = [*pixel_obj, sight_distance]
    return np.arccos(np.dot(v1, v2) / np.linalg.norm(v1) / np.linalg.norm(v2))


def calc_observer_position(gha_declination_objs, zenith_angle_objs):
    sight_distance = get_pixel_sight_distance(gha_declination_objs, pixel_objs)

    zenith_angle_objs = []
    for pixel_obj in pixel_objs:
        zenith_angle_obj = calc_pixel_zenith_angle(
            pixel_zenith, pixel_obj, sight_distance
        )
        zenith_angle_objs.append(zenith_angle_obj)

    A = []
    y = []
    for gd, z in zip(
        gha_declination_objs,
        zenith_angle_objs,
    ):
        lng = hour2rad(gd[0])
        lat = angle2rad(gd[1])
        xyz = lnglat2xyz(lng, lat)
        A.append(xyz)
        y.append(np.cos(z))

    AA = np.array(A)
    yy = np.array(y)

    res = np.linalg.pinv(AA) @ yy
    res /= np.linalg.norm(res)

    lat = np.rad2deg(np.arcsin(res[2]))
    lng = np.rad2deg(np.arctan2(res[1], res[0]))
    return lng, lat


def calc_var_for_sight_distance(xyz_objs, pixel_objs, z):
    sum_of_square_diff = 0
    n = len(xyz_objs)
    for i in range(n):
        gd_i = xyz_objs[i]
        gd_i_norm = np.linalg.norm(gd_i)

        pixel_i = [*pixel_objs[i], z]
        pixel_i_norm = np.linalg.norm(pixel_i)

        for j in range(i + 1, n):
            gd_j = xyz_objs[j]

            gd_angle_cos = np.dot(gd_i, gd_j) / np.linalg.norm(gd_j) / gd_i_norm

            pixel_j = [*pixel_objs[j], z]
            pixel_angle_cos = (
                np.dot(pixel_i, pixel_j) / np.linalg.norm(pixel_j) / pixel_i_norm
            )
            square_diff = (pixel_angle_cos - gd_angle_cos) ** 2
            sum_of_square_diff += square_diff
    return sum_of_square_diff


def get_pixel_sight_distance(gha_declination_objs, pixel_objs):
    xyz_objs = []

    for gd in gha_declination_objs:
        lng = hour2rad(gd[0])
        lat = angle2rad(gd[1])
        xyz = lnglat2xyz(lng, lat)
        xyz_objs.append(xyz)

    l = 0
    r = 1e10
    while r - l > 1e-6:
        z1 = (r - l) / 3 + l
        z2 = (r - l) * 2 / 3 + l

        var_z1 = calc_var_for_sight_distance(xyz_objs, pixel_objs, z1)
        var_z2 = calc_var_for_sight_distance(xyz_objs, pixel_objs, z2)
        if var_z1 > var_z2:
            l = z1
        else:
            r = z2
    return r


# 拍照时刻，天体在地球 0° 经线处的时角和赤经
gha_declination_obj_1 = ["16h4m10.9s", "13°39'15.2\""]
gha_declination_obj_2 = ["15h36m7.09s", "4°11'4.5\""]
gha_declination_obj_3 = ["14h50m44.52", "24°10'46.5\""]
gha_declination_obj_4 = ["14h37m29.76", "-13°26'19.1\""]
gha_declination_obj_5 = ["15h55m6.43", "3°20'16.6\""]

# 照片中，天体的坐标；其中，照片正中心为 0,0
pixel_obj_1 = [44, -130.5]
pixel_obj_2 = [-97, 97.5]
pixel_obj_3 = [-384, -364.5]
pixel_obj_4 = [-412, 580.5]
pixel_obj_5 = [13, 106.5]

# 照片中，天顶的坐标
pixel_zenith = [-117.5, -857.5]

gha_declination_objs = [
    gha_declination_obj_1,
    gha_declination_obj_2,
    gha_declination_obj_3,
    gha_declination_obj_4,
    gha_declination_obj_5,
]
pixel_objs = [pixel_obj_1, pixel_obj_2, pixel_obj_3, pixel_obj_4, pixel_obj_5]


lng, lat = calc_observer_position(gha_declination_objs, pixel_objs)
print("{},{}".format(lng, lat))
