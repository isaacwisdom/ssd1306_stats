#setup commands
#sudo pip3 install adafruit-blinka adafruit-circuitpython-ssd1306 adafruit-circuitpython-mcp3xx requests
#sudo apt-get install python3-pil
#cd /home/dietpi/ssd1306_stats
#wget http://kottke.org/plus/type/silkscreen/download/silkscreen.zip
#unzip silkscreen.zip

#enable i2c and spi

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import logging #for logging
import time
import subprocess
import busio

#for stopping the script
import sys

#for I2C PiOLED
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

#For SPI MCP3008
import board
import digitalio #also used for the fan
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# For Pi-hole stats
import json
import requests
api_url = 'http://127.0.0.1/admin/api.php'

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


# Create the SPI Bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# Create the cs (chip select)
cs = digitalio.DigitalInOut(board.D8)
# Create the mcp object
mcp = MCP.MCP3008(spi, cs)
#create an analog input channel on  pin 0, 1 and 2
InputVoltage = AnalogIn(mcp, MCP.P2)
Button1 = AnalogIn(mcp, MCP.P0)
Button2 = AnalogIn(mcp, MCP.P1)


#create the fan object
Fan = digitalio.DigitalInOut(board.D25)
Fan.direction = digitalio.Direction.OUTPUT
#Control this pin by using Fan.value = True or Fan.value = False
ON_THRESHOLD = 60
OFF_THRESHOLD = 50


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

def handleFan():
        Temp = getTemp()
        if ((Temp >= ON_THRESHOLD) and not Fan.value):
           Fan.value = True
           logging.info("Turning Fan ON, temp = %s", str(Temp)) 
        elif (Fan.value and Temp <= OFF_THRESHOLD):
           Fan.value = False
           logging.info("Turning Fan OFF, temp = %s ", str(Temp))

def waitForButton():
    while (Button1.value < 32767):
        time.sleep(0.05)

def clearImage():
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

def pushToScreen():
	disp.image(image)
	disp.show()

def clearScreen():
        #not like this: draw.rectangle((0, 0, width, height), outline=0, fill=0)
        disp.fill(0)
        disp.show()

def drawVoltageAndTemp():
        clearImage()
        CTemp = getTemp()
        FTemp = CTemp * 1.8 + 32
        CTempText = str('%.1f'%(CTemp)) + '°C'
        FTempText = '(' + str(int(FTemp)) + '°F)'
        Voltage = 5.00 * InputVoltage.value/46592.00
        VoltageText = str('%.2f'%(Voltage)) + 'V'
        draw.text((x, top),    CTempText   , font=bigfont, fill=255)
        draw.text((x+70,top+6),FTempText   , font= font,   fill=255)
        draw.text((x, top+18), VoltageText , font=bigfont, fill=255)
        if (Fan.value):
            draw.text((x+70, top+18+6),   "Fan ON" , font=font, fill=255)
        else:
            draw.text((x+70, top+18+6) ,  "Fan OFF", font=font, fill=255)

def drawSystemStats():
        clearImage()
        #System Stats data:
        # Shell scripts for system monitoring from here:
        # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
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
        Voltage = 5.00 * InputVoltage.value/46592.00
        VoltageText = str('%.2f'%(Voltage)) + 'V'

        #Draw System Stats, temp and voltage
        draw.text((x, top + 0), "IP: " + IP, font=font, fill=255)
        draw.text((x, top + 9), CPU, font=font, fill=255)
        draw.text((x, top + 17), MemUsage, font=font, fill=255)
        draw.text((x, top + 25), Disk, font=font, fill=255)
        draw.text((x+100, top + 0), VoltageText, font=font, fill=255)
        draw.text((x+95, top + 9), Temp, font=font, fill=255)

