# Crying Mirror by Alenka Dmitrović && Goran Mahovlić


import Image
import pygame
import RPi.GPIO as GPIO            # import RPi.GPIO module  
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import sys
import imutils

from pygame.locals import *
GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD  
GPIO.setup(24, GPIO.OUT)           # set GPIO24 as an output   

GPIO.output(24, 1)

class GIFImage(object):
    def __init__(self, filename):
        self.filename = filename
        self.image = Image.open(filename)
        self.frames = []
        self.get_frames()

        self.cur = 0
        self.ptime = time.time()

        self.running = True
        self.breakpoint = len(self.frames)-1
        self.startpoint = 0
        self.reversed = False

    def get_rect(self):
        return pygame.rect.Rect((0,0), self.image.size)

    def get_frames(self):
        image = self.image

        pal = image.getpalette()
        base_palette = []
        for i in range(0, len(pal), 3):
            rgb = pal[i:i+3]
            base_palette.append(rgb)

        all_tiles = []
        try:
            while 1:
                if not image.tile:
                    image.seek(0)
                if image.tile:
                    all_tiles.append(image.tile[0][3][0])
                image.seek(image.tell()+1)
        except EOFError:
            image.seek(0)

        all_tiles = tuple(set(all_tiles))

        try:
            while 1:
                try:
                    duration = image.info["duration"]
                except:
                    duration = 10

                duration *= .001 #convert to milliseconds!
                cons = False

                x0, y0, x1, y1 = (0, 0) + image.size
                if image.tile:
                    tile = image.tile
                else:
                    image.seek(0)
                    tile = image.tile
                if len(tile) > 0:
                    x0, y0, x1, y1 = tile[0][1]

                if all_tiles:
                    if all_tiles in ((6,), (7,)):
                        cons = True
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i+3]
                            palette.append(rgb)
                    elif all_tiles in ((7, 8), (8, 7)):
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i+3]
                            palette.append(rgb)
                    else:
                        palette = base_palette
                else:
                    palette = base_palette

                pi = pygame.image.fromstring(image.tostring(), image.size, image.mode)
                pi.set_palette(palette)
                if "transparency" in image.info:
                    pi.set_colorkey(image.info["transparency"])
                pi2 = pygame.Surface(image.size, SRCALPHA)
                if cons:
                    for i in self.frames:
                        pi2.blit(i[0], (0,0))
                pi2.blit(pi, (x0, y0), (x0, y0, x1-x0, y1-y0))

                self.frames.append([pi2, duration])
                image.seek(image.tell()+1)
        except EOFError:
            pass

    def render(self, screen, pos):
        if self.running:
            if time.time() - self.ptime > self.frames[self.cur][1]:
                if self.reversed:
                    self.cur -= 1
                    if self.cur < self.startpoint:
                        self.cur = self.breakpoint
                else:
                    self.cur += 1
                    if self.cur > self.breakpoint:
                        self.cur = self.startpoint

                self.ptime = time.time()

        screen.blit(self.frames[self.cur][0], pos)

    def seek(self, num):
        self.cur = num
        if self.cur < 0:
            self.cur = 0
        if self.cur >= len(self.frames):
            self.cur = len(self.frames)-1

    def set_bounds(self, start, end):
        if start < 0:
            start = 0
        if start >= len(self.frames):
            start = len(self.frames) - 1
        if end < 0:
            end = 0
        if end >= len(self.frames):
            end = len(self.frames) - 1
        if end < start:
            end = start
        self.startpoint = start
        self.breakpoint = end

    def pause(self):
        self.running = False

    def play(self):
        self.running = True

    def rewind(self):
        self.seek(0)
    def fastforward(self):
        self.seek(self.length()-1)

    def get_height(self):
        return self.image.size[1]
    def get_width(self):
        return self.image.size[0]
    def get_size(self):
        return self.image.size
    def length(self):
        return len(self.frames)
    def reverse(self):
        self.reversed = not self.reversed
    def reset(self):
        self.cur = 0
        self.ptime = time.time()
        self.reversed = False

    def copy(self):
        new = GIFImage(self.filename)
        new.running = self.running
        new.breakpoint = self.breakpoint
        new.startpoint = self.startpoint
        new.cur = self.cur
        new.ptime = self.ptime
        new.reversed = self.reversed
        return new

# Get user supplied values
cascPath = sys.argv[1]

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (160, 128)
camera.framerate = 5
rawCapture = PiRGBArray(camera, size=(160, 128))

# allow the camera to warmup
time.sleep(0.1)
lastTime = time.time()*1000.0
# capture frames from the camera

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 480))
    pygame.mouse.set_visible(0)
    cry = GIFImage("/home/pi/cryingMirror/cry.gif")


    while 1:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
		#GPIO.cleanup()
		GPIO.output(24, 1) 
                return



        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            # grab the raw NumPy array representing the image, then initialize the timestamp
            # and occupied/unoccupied text
            image = frame.array
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
            # Detect faces in the image
            faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(2, 2),
            flags = cv2.cv.CV_HAAR_SCALE_IMAGE
            )
            # print time.time()*1000.0-lastTime," Found {0} faces!".format(len(faces))
            # lastTime = time.time()*1000.0
            # Draw a rectangle around the faces
            # for (x, y, w, h) in faces:
            #      cv2.circle(image, (x+w/2, y+h/2), int((w+h)/3), (255, 255, 255), 1)
            # show the frame
            #    cv2.imshow("Frame", image)
            key = cv2.waitKey(1) & 0xFF
 
            # clear the stream in preparation for the next frame
            rawCapture.truncate(0)
            
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
		#GPIO.cleanup()
		GPIO.output(24, 1)
                break

            if ((len(faces)) > 0):
		screen.fill((0,0,0))
                GPIO.output(24, 0)         # set GPIO24 to 0/GPIO.LOW/False
		timestr = time.strftime("%Y%m%d-%H%M%S")
		cv2.imwrite("/var/www/cryingMirror/" + timestr + ".png",image)
            else:
		cry.render(screen, (0, 0))
		GPIO.output(24, 1)         # set GPIO24 to 1/GPIO.HIGH/True  
            pygame.display.flip()

if __name__ == "__main__":
    main()



        
  
        

