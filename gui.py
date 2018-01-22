import Tkinter as tk
from socket import *
import threading
import utils
import time
tLock = threading.Lock()
shutdown = False
TEST = True

# file with the VOR/DME information
file_name = 'vor-dme.csv'
# read file
nav_aids = utils.read_nav_aids(file_name)

if TEST:
    # self IP
    ip_group_1, port_group_1 = '127.0.0.1', 5013
    ip_group_2, port_group_2 = '127.0.0.1', 5014
    ip_int, port_int_gui, port_int_indicators = 'localhost', 5011, 5012
    ip_ext, port_ext = '127.0.0.1', 5004
else:
    # Set the other groups IP addresses
    ip_group_1, port_group_1 = '10.0.0.1', 5003
    ip_group_2, port_group_2 = '10.0.0.2', 12345
    # self IP when connected via LAN for internal communication with "indicators.py"
    ip_int, port_int_gui, port_int_indicators = '10.0.0.3', 5011, 5012
    # self IP when connected via LAN for external communication with the other groups
    ip_ext, port_ext = '10.0.0.3', 5004


# Initializae variables
current_station_dme_1 = 'NO_DME_1'
current_station_dme_2 = 'NO_DME_2'
current_station_vor = 'NO_VOR'
current_fix_heading = True
VOR_MIN_RANGE = 0.5                     # [NM]
MAX_SCALE, MAX_SCALE_ = 50.0, 50.0      # [deg]
MAX_ROLL, MAX_ROLL_ = 50.0, 50.0        # [deg]
MIN_ROLL, MIN_ROLL_ = -50.0, -50.0      # [deg]
MAX_PITCH, MAX_PITCH_ = 20.0, 20.0      # [deg]
MIN_PITCH, MIN_PITCH_ = -20.0, -20.0    # [deg]
VOR_NAV = True
PRINT = True


def receiving(name, sock):
    """
    Function to run when the thread is activated
    """
    while not shutdown:
        try:
            while True:
                data_, addr = sock.recvfrom(1024)
                data_ = data_.decode('utf-8')
                data_ = data_[:-1]   # ???
                if PRINT:
                    print ('data received:', data_)
                    print ('from:', addr, '\n')
                # check if the data received is from group 2
                if addr == (ip_group_2, port_group_2):
                    # data format: "float(roll),float(pitch),float(yaw)"    [deg]
                    data = data_.split(',')
                    yaw = data[0]
                    pitch = data[1]
                    roll = data[2]
                    message = 'ROLL ' + str(roll)
                    s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                    message = 'PITCH ' + str(pitch)
                    s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                    message = 'YAW ' + str(yaw)
                    s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                # check if the data received is from group 1
                elif addr == (ip_group_1, port_group_1):
                    # data format: "float(lat);float(lon);float(alt)"    [wgs84] [deg]
                    data = data_.split(';')
                    lat = float(data[7])
                    lon = float(data[8])
                    alt = float(data[9])
                    pos_aviao = utils.Position(lat, lon, alt, 'geo')
                    if current_station_vor != 'NO_VOR':
                        vor_dist = utils.dist(current_station_vor.pos, pos_aviao) * 0.000539956803  # distancia em nm
                        az, _ = utils.azimuth_elevation(current_station_vor.pos, pos_aviao)
                        if vor_dist > current_station_vor.range_ or vor_dist < VOR_MIN_RANGE:
                            message = 'AZ ' + str(az) + ' NAV'
                        else:
                            message = 'AZ ' + str(az) + ' AV'
                        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                        if PRINT:
                            print ('message sent:', message)
                            print ('to:', (ip_int, port_int_indicators), '\n')
                    if current_station_dme_1 != 'NO_DME_1':
                        dme_1__ = utils.dist(current_station_dme_1.pos, pos_aviao) * 0.000539956803  # distancia em nm
                        if dme_1__ > current_station_dme_1.range_:
                            dme_1 = 'NAV'
                        else:
                            dme_1 = "%05.1f" % dme_1__
                        message = 'DME1 ' + dme_1
                        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                        if PRINT:
                            print ('message sent:', message)
                            print ('to:', (ip_int, port_int_indicators), '\n')
                    if current_station_dme_2 != 'NO_DME_2':
                        dme_2__ = utils.dist(current_station_dme_2.pos, pos_aviao) * 0.000539956803  # distancia em nm
                        if dme_2__ > current_station_dme_2.range_:
                            dme_2 = 'NAV'
                        else:
                            dme_2 = "%05.1f" % dme_2__
                        message = 'DME2 ' + dme_2
                        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
                        if PRINT:
                            print ('message sent:', message)
                            print ('to:', (ip_int, port_int_indicators), '\n')
        except:
            pass


