#setup commands
#sudo apt-get install python3-pil python3-pip
#sudo pip3 install adafruit-blinka adafruit-circuitpython-ssd1306 adafruit-circuitpython-mcp3xx requests
#cd /home/dietpi/ssd1306_stats
#wget http://kottke.org/plus/type/silkscreen/download/silkscreen.zip
#unzip silkscreen.zip

#enable i2c and spi

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import time
import subprocess
import busio
import logging #for logging

#for stopping the script
import sys

#for GPIO
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

#for I2C PiOLED
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

#log settings
LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.DEBUG
LOG_FILE = "/var/log/ssd1306-stats.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)
logging.info("Beginning Log File")

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)
# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

ButtonPin = 15
GPIO.setup(ButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


disp.fill(0) #clear display
disp.show()
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
#font = ImageFont.load_default()
#Load custom font
font = ImageFont.truetype("/home/dietpi/ssd1306_stats/slkscr.ttf", 8)
bigfont = ImageFont.truetype("/home/dietpi/ssd1306_stats/slkscr.ttf", 16)
# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)

def getTemp():
        cmd = "cat /sys/class/thermal/thermal_zone0/temp"
        Temp = subprocess.check_output(cmd, shell=True).decode("utf-8").rstrip()
        return float(Temp)/1000.0 #returns float

#def waitForButton():
#    while (Button1.value < 32767):
#        time.sleep(0.05)

def clearImage():
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

def pushToScreen():
	disp.image(image)
	disp.show()

def clearScreen():
        #not like this: draw.rectangle((0, 0, width, height), outline=0, fill=0)
        disp.fill(0)
        disp.show()


def drawSystemStats():
        clearImage()
        #System Stats data:
        # Shell scripts for system monitoring from here:
        # https://unix.stackexchange.com/questions/119126/command-to-display memory-usage-disk-usage-and-cpu-load
        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%s MB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
        Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
        #temp and voltage data
        Temp = str('%.1f'%(getTemp())) + '°C'

        #Draw System Stats, temp and voltage
        draw.text((x, top + 0), "IP: " + IP, font=font, fill=255)
        draw.text((x, top + 9), CPU, font=font, fill=255)
        draw.text((x, top + 17), MemUsage, font=font, fill=255)
        draw.text((x, top + 25), Disk, font=font, fill=255)
        draw.text((x+95, top + 9), Temp, font=font, fill=255)


def drawShutdownPage():
         clearImage()
         draw.text((x,top),            "Reboot", font=bigfont, fill = 255)
         draw.text((x,top+18),       "Shutdown", font= bigfont, fill = 255)

         draw.rectangle((x+72, top+2, x+72+55, top+2+15), outline=255, fill=0)
         draw.text((x + 73,top + 1),   "RB - Press", font = font, fill = 255)
         draw.text((x + 73, top + 8),  "SD - Hold", font = font, fill = 255)
         pushToScreen()
         time.sleep(0.3)

         timeout = GPIO.wait_for_edge(ButtonPin, GPIO.FALLING, timeout=3000)
         if timeout is None:
            return
         time.sleep(0.3)
         if not(GPIO.input(ButtonPin)):
            Reboot = 0
            Shutdown = 1
         else:
            Reboot = 1
            Shutdown = 0

         if (Shutdown):
            logging.info("Shutting Down...")
            draw.rectangle((x,top+20, 93, 30), outline = 255, fill = 255)
            draw.text((x,top+18),            "Shutdown", font=bigfont, fill = 0)
            pushToScreen()
            time.sleep(0.5)
            clearImage()
            draw.text((x,top),            "Shutting", font=bigfont, fill = 255)
            draw.text((x,top +17),        "Down...", font=bigfont, fill =255)
            pushToScreen()
            time.sleep(0.5)
            clearScreen()
            subprocess.run("sudo shutdown now", shell=True) #Shutdown Command
            sys.exit()

         elif (Reboot):
            logging.info("Rebooting...")
            draw.rectangle((x,top +1, 68, 16), outline = 255, fill = 255)
            draw.text((x,top),               "Reboot", font=bigfont, fill = 0)
            pushToScreen()
            time.sleep(0.5)
            clearImage()
            draw.text((x,top),            "Rebooting...", font=bigfont, fill = 255)
            pushToScreen()
            time.sleep(0.5)
            clearScreen()
            subprocess.run("sudo reboot", shell=True) #Reboot Command
            sys.exit()


displaytime = 1 #how often to update the screen


Shutdown = 0
Reboot = 0

page = 0
Timer = 0
forceUpdate = 1 #force a screen update on startup

#On startup of script:
logo = Image.open("/home/dietpi/ssd1306_stats/pi-logo.ppm").convert("1")
disp.image(logo)
disp.show()
time.sleep(3)
clearScreen()


FirstRun = 1
#Active Loop
try:
     while True:
          print("1")
          GPIO.add_event_detect(ButtonPin, GPIO.FALLING, bouncetime=300)
          while not((GPIO.event_detected(ButtonPin)) or FirstRun):
               print("2")
               clearImage()
               drawSystemStats()
               pushToScreen()
               time.sleep(1)
               if not(GPIO.input(ButtonPin)): #if button held for ~1 second
                     GPIO.remove_event_detect(ButtonPin)
                     drawShutdownPage()
                     GPIO.remove_event_detect(ButtonPin)
                     GPIO.add_event_detect(ButtonPin, GPIO.FALLING, bouncetime=300)      
          clearScreen()
          print("3")
          GPIO.remove_event_detect(ButtonPin)
          GPIO.wait_for_edge(ButtonPin, GPIO.FALLING)
          GPIO.remove_event_detect(ButtonPin)
          time.sleep(0.1)
          if (FirstRun): FirstRun = 0

except KeyboardInterrupt:
     clearScreen()
     GPIO.cleanup()
