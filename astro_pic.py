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
    deg = abs(d) + m / 60 + s / 3600
    rad = np.deg2rad(deg)
    if d < 0:
        return -rad
    return rad


def lnglat2xyz(lng, lat):
    t = np.cos(lat)
    x = np.cos(lng) * t
    y = np.sin(lng) * t
    z = np.sin(lat)
    return x, y, z


def xyz2lnglat(v):
    v /= np.linalg.norm(v)
    lng = np.arctan2(v[1], v[0])
    lat = np.arcsin(v[2])
    return lat, lng


def vec_angle_cos(vec1, vec2):
    return np.dot(vec1, vec2) / np.linalg.norm(vec1) / np.linalg.norm(vec2)


def calc_pixel_zenith_angle_cos(star_img, zenith, focal_length):
    v1 = [*zenith, focal_length]
    v2 = [*star_img, focal_length]
    return vec_angle_cos(v1, v2)


def calc_observer_position(stars_hourangle, zenith_angle_cos_list):
    f = get_focal_length(stars_hourangle, stars_img)

    zenith_angle_cos_list = []
    for star_img in stars_img:
        zenith_angle_cos_obj = calc_pixel_zenith_angle_cos(zenith, star_img, f)
        zenith_angle_cos_list.append(zenith_angle_cos_obj)

    A = np.array([hourangle_to_xyz(i) for i in stars_hourangle])

    b = np.array(zenith_angle_cos_list)

    res = np.linalg.pinv(A) @ b
    res /= np.linalg.norm(res)

    lat_rad, lng_rad = xyz2lnglat(res)
    return np.rad2deg(lat_rad), np.rad2deg(lng_rad)


def calc_var_for_focal_length(stars_xyz, stars_img, f):
    sum_of_square_diff = 0
    n = len(stars_xyz)
    for i in range(n):
        star_i = stars_xyz[i]
        img_i = [*stars_img[i], f]

        for j in range(i + 1, n):
            star_j = stars_xyz[j]

            angle_cos = vec_angle_cos(star_i, star_j)

            img_j = [*stars_img[j], f]
            img_angle_cos = vec_angle_cos(img_i, img_j)

            square_diff = (img_angle_cos - angle_cos) ** 2
            sum_of_square_diff += square_diff
    return sum_of_square_diff


def hourangle_to_xyz(hourangle):
    lng = hour2rad(hourangle[0])
    lat = angle2rad(hourangle[1])
    xyz = lnglat2xyz(lng, lat)
    return xyz


def get_focal_length(stars_hourangle, stars_img):
    stars_xyz = [hourangle_to_xyz(i) for i in stars_hourangle]

    l = 0
    r = 1e9
    for _ in range(100):
        ml = (r - l) / 3 + l
        mr = (r - l) * 2 / 3 + l

        var_z1 = calc_var_for_focal_length(stars_xyz, stars_img, ml)
        var_z2 = calc_var_for_focal_length(stars_xyz, stars_img, mr)
        if var_z1 > var_z2:
            l = ml
        else:
            r = mr
    return r


def astronomic_latitude_to_geodetic_latitude(astronomic_latitudes_in_degree):
    bn = [
        0.0016248797304581834,
        -1.5959025318697836e-06,
        1.7384354350353823e-09,
        6.2648178203277005e-12,
        -2.723302870849e-14,
    ]
    angle_rad = np.deg2rad(astronomic_latitudes_in_degree)
    res = 0
    for i, b in enumerate(bn):
        res += b * np.sin(2 * (i + 1) * angle_rad)
    return astronomic_latitudes_in_degree + np.rad2deg(res)


# 拍照时刻，天体在地球 0° 经线处的时角和赤经
star_hourangle_1 = ["16h4m10.9s", "13°39'15.2\""]
star_hourangle_2 = ["15h36m7.09s", "4°11'4.5\""]
star_hourangle_3 = ["14h50m44.52", "24°10'46.5\""]
star_hourangle_4 = ["14h37m29.76", "-13°26'19.1\""]
star_hourangle_5 = ["15h55m6.43", "3°20'16.6\""]

# 照片中，天体的坐标；其中，照片正中心为 0,0
star_img_1 = [44, -130.5]
star_img_2 = [-97, 97.5]
star_img_3 = [-384, -364.5]
star_img_4 = [-412, 580.5]
star_img_5 = [13, 106.5]

# 照片中，天顶的坐标
zenith = [-117.5, -857.5]

stars_hourangle = [
    star_hourangle_1,
    star_hourangle_2,
    star_hourangle_3,
    star_hourangle_4,
    star_hourangle_5,
]
stars_img = [star_img_1, star_img_2, star_img_3, star_img_4, star_img_5]


lat, lng = calc_observer_position(stars_hourangle, stars_img)

lat = astronomic_latitude_to_geodetic_latitude(lat)

print("{},{}".format(lat, lng))
