# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import threading
import time
import datetime
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import Adafruit_SSD1306
import json, sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

c = threading.Condition()

# Raspberry Pi pin configuration:
RST = None	 # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Input pins:
L_pin = 27 
R_pin = 23 
C_pin = 4 
U_pin = 17 
D_pin = 22 
 
A_pin = 5 
B_pin = 6 
 
GPIO.setmode(GPIO.BCM) 
GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up



disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
# Initialize library.
disp.begin()
# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))


# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

#Variables cause 2 unsynchroned threads
flip = "0"
mode = "0"
BTC = ""
IP = ""
CPU = ""
MemUsage = ""
Disk = ""

class varupdate(threading.Thread):
	#Thread to update variables every 30 seconds
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global flip
		global mode	 
		global BTC
		global IP
		global CPU
		global MemUsage
		global Disk
		while True:
			if mode =="1":
				cmd = "hostname -I | cut -d\' \' -f1"
				IP = subprocess.check_output(cmd, shell = True )
				cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
				CPU = subprocess.check_output(cmd, shell = True )
				cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
				MemUsage = subprocess.check_output(cmd, shell = True )
				cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
				Disk = subprocess.check_output(cmd, shell = True )
				cmd = "curl -s http://api.coindesk.com/v1/bpi/currentprice.json | python -c \"import json, sys; print(json.load(sys.stdin)['bpi']['USD']['rate'])\"|awk {'print \"BTC: \"$1'}"
				BTC = subprocess.check_output(cmd, shell = True )
				time.sleep(30)
			else:
				cmd = "curl -s http://api.coindesk.com/v1/bpi/currentprice.json | python -c \"import json, sys; print(json.load(sys.stdin)['bpi']['USD']['rate'])\"| tr \".\" \" \" |awk '{ print $1}'"
				BTC = subprocess.check_output(cmd, shell = True )
				time.sleep (30)


class screenctl(threading.Thread):
	#Thread to refresh oled display
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global flip
		global mode	 
		global BTC
		try:
			while True:

				# Draw a black filled box to clear the image.
				draw.rectangle((0,0,width,height), outline=0, fill=0)
				if GPIO.input(A_pin): # button is released
					mode = mode
				else: # button is pressed:
					if mode == "0":
						mode = "1"
					else:
						mode = "0"

				if mode == "1":
					#Stats Mode
					font = ImageFont.load_default()
					# Writes text.
					shape_width = 20
					draw.text((x, top),	   "IP: " + str(IP),  font=font, fill=255)
					draw.text((x, top+8),	 str(CPU), font=font, fill=255)
					draw.text((x, top+16),	str(MemUsage),  font=font, fill=255)
					draw.text((x, top+24),	str(Disk),  font=font, fill=255)
					draw.text((x, top+25),	"______________________s	   ",  font=font, fill=255)
					draw.text((x, top+25),	"______________________	   ",  font=font, fill=255)
					draw.text((x, top+48),	str(BTC),  font=font, fill=255)

					disp.image(image.rotate(180)) #rotated 180
					disp.display()
					time.sleep(0.1)
				else:
					#Stats Mode
						font = ImageFont.load_default()
						draw.text((x, top),	"BTC/USD:",  font=font, fill=255)
						st = datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%y %H:%M:%S')
						ont = ImageFont.truetype('vcr.ttf', 2)
						draw.text((x, top+51),	str(st),  font=font, fill=255)
						font = ImageFont.truetype('vcr.ttf', 35)
						draw.text((x, top+16),	str(BTC),  font=font, fill=255)
						font = ImageFont.load_default()
			
						
						disp.image(image.rotate(180)) #rotated 180
						disp.display()
						time.sleep(1)
		except KeyboardInterrupt: 
			GPIO.cleanup()
a = varupdate("varupdate")
b = screenctl("screenctl")

b.start()
a.start()

a.join()
b.join()
					