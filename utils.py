import numpy as np


class VORDME:
    n = 0

    def __init__(self, id_, lat, lon, alt, range_, name):
        self.n = VORDME.n
        VORDME.n += 1
        self.id_ = id_
        self.pos = Position(lat, lon, alt, 'geo')
        self.range_ = range_
        self.name = name


class Latitude:

    def __init__(self, *args):
        if args.__len__() == 5:
            self.r = args[0]
            self.dd = args[1]
            self.d = args[2]
            self.m = args[3]
            self.s = args[4]
        elif args.__len__() == 4:
            self.dd = args[0]
            self.d = args[1]
            self.m = args[2]
            self.s = args[3]
            self.r = dd2r(self.dd)
        elif args.__len__() == 3:
            self.d = args[0]
            self.m = args[1]
            self.s = args[2]
            self.dd = dms2dd(self.d, self.m, self.s)
            self.r = dms2r(self.d, self.m, self.s)
        elif args.__len__() == 1:
            self.dd = args[0]
            self.r = dd2r(self.dd)
            self.d, self.m, self.s = dd2dms(self.dd)
        else:
            print("Invalid number of arguments!")


class Longitude:

    def __init__(self, *args):
        if args.__len__() == 5:
            self.r = args[0]
            self.dd = args[1]
            self.d = args[2]
            self.m = args[3]
            self.s = args[4]
        elif args.__len__() == 4:
            self.dd = args[0]
            self.d = args[1]
            self.m = args[2]
            self.s = args[3]
            self.r = dd2r(self.dd)
        elif args.__len__() == 3:
            self.d = args[0]
            self.m = args[1]
            self.s = args[2]
            self.dd = dms2dd(self.d, self.m, self.s)
            self.r = dms2r(self.d, self.m, self.s)
        elif args.__len__() == 1:
            self.dd = args[0]
            self.r = dd2r(self.dd)
            self.d, self.m, self.s = dd2dms(self.dd)
        else:
            raise TypeError('invalid number of arguments')


class GeographicPosition:

    def __init__(self, *args):
        if args.__len__() == 1:
            lat, lon, self.alt = cart2geo(args[0])
            self.lat = Latitude(lat)
            self.lon = Longitude(lon)
        elif args.__len__() == 3:
            self.lat = Latitude(args[0])
            self.lon = Longitude(args[1])
            self.alt = args[2]
        elif args.__len__() == 5:
            self.lat = Latitude(args[0], args[1])
            self.lon = Longitude(args[4], args[3])
            self.alt = args[4]
        elif args.__len__() == 7:
            self.lat = Latitude(args[0], args[1], args[2])
            self.lon = Longitude(args[3], args[4], args[5])
            self.alt = args[6]
        else:
            raise TypeError('invalid number of arguments')


class CartesianPosition:

    def __init__(self, *args):
        if args.__len__() == 1:
            self.x, self.y, self.z = geo2cart(args[0])
        elif args.__len__() == 3:
            self.x = args[0]
            self.y = args[1]
            self.z = args[2]
        else:
            raise TypeError('invalid number of arguments')


