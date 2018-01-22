import sys
import math
import pygame
import threading
import time
import numpy as np
from socket import *
from pygame.locals import *
pygame.init()
tLock = threading.Lock()
shutdown = False
TEST = True

# initialize variables
roll_data = 20.0
pitch_data = 25.0
yaw_data = 90.0
dme_1_data = '124.2'
dme_2_data = 'NAV'
az_data = 145.0
radial_ref = 120.0/180*np.pi
diff_data = az_data - radial_ref*180/np.pi
heading_rotate_airplane = False
TO_FLAG = True
MAX_SCALE = 50.0
MAX_ROLL = 30.0
MIN_ROLL = -30.0
MAX_PITCH = 20.0
MIN_PITCH = -20.0
VOR_NAV = False
WARNING_PULL_UP = False
WARNING_PULL_DOWN = False
WARNING_ROLL_RIGHT = False
WARNING_ROLL_LEFT = False

if TEST:
    # self IP
    localhost = '127.0.0.1'
    ip_int, port_int_gui, port_int_indicators = localhost, 5011, 5012
else:
    # Self IP when connected via LAN
    ip_int, port_int_gui, port_int_indicators = '10.0.0.3', 5011, 5012


def receiving(name, sock):
    """
    Function to run when the thread is activated
    """
    global roll_data, pitch_data, yaw_data, dme_1_data, dme_2_data, az_data, diff_data, TO_FLAG, \
        heading_rotate_airplane, VOR_NAV, MAX_ROLL, MIN_ROLL, MAX_PITCH, MIN_PITCH, MAX_SCALE
    while not shutdown:
        try:
            while True:
                data_, addr = sock.recvfrom(1024)
                print data_, addr
                if addr == (ip_int, port_int_gui):
                    data_ = data_.decode('utf-8')
                    print 'received:', data_, '  from:', addr
                    data = str(data_).split()
                    if data[0] == 'ROLL':
                        roll_data = float(data[1])
                        pass
                    elif data[0] == 'PITCH':
                        pitch_data = float(data[1])
                        pass
                    elif data[0] == 'YAW':
                        yaw_data = float(data[1])
                        pass
                    elif data[0] == 'AZ':
                        if data[2] == 'NAV':
                            az_data = float(data[1])
                            VOR_NAV = True
                        else:
                            az_data = float(data[1])
                            VOR_NAV = False
                        diff_data = az_data - radial_ref*180/np.pi
                        if np.abs(diff_data) > 180:
                            if diff_data < 0:
                                diff_data = 360 + diff_data
                            else:
                                diff_data = diff_data - 360
                        if 90 < np.abs(diff_data):
                            TO_FLAG = True
                            if diff_data > 0:
                                diff_data = diff_data - 180
                            else:
                                diff_data = diff_data + 180
                        else:
                            TO_FLAG = False
                            diff_data = -diff_data
                        print 'radial', radial_ref
                        print 'diff data:', diff_data
                    elif data[0] == 'DME1':
                        dme_1_data = data[1]
                        pass
                    elif data[0] == 'DME2':
                        dme_2_data = data[1]
                        pass
                    elif data[0] == 'FIX':
                        if data[1] == 'W':
                            heading_rotate_airplane = True
                        elif data[1] == 'A':
                            heading_rotate_airplane = False
                    elif data[0] == 'MAX_ROLL':
                        MAX_ROLL = float(data[1])
                        pass
                    elif data[0] == 'MIN_ROLL':
                        MIN_ROLL = float(data[1])
                        pass
                    elif data[0] == 'MAX_PITCH':
                        MAX_PITCH = float(data[1])
                        pass
                    elif data[0] == 'MIN_PITCH':
                        MIN_PITCH = float(data[1])
                        pass
                    elif data[0] == 'MAX_SCALE':
                        MAX_SCALE = float(data[1])
                        pass
        except:
            pass


def internal_comm():
    """
    Function to setup the internal communication with gui.py
    """
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind((ip_int, port_int_indicators))
    s.setblocking(0)
    return s