def internal_comm():
    """Setup the internal communication"""
    global s_int
    s_int = socket(AF_INET, SOCK_DGRAM)
    s_int.bind((ip_int, port_int_gui))


def external_comm():
    """Setup the external communication"""
    global s_ext
    s_ext = socket(AF_INET, SOCK_DGRAM)
    s_ext.bind((ip_ext, port_ext))
    s_ext.setblocking(0)


def opt_update_dme_1(value):
    """Function to run when a different station is selected by user for the DME 1."""
    global current_station_dme_1
    for station in nav_aids:
        if value == station.name:
            current_station_dme_1 = station
            if PRINT:
                print ('setting: current station dme1:', current_station_dme_1)


def opt_update_dme_2(value):
    """Function to run when a different station is selected by user for the DME 2."""
    global current_station_dme_2
    for station in nav_aids:
        if value == station.name:
            current_station_dme_2 = station
            if PRINT:
                print ('setting: current station dme2:', current_station_dme_2)


def opt_update_vor(value):
    """Function to run when a different station is selected by user for the VOR."""
    global current_station_vor
    for station in nav_aids:
        if value == station.name:
            current_station_vor = station
            if PRINT:
                print ('setting: current station vor:', current_station_vor)


def opt_update_fix():
    """Function to run when the user select between 'fixed airplane' and 'fixed scale'."""
    global current_fix_heading
    value = vare.get()
    if value != current_fix_heading:
        current_fix_heading = value
        if value == 0:
            message = 'FIX W'
            s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
            if PRINT:
                print ('sent:', message)
        elif value == 1:
            message = 'FIX A'
            s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
            if PRINT:
                print ('sent:', message)


def opt_udpate_send():
    """If the values in the Entry boxes are valid and different from the previous ones,
        that information is sent to the 'indicators.py'."""
    global MAX_SCALE, MAX_SCALE_, MAX_ROLL, MAX_ROLL_, MIN_ROLL, MIN_ROLL_,\
        MAX_PITCH, MAX_PITCH_, MIN_PITCH, MIN_PITCH_
    if MAX_SCALE != MAX_SCALE_:
        message = 'MAX_SCALE ' + str(MAX_SCALE_)
        MAX_SCALE = MAX_SCALE_
        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
        if PRINT:
            print ('sent:', message)
    if MAX_ROLL != MAX_ROLL_:
        MAX_ROLL = MAX_ROLL_
        message = 'MAX_ROLL ' + str(MAX_ROLL_)
        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
        if PRINT:
            print ('sent:', message)
    if MIN_ROLL != MIN_ROLL_:
        MIN_ROLL = MIN_ROLL_
        message = 'MIN_ROLL ' + str(MIN_ROLL_)
        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
        if PRINT:
            print ('sent:', message)
    if MAX_PITCH != MAX_PITCH_:
        MAX_PITCH = MAX_PITCH_
        message = 'MAX_PITCH ' + str(MAX_PITCH_)
        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
        if PRINT:
            print ('sent:', message)
    if MIN_PITCH != MIN_PITCH_:
        MIN_PITCH = MIN_PITCH_
        message = 'MIN_PITCH ' + str(MIN_PITCH_)
        s_int.sendto(message.encode('utf-8'), (ip_int, port_int_indicators))
        if PRINT:
            print ('sent:', message)


def save_button():
    """Function to run when the 'save' button is pressed by the user."""
    global MAX_ROLL_, MIN_ROLL_, MAX_PITCH_, MIN_PITCH_, VOR_MIN_RANGE, MAX_SCALE_
    if e_r_max != '':
        MAX_ROLL_ = float(e_r_max.get())
    if e_r_min != '':
        MIN_ROLL_ = float(e_r_min.get())
    if e_p_max != '':
        MAX_PITCH_ = float(e_p_max.get())
    if e_p_min != '':
        MIN_PITCH_ = float(e_p_min.get())
    if e_range_min != '':
        VOR_MIN_RANGE = float(e_range_min.get())
    if e_scale != '':
        MAX_SCALE_ = float(e_scale.get())
    opt_udpate_send()