class Position:

    def __init__(self, *args):
        if args.__len__() == 4:
            if args[3] == 'geo':
                self.geo = GeographicPosition(args[0], args[1], args[2])
                self.cart = CartesianPosition(self.geo)
            elif args[3] == 'cart':
                self.cart = CartesianPosition(args[0], args[1], args[2])
                self.geo = GeographicPosition(self.cart)
            else:
                print('Invalid argument!')
        elif args.__len__() == 6:
            self.geo = GeographicPosition(args[0], args[1], args[2])
            self.cart = CartesianPosition(args[3], args[4], args[5])
        elif args.__len__() == 7:
            self.geo = GeographicPosition(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
            self.cart = CartesianPosition(self.geo)
        else:
            print('Invalid number of arguments!')

    def print_geo(self):
        if self.geo.lat.dd > 0:
            if self.geo.lon.dd > 0:
                print("{0}d{1}'{2:.2f}''N {3}d{4}'{5:.2f}''E\n".format(self.geo.lat.d, self.geo.lat.m, self.geo.lat.s,
                                                                       self.geo.lon.d, self.geo.lon.m, self.geo.lon.s))
            else:
                print("{0}d{1}'{2}''N {3}d{4}'{5}''W\n".format(self.geo.lat.d, self.geo.lat.m, self.geo.lat.s,
                                                               -self.geo.lon.d, self.geo.lon.m, self.geo.lon.s))
        else:
            if self.geo.lon.dd > 0:
                print("{0}d{1}'{2}''S {3}d{4}'{5}''E\n".format(-self.geo.lat.d, self.geo.lat.m, self.geo.lat.s,
                                                               self.geo.lon.d, self.geo.lon.m, self.geo.lon.s))
            else:
                print("{0}d{1}'{2}''S {3}d{4}'%.2f''W\n".format(-self.geo.lat.d, self.geo.lat.m, self.geo.lat.s,
                                                                -self.geo.lon.d, self.geo.lon.m, self.geo.lon.s))

    def print_cart(self):
        print('X={0},Y={1},Z={2}\n'.format(self.cart.x, self.cart.y, self.cart.z))


def r2dd(r):
    return r*180/np.pi


def r2dms(r):
    dd = r*180/np.pi
    if dd >= 0:
        d = np.floor(dd)
    else:
        d = np.ceil(dd)
    m = np.floor(np.abs((dd-d))*60)
    s = (np.abs(dd-d)-m/60)*3600
    return d, m, s


def dd2r(dd):
    return dd/180*np.pi


def dd2dms(dd):
    if dd >= 0:
        d = np.floor(dd)
    else:
        d = np.ceil(dd)
    m = np.floor(np.abs((dd-d))*60)
    s = (np.abs(dd-d)-m/60)*3600
    return d, m, s


def dms2dd(d, m, s):
    dd = np.abs(d)+m/60+s/3600
    if d < 0:
        dd = -dd
    return dd


def dms2r(d, m, s):
    r = (np.abs(d)+m/60+s/3600)*np.pi/180
    if d < 0:
        r = -r
    return r


def dist(p1, p2):
    return np.sqrt(np.power(p1.cart.x-p2.cart.x, 2)+np.power(p1.cart.y-p2.cart.y, 2)+np.power(p1.cart.z-p2.cart.z, 2))


def cart2geo(cart):
    a = 6378137
    f = 1/298.257223563
    b = a*(1-f)
    p = np.sqrt(np.power(cart.x, 2)+np.power(cart.y, 2))
    e2 = 1-np.power(b, 2)/np.power(a, 2)
    el2 = np.power(a, 2)/np.power(b, 2)-1
    beta = np.arctan(a*cart.z/(b*p))
    if cart.y >= 0:
        lon = np.pi/2-2*np.arctan(cart.x/(np.sqrt((np.power(cart.x, 2)+np.power(cart.y, 2)))+cart.y))
    else:
        lon = -np.pi/2+2*np.arctan(cart.x/(np.sqrt((np.power(cart.x, 2)+np.power(cart.y, 2)))-cart.y))
    lat = np.arctan((cart.z+el2*b*np.power(np.sin(beta), 3))/(p-e2*a*np.power(np.cos(beta), 3)))
    rn = a/np.sqrt(1-e2*np.power(np.sin(lat), 2))
    alt = p*np.cos(lat)+cart.z*np.sin(lat)-np.power(a, 2)/rn
    return lat, lon, alt


def geo2cart(geo):
    a = 6378137
    f = 1/298.257223563
    rn = a/np.sqrt(1-f*(2-f)*np.power(np.sin(geo.lat.r), 2))
    x = (rn+geo.alt)*np.cos(geo.lat.r)*np.cos(geo.lon.r)
    y = (rn+geo.alt)*np.cos(geo.lat.r)*np.sin(geo.lon.r)
    z = (np.power((1 - f), 2)*rn+geo.alt)*np.sin(geo.lat.r)
    return x, y, z


def rotx(a):
    m = np.array([[1, 0, 0],
                  [0, np.cos(a), -np.sin(a)],
                  [0, np.sin(a), np.cos(a)]])
    return m


def roty(a):
    m = np.array([[np.cos(a), 0, np.sin(a)],
                  [0, 1, 0],
                  [-np.sin(a), 0, np.cos(a)]])
    return m


def rotz(a):
    m = np.array([[np.cos(a), -np.sin(a), 0],
                  [np.sin(a), np.cos(a), 0],
                  [0, 0, 1]])
    return m


def ecef2enu(p1, p2):
    ecef = np.array([p2.cart.x-p1.cart.x, p2.cart.y-p1.cart.y, p2.cart.z-p1.cart.z])
    a = np.dot(rotz(p1.geo.lon.r+np.pi/2),rotx(np.pi/2-p1.geo.lat.r))
    return np.dot(ecef, a)


def azimuth_elevation(p1, p2):
    enu = ecef2enu(p1, p2)
    az = np.arctan2(enu[0], enu[1])*180/np.pi
    el = np.arctan2(enu[2], np.sqrt(np.power(enu[1], 2)+np.power(enu[0], 2)))*180/np.pi
    if az < 0:
        az += 360
    return az, el


def read_nav_aids(file_name):
    with open(file_name) as f:
        data = f.readlines()
    nav_aids = []
    for du in data[0:]:
        d = du.split(',')
        if d[0] == 'VOR-DME':
            id_ = d[1]
            lat = dms2dd(float(d[2]), float(d[3]), float(d[4]))
            lon = dms2dd(float(d[5]), float(d[6]), float(d[7]))
            alt = float(d[8])+float(d[9])
            range_ = float(d[10])
            name = d[11]
            nav_aids.append(VORDME(id_, lat, lon, alt, range_, name))
    return nav_aids