def button_func(cx, cy, angle, total_rotation):
    """Function to deal with the button rotation"""
    mx, my = pygame.mouse.get_pos()
    new_angle = np.arctan2(- my + cy, mx - cx)
    if new_angle < 0:
        new_angle += 2 * np.pi

    if 3 * np.pi / 2 <= angle < 2 * np.pi:
        if 0 <= new_angle < np.pi / 2:
            rotation = new_angle + 2 * np.pi - angle
        else:
            rotation = new_angle - angle
    elif 0 <= angle < np.pi / 2:
        if 3 * np.pi / 2 <= new_angle < 2 * np.pi:
            rotation = 2 * np.pi - (new_angle - angle)
        else:
            rotation = new_angle - angle
    else:
        rotation = new_angle - angle

    angle = new_angle
    total_rotation += rotation
    return angle, total_rotation, rotation


# classes for indicators
class Dial:
    """
    Generic dial type.
    """
    def __init__(self, image, frameImage, x=0, y=0, w=0, h=0):
        """
        x,y = coordinates of top left of dial.
        w,h = Width and Height of dial.
        """
        self.x = x
        self.y = y
        self.image = image
        self.frameImage = frameImage
        self.dial = pygame.Surface(self.frameImage.get_rect()[2:4])
        self.dial.fill(0xFFFF00)
        if(w==0):
          w = self.frameImage.get_rect()[2]
        if(h==0):
          h = self.frameImage.get_rect()[3]
        self.w = w
        self.h = h
        self.pos = self.dial.get_rect()
        self.pos = self.pos.move(x, y)

    def position(self, x, y):
        """
        Reposition top,left of dial at x,y.
        """
        self.x = x
        self.y = y
        self.pos[0] = x
        self.pos[1] = y

    def position_center(self, x, y):
        """
        Reposition centre of dial at x,y.
        """
        self.x = x
        self.y = y
        self.pos[0] = x - self.pos[2]/2
        self.pos[1] = y - self.pos[3]/2

    def rotate(self, image, angle):
        """
        Rotate supplied image by "angle" degrees.
        This rotates round the centre of the image.
        If you need to offset the centre, resize the image using self.clip.
        This is used to rotate dial needles and probably doesn't need to be used externally.
        """
        tmpImage = pygame.transform.rotate(image, angle)
        imageCentreX = tmpImage.get_rect()[0] + tmpImage.get_rect()[2]/2
        imageCentreY = tmpImage.get_rect()[1] + tmpImage.get_rect()[3]/2

        targetWidth = tmpImage.get_rect()[2]
        targetHeight = tmpImage.get_rect()[3]

        imageOut = pygame.Surface((targetWidth, targetHeight))
        imageOut.fill(0xFFFF00)
        imageOut.set_colorkey(0xFFFF00)
        imageOut.blit(tmpImage, (0, 0), pygame.Rect( imageCentreX-targetWidth/2, imageCentreY-targetHeight/2, targetWidth, targetHeight))
        return imageOut

    def clip(self, image, x=0, y=0, w=0, h=0, oX=0, oY=0):
        """
        Cuts out a part of the needle image at x,y position to the correct size (w,h).
        This is put on to "imageOut" at an offset of oX,oY if required.
        This is used to centre dial needles and probably doesn't need to be used externally.
        """
        if(w == 0):
            w = image.get_rect()[2]
        if(h == 0):
            h = image.get_rect()[3]
        needleW = w + 2*math.sqrt(oX*oX)
        needleH = h + 2*math.sqrt(oY*oY)
        imageOut = pygame.Surface((needleW, needleH))
        imageOut.fill(0xFFFF00)
        imageOut.set_colorkey(0xFFFF00)
        imageOut.blit(image, (needleW/2-w/2+oX, needleH/2-h/2+oY), pygame.Rect(x, y, w, h))
        return imageOut

    def overlay(self, image, x, y, r=0):
        """
        Overlays one image on top of another using 0xFFFF00 (Yellow) as the overlay colour.
        """
        x -= (image.get_rect()[2] - self.dial.get_rect()[2])/2
        y -= (image.get_rect()[3] - self.dial.get_rect()[3])/2
        image.set_colorkey(0xFFFF00)
        self.dial.blit(image, (x, y))