def gui():
    """Function that creates the Graphical User Interface."""
    global current_fix_heading, vare, e_range_min, e_scale, e_r_max, e_r_min, e_p_max, e_p_min

    root = tk.Tk()

    total_width = 280
    total_height = 300

    root.geometry(str(total_width) + "x" + str(total_height))

    dme_1_label = tk.Label(root, text="DME 1:")
    dme_2_label = tk.Label(root, text="DME 2:")
    vor_label = tk.Label(root, text="VOR:")
    vor_min_label = tk.Label(root, text="Range Min [NM]:")
    vor_max_label = tk.Label(root, text="Max Scale [deg]:")
    heading_label = tk.Label(root, text="Fix in Heading:")
    roll_label = tk.Label(root, text="ROLL [deg]:")
    roll_max_label = tk.Label(root, text="MAX:")
    roll_min_label = tk.Label(root, text="MIN:")
    pitch_label = tk.Label(root, text="PITCH [deg]:")
    pitch_max_label = tk.Label(root, text="MAX:")
    pitch_min_label = tk.Label(root, text="MIN:")

    dme_1_label.place(x=10, y=20)
    dme_2_label.place(x=10, y=50)
    vor_label.place(x=10, y=80)
    vor_min_label.place(x=70, y=112)
    vor_max_label.place(x=70, y=142)
    heading_label.place(x=10, y=230)
    roll_label.place(x=10, y=172)
    roll_max_label.place(x=100, y=172)
    roll_min_label.place(x=180, y=172)
    pitch_label.place(x=10, y=200)
    pitch_max_label.place(x=100, y=202)
    pitch_min_label.place(x=180, y=202)

    e_range_min = tk.Entry(root, width=5)
    e_range_min.insert(0, "0.5")
    e_range_min.place(x=185, y=110)
    e_scale = tk.Entry(root, width=5)
    e_scale.insert(0, "50")
    e_scale.place(x=185, y=140)
    e_r_max = tk.Entry(root, width=3)
    e_r_max.insert(0, "50")
    e_r_max.place(x=138, y=170)
    e_r_min = tk.Entry(root, width=3)
    e_r_min.insert(0, "-50")
    e_r_min.place(x=214, y=170)
    e_p_max = tk.Entry(root, width=3)
    e_p_max.insert(0, "20")
    e_p_max.place(x=138, y=200)
    e_p_min = tk.Entry(root, width=3)
    e_p_min.insert(0, "-20")
    e_p_min.place(x=214, y=200)

    b = tk.Button(root, text='Save', width=10, command=save_button)
    b.place(x=80, y=260)

    variable_1 = tk.StringVar(root)
    variable_1.set("select station                ")
    variable_2 = tk.StringVar(root)
    variable_2.set("select station                ")
    variable_3 = tk.StringVar(root)
    variable_3.set("select station                ")
    vare = tk.IntVar()

    station_names = [station.name for station in nav_aids]
    option_menu_1 = tk.OptionMenu(root, variable_1, *station_names, command=opt_update_dme_1)
    option_menu_1.place(x=60, y=17)
    option_menu_2 = tk.OptionMenu(root, variable_2, *station_names, command=opt_update_dme_2)
    option_menu_2.place(x=60, y=47)
    option_menu_3 = tk.OptionMenu(root, variable_3, *station_names, command=opt_update_vor)
    option_menu_3.place(x=60, y=77)

    chkhead1 = tk.Radiobutton(root, text="Airplane", variable=vare, value=1, command=opt_update_fix)
    chkhead2 = tk.Radiobutton(root, text="Wheel", variable=vare, value=0, command=opt_update_fix)
    chkhead1.place(x=120, y=230)
    chkhead2.place(x=200, y=230)

    return root


def main():
    """Main Function."""

    global shutdown

    internal_comm()
    external_comm()
    rT = threading.Thread(target=receiving, args=("RecvThread", s_ext))
    rT.start()
    # internal comm data processing
    tLock.acquire()
    tLock.release()
    time.sleep(0.2)

    root = gui()
    root.mainloop()

    shutdown = True
    rT.join()
    s_ext.close()
    s_int.close()

    pass

if __name__ == '__main__':
    main()