def drawPiHoleStats():
        clearImage()
        #Host Name and I
        cmd = "hostname -I | cut -d' ' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8").rstrip()
        cmd = "hostname"
        HOST = subprocess.check_output(cmd, shell=True).decode("utf-8").rstrip()
        draw.text((x, top),       "IP: " + str(IP) + " ( " + HOST + " )",  font=font, fill=255)
        #PiHole data from API
        try:
             r = requests.get(api_url)
             data = json.loads(r.text)
             DNSQUERIES = data['dns_queries_today']
             ADSBLOCKED = data['ads_blocked_today']
             CLIENTS = data['unique_clients']
             #Draw PiHole data:
             draw.text((x, top+8),     "Ads Blocked: " + str(ADSBLOCKED), font=font, fill=255)
             draw.text((x, top+16),    "Clients:     " + str(CLIENTS),  font=font, fill=255)
             draw.text((x, top+24),    "DNS Queries: " + str(DNSQUERIES),  font=font, fill=255)
        except:
             logging.info("PiHole data could not be accessed")
             draw.text((x, top+8),     "PiHole data Error", font=font, fill=255)

def drawShutdownPage():
         clearImage()
         draw.text((x,top),            "Reboot", font=bigfont, fill = 255)
         draw.text((x,top+18),       "Shutdown", font= bigfont, fill = 255)

         draw.rectangle((x+72, top+2, x+72+55, top+2+15), outline=255, fill=0)
         draw.text((x + 73,top + 1),   "RB - Press", font = font, fill = 255)
         draw.text((x + 73, top + 8),  "SD - Hold", font = font, fill = 255)
         if (Button2.value > 32767):
            Reboot =  1
            Shutdown = 0
            time.sleep(0.1)
            if (Button2.value > 32767):
               Reboot = 0
               Shutdown = 1
         else:
            Reboot = 0
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

fantime = 3 #how often to update the fan state
displaytime = 1 #how often to update the screen
buttontime = 0.2 #how often the loops runs (to handle the buttons), keep this value low

if (fantime > displaytime):
    TimerMax = fantime/buttontime
else:
    TimerMax = displaytime/buttontime


Shutdown = 0
Reboot = 0

prevButton1var = 0
prevButton2var = 0
page = 0
Timer = 0
forceUpdate = 1 #force a screen update on startup

#On startup of script:
logo = Image.open("/home/dietpi/ssd1306_stats/pi-logo.ppm").convert("1")
disp.image(logo)
disp.show()
time.sleep(5)

#Active Loop
try:
    while True:
         #get Button 1 value
        if (Button1.value > 32767): Button1var = 1; logging.debug("Button1Pressed")
        else: Button1var = 0
        #debounce it to create a single press
        if ((not prevButton1var) and Button1var): BouncedButton1 = 1; logging.debug("Button 1 bounced  press");
        else: BouncedButton1 = 0
        prevButton1var = Button1var

        #get Button 2 value
        if (Button2.value > 32767): Button2var = 1; logging.debug("Button2Pressed") 
        else: Button2var = 0
        #debounce it to create a single press
        if ((not prevButton2var) and Button2var): BouncedButton2 = 1; logging.debug("Button 2 bounced  press")
        else: BouncedButton2 = 0
        prevButton2var = Button2var

        #handle the fan code every fantime seconds
        if (Timer % (fantime/buttontime) == 0):
           handleFan()
           logging.debug("Fan Check")


        #change the page on each button1 press and force a screen update
        if (BouncedButton1):
             page += 1
             forceUpdate = 1

        if (BouncedButton2 or Button2var):
             forceUpdate = 1

        #push the image to the screen every displaytime seconds
        if (Timer % (displaytime/buttontime) == 0 or forceUpdate == 1):
             forceUpdate = 0
             if (page == 0 or page > 4):
                page = 0
                clearScreen()
             if (page == 1):
                drawVoltageAndTemp()
                pushToScreen()
             elif (page == 2):
                drawSystemStats()
                pushToScreen()
             elif (page == 3):
                drawPiHoleStats()
                pushToScreen()
             elif (page == 4):
                drawShutdownPage()
                pushToScreen()
             logging.debug("screen updated, page = %s", str(page))



        Timer += 1
        if (Timer == TimerMax):
           Timer = 0
        #sleep for buttontime seconds (buttons are checked every loop)
        time.sleep(buttontime)

except KeyboardInterrupt:
     clearScreen()