class Horizon(Dial):
    """
    Artificial horizon dial.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.image = pygame.image.load('cockpit/resources/Horizon_GroundSky.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/Horizon_Background.png').convert()
        self.maquetteImage = pygame.image.load('cockpit/resources/Maquette_Avion.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, angleX, angleY):
        """
        Called to update an Artificial horizon dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        global WARNING_PULL_UP, WARNING_PULL_DOWN, WARNING_ROLL_RIGHT, WARNING_ROLL_LEFT
        angleX %= 360
        angleY %= 360
        if angleX > 180:
            angleX -= 360
        if 90 < angleY < 270:
            angleY = 180 - angleY
        elif angleY > 270:
            angleY -= 360

        WARNING_PULL_UP = False
        WARNING_PULL_DOWN = False
        WARNING_ROLL_RIGHT = False
        WARNING_ROLL_LEFT = False

        # Test if the roll and pitch angles are in the limits
        if angleX > MAX_ROLL:
            WARNING_ROLL_LEFT = True
        elif angleX < MIN_ROLL:
            WARNING_ROLL_RIGHT = True

        if angleY < MIN_PITCH:
            WARNING_PULL_UP = True
        elif angleY > MAX_PITCH:
            WARNING_PULL_DOWN = True

        dim_1_ = self.image.get_rect()
        dim_1 = dim_1_[3]/180
        tmpImage = self.clip(self.image, 0, -angleY*dim_1,  dim_1_[2],  dim_1_[3])
        tmpImage = self.rotate(tmpImage, angleX)
        self.overlay(tmpImage, 0, 0)
        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.maquetteImage, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class Warning_pitch(Dial):
    """
    Dial for the Pitch Warning indication.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.image = pygame.image.load('cockpit/resources/warning_background_pitch.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/warning_background_pitch.png').convert()
        self.warning_pull_up = pygame.image.load('cockpit/resources/warning_pull_up.png').convert()
        self.warning_pull_down = pygame.image.load('cockpit/resources/warning_pull_down.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen):
        """
        Called to update an Artificial horizon dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """

        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.image, 0, 0)
        if WARNING_PULL_UP is True:
            self.overlay(self.warning_pull_up, 0, 0)
        elif WARNING_PULL_DOWN is True:
            self.overlay(self.warning_pull_down, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class Warning_roll(Dial):
    """
    Dial for the Roll Warning indication.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.image = pygame.image.load('cockpit/resources/warning_background_roll.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/warning_background_roll.png').convert()
        self.warning_roll_right = pygame.image.load('cockpit/resources/warning_roll_right.png').convert()
        self.warning_roll_left = pygame.image.load('cockpit/resources/warning_roll_left.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen):
        """
        Called to update an Artificial horizon dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """

        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.image, 0, 0)
        if WARNING_ROLL_RIGHT is True:
            self.overlay(self.warning_roll_right, 0, 0)
        elif WARNING_ROLL_LEFT is True:
            self.overlay(self.warning_roll_left, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class Heading_1(Dial):
    """
    Heading dial for fixed airplane (rotate scale).
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.frameImage = pygame.image.load('cockpit/resources/HeadingIndicator_Background.png').convert()
        self.image = pygame.image.load('cockpit/resources/HeadingIndicator_Aircraft.png').convert()
        self.weel = pygame.image.load('cockpit/resources/HeadingWeel.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, heading):
        """
        Called to update a Heading dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        heading %= 360
        if heading > 180:
           heading -= 360
        tmpImage = self.weel
        tmpImage = self.rotate(tmpImage, heading)
        self.overlay(self.frameImage, 0,0)
        self.overlay(self.image, 0, 0)
        self.overlay(tmpImage, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit( pygame.transform.scale(self.dial,(self.w,self.h)), self.pos )


class Heading_2(Dial):
    """
    Heading dial for fixed scale (rotate airplane).
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.frameImage = pygame.image.load('cockpit/resources/HeadingIndicator_Background.png').convert()
        self.image = pygame.image.load('cockpit/resources/HeadingIndicator_Aircraft.png').convert()
        self.weel = pygame.image.load('cockpit/resources/HeadingWeel.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, heading):
        """
        Called to update a Heading dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        heading = -heading
        heading %= 360
        if heading > 180:
            heading -= 360
        tmpImage = self.image
        tmpImage = self.rotate(tmpImage, heading)
        self.overlay(self.frameImage, 0, 0)
        self.overlay(tmpImage, 0, 0)
        self.overlay(self.weel, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class VOR(Dial):
    """
    VOR dial.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        """
        self.image = pygame.image.load('cockpit/resources/VOR_weel.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/VOR_background.png').convert()
        self.back_2 = pygame.image.load('cockpit/resources/VOR_background_2.png').convert()
        self.points = pygame.image.load('cockpit/resources/points.png').convert()
        self.line = pygame.image.load('cockpit/resources/line.png').convert()
        self.line_red = pygame.image.load('cockpit/resources/line_red.png').convert()
        self.to = pygame.image.load('cockpit/resources/to.png').convert()
        self.to_red = pygame.image.load('cockpit/resources/to_red.png').convert()
        self.from_ = pygame.image.load('cockpit/resources/from.png').convert()
        self.from_red = pygame.image.load('cockpit/resources/from_red.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, heading, diff__):
        """
        Called to update a Generic dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        max_scale = MAX_SCALE
        if diff__ < -max_scale:
            diff__ = -max_scale
        elif diff__ > max_scale:
            diff__ = max_scale

        d = np.abs(diff__)
        if d < max_scale/5:
            d = d*20/(max_scale/5)
        else:
            d = 20+15*(d-max_scale/5)/(max_scale/5)
        if diff__ < 0:
            d = -d

        tmpImage = self.image
        tmpImage = self.rotate(tmpImage, heading)
        tmpImage_2 = self.clip(self.line, d, 0, 0, 0)
        tmpImage_2_red = self.clip(self.line_red, d, 0, 0, 0)
        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.points, 0, 0)
        self.overlay(tmpImage_2, 0, 0)
        if TO_FLAG is True:
            self.overlay(self.to, 0, 0)
        else:
            self.overlay(self.from_, 0, 0)
        if VOR_NAV is True:
            self.overlay(self.from_red, 0, 0)
            self.overlay(self.to_red, 0, 0)
            self.overlay(tmpImage_2_red, 0, 0)
        self.overlay(tmpImage, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class VOR_azimute(Dial):
    """
    Azimute dial.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        """
        self.image = pygame.image.load('cockpit/resources/LongNeedleAltimeter.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/VOR_background_1.png').convert()
        self.weel = pygame.image.load('cockpit/resources/VOR_weel.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, heading):
        """
        Called to update a Generic dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        tmpImage = self.clip(self.image, 0, 0, 0, 0, 0, -37)
        tmpImage = self.rotate(tmpImage, heading)
        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.weel, 0, 0)
        self.overlay(tmpImage, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class DME(Dial):
    """
    DME dial.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        """
        self.image = pygame.image.load('cockpit/resources/VOR_background_2.png').convert()
        self.frameImage = pygame.image.load('cockpit/resources/VOR_background_2.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen):
        """
        Called to update a Generic dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """

        self.overlay(self.frameImage, 0, 0)
        self.overlay(self.image, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


class Button(Dial):
    """
    Button dial.
    """
    def __init__(self, x=0, y=0, w=0, h=0):
        """
        Initialise dial at x,y.
        Default size of 300px can be overidden using w,h.
        """
        self.frameImage = pygame.image.load('cockpit/resources/button.png').convert()
        self.image = pygame.image.load('cockpit/resources/button.png').convert()
        Dial.__init__(self, self.image, self.frameImage, x, y, w, h)

    def update(self, screen, rotation):
        """
        Called to update a Heading dial.
        "angleX" and "angleY" are the inputs.
        "screen" is the surface to draw the dial on.
        """
        tmpImage = self.image
        tmpImage = self.rotate(tmpImage, rotation)
        self.dial.fill(0xFFFF00)
        self.overlay(tmpImage, 0, 0)
        self.dial.set_colorkey(0xFFFF00)
        screen.blit(pygame.transform.scale(self.dial, (self.w, self.h)), self.pos)


def main():
    global shutdown, radial_ref, heading_rotate_airplane

    # Indicators positions
    total_x = 1350
    total_y = 470
    vor_az_pos_x = 20
    vor_az_pos_y = 120
    vor_pos_x = vor_az_pos_x + 320
    vor_pos_y = 120
    heading_pos_x = vor_pos_x + 320
    heading_pos_y = 120
    horizon_pos_x = heading_pos_x + 320 + 50
    horizon_pos_y = 120
    button_pos_x = vor_pos_x + 11
    button_pos_y = vor_pos_y + 232
    warning_pitch_x = horizon_pos_x
    warning_pitch_y = horizon_pos_y - 50
    warning_roll_x = horizon_pos_x - 50
    warning_roll_y = horizon_pos_y


    # colors
    RED = (255, 0, 0)
    WHITE = (255, 255, 255)

    # Initialize screen.
    screen = pygame.display.set_mode((total_x, total_y))
    screen.fill(0x222222)

    # Initialize Dials.
    horizon_dial = Horizon(horizon_pos_x, horizon_pos_y)
    heading_1_dial_fix_a = Heading_1(heading_pos_x, heading_pos_y)
    heading_2_dial_fix_w = Heading_2(heading_pos_x, heading_pos_y)
    vor_dial = VOR(vor_pos_x, vor_pos_y)
    vor_az_dial = VOR_azimute(vor_az_pos_x, vor_az_pos_y)
    dme_dial = DME(vor_pos_x, vor_pos_y-50)
    warning_pitch_dial = Warning_pitch(warning_pitch_x, warning_pitch_y)
    warning_roll_dial = Warning_roll(warning_roll_x, warning_roll_y)

    # Get images dimensions
    horizon_dim = horizon_dial.frameImage.get_rect()
    heading_dim_fix_a = heading_1_dial_fix_a.frameImage.get_rect()
    heading_dim_fix_w = heading_2_dial_fix_w.frameImage.get_rect()
    vor_dim = vor_dial.frameImage.get_rect()
    vor_az_dim = vor_az_dial.frameImage.get_rect()
    button_dial = Button(button_pos_x, button_pos_y)

    # Initialize fonts
    pygame.font.init()
    default_font = pygame.font.get_default_font()
    font_size = 30
    font_size_dme = 25
    font_size_dme_title = 20
    font_renderer = pygame.font.Font(default_font, font_size)
    font_renderer_dme = pygame.font.Font(default_font, font_size_dme)
    font_renderer_dme_title = pygame.font.Font(default_font, font_size_dme_title)

    # Create Labels
    horizon_title = font_renderer.render("HORIZON", 1, WHITE)
    heading_title = font_renderer.render("HEADING", 1, WHITE)
    vor_title = font_renderer.render("VOR", 1, WHITE)
    vor_az_title = font_renderer.render("AZIMUTE", 1, WHITE)
    dme_1_title = font_renderer_dme_title.render("DME1", 1, WHITE)
    dme_2_title = font_renderer_dme_title.render("DME2", 1, WHITE)

    # Get labels dimensions
    horizon_title_width, horizon_title_height = font_renderer.size("HORIZON")
    heading_title_width, heading_title_height = font_renderer.size("HEADING")
    vor_title_width, vor_title_height = font_renderer.size("VOR")
    vor_az_title_width, vor_az_title_height = font_renderer.size("AZIMUTE")
    dme_1_width, dme_1_title_height = font_renderer_dme.size("000.0")
    dme_2_width, dme_2_title_height = font_renderer_dme.size("000.0")
    dme_1_title_width, dme_1_title_height = font_renderer_dme_title.size("DME1")
    dme_2_title_width, dme_2_title_height = font_renderer_dme_title.size("DME2")

    # Define labels positions
    horizon_title_pos_x = horizon_pos_x+horizon_dim[2]/2-horizon_title_width/2
    horizon_title_pos_y = horizon_pos_y-horizon_title_height - 50
    vor_title_pos_x = vor_pos_x+vor_dim[2]/2-vor_title_width/2
    vor_title_pos_y = vor_pos_y-vor_title_height - 50
    vor_az_title_pos_x = vor_az_pos_x+vor_az_dim[2]/2-vor_az_title_width/2
    vor_az_title_pos_y = vor_az_pos_y-vor_az_title_height
    dme_1_pos_x = vor_pos_x + 18
    dme_1_pos_y = horizon_title_pos_y-2 + 50
    dme_2_pos_x = vor_pos_x+300-dme_2_width-18
    dme_2_pos_y = horizon_title_pos_y-2 + 50
    dme_1_title_pos_x = dme_1_pos_x+dme_1_width/2-dme_1_title_width/2
    dme_1_title_pos_y = vor_pos_y-dme_1_title_height - 46
    dme_2_title_pos_x = dme_2_pos_x+dme_2_width/2-dme_2_title_width/2
    dme_2_title_pos_y = vor_pos_y-dme_2_title_height - 46

    # Setup internal communication
    s = internal_comm()
    rT = threading.Thread(target=receiving, args=("RecvThread", s))
    rT.start()

    # Initialize data for button function
    br, bx, by = 27, button_pos_x, button_pos_y
    cx = button_pos_x + 30
    cy = button_pos_y + 30
    radius = np.power(br, 2)
    button_pressed = False
    total_rotation = 0

    # Main program loop.
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                # In case the program is ended by user, exit safely
                print("Exiting....")
                shutdown = True
                rT.join()
                s.close()
                sys.exit()   # end program.

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Deal with the mouse position, when button is rotated
                mx, my = pygame.mouse.get_pos()
                print 'm', mx, my
                r = np.power((cx - mx), 2) + np.power((cy - my), 2)
                print 'r', r, radius
                if r <= radius:
                    initial_angle = np.arctan2(- my + cy, mx - cx)
                    if initial_angle < 0:
                        initial_angle += 2 * np.pi
                    angle = initial_angle
                    button_pressed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                # Deal with the mouse position, when button is rotated
                button_pressed = False
                total_rotation = 0

        # Deal with the button rotation
        if button_pressed is True:
            angle, total_rotation, rotation = button_func(cx, cy, angle, total_rotation)
            radial_ref = -angle

        # Set colors for Not AVailable DME
        if dme_1_data == 'NAV':
            color_dme1 = RED
            w_, h_ = font_renderer_dme.size('NAV')
            dme_1_pos_x_ = dme_1_pos_x + dme_1_width/2-w_/2
        else:
            color_dme1 = WHITE
            dme_1_pos_x_ = dme_1_pos_x
        if dme_2_data == 'NAV':
            color_dme2 = RED
            w_, h_ = font_renderer_dme.size('NAV')
            dme_2_pos_x_ = dme_2_pos_x + dme_2_width/2-w_/2
        else:
            color_dme2 = WHITE
            dme_2_pos_x_ = dme_2_pos_x
        dme_1_text = font_renderer_dme.render(dme_1_data, 1, color_dme1)
        dme_2_text = font_renderer_dme.render(dme_2_data, 1, color_dme2)

        # Update screen with new data
        screen.fill(0x222222)
        screen.blit(dme_1_text, (dme_1_pos_x_, dme_1_pos_y))
        screen.blit(dme_2_text, (dme_2_pos_x_, dme_2_pos_y))
        screen.blit(horizon_title, (horizon_title_pos_x, horizon_title_pos_y))
        # Choose the hading indicator mode
        if not heading_rotate_airplane:
            screen.blit(heading_title, (heading_pos_x+heading_dim_fix_a[2]/2-heading_title_width/2, heading_pos_y-heading_title_height))
        else:
            screen.blit(heading_title, (heading_pos_x+heading_dim_fix_w[2]/2-heading_title_width/2, heading_pos_y-heading_title_height))
        screen.blit(vor_title, (vor_title_pos_x, vor_title_pos_y))
        screen.blit(vor_az_title, (vor_az_title_pos_x, vor_az_title_pos_y))
        screen.blit(dme_1_title, (dme_1_title_pos_x, dme_1_title_pos_y))
        screen.blit(dme_2_title, (dme_2_title_pos_x, dme_2_title_pos_y))

        # Internal communication data processing
        tLock.acquire()
        tLock.release()
        time.sleep(0.2)

        # Update dials.
        horizon_dial.update(screen, roll_data, pitch_data)
        if not heading_rotate_airplane:
            heading_1_dial_fix_a.update(screen, yaw_data)
        else:
            heading_2_dial_fix_w.update(screen, yaw_data)
        vor_dial.update(screen, -radial_ref*180/np.pi, -diff_data)
        vor_az_dial.update(screen, -az_data)
        dme_dial.update(screen)
        button_dial.update(screen, -radial_ref*180/np.pi)
        warning_pitch_dial.update(screen)
        warning_roll_dial.update(screen)

        pygame.display.update()

    pass


if __name__ == '__main__':
    main()
