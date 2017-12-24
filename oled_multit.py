# Some comments on first row.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import psutil, sys,threading
import time,datetime
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import Adafruit_SSD1306
import json, urllib, requests
import os
import netifaces as ni

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


# Load fonts.
font = ImageFont.load_default()
font35 = ImageFont.truetype('vcr.ttf', 35)

#Variables cause 2 threads ?
flip = "0"
mode = 0
BTC = ""
IP = ""
CPU = ""
MemUsage = ""
Disk = ""
timer = 30 
kill = 0

class varupdate(threading.Thread):
	#Thread to update variables every 30 seconds
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name
	def stop(self):
		return
		self._stop_event.set()
	def run(self):
		global flip
		global mode	 
		global BTC
		global IP
		global CPU
		global MemUsage
		global Disk
		global timer
		global kill
		while True:
			if mode ==1:
				c.acquire()
				IP = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
				CPU = "Cpu: " + str(psutil.cpu_percent()) + "% "
				Mem = psutil.virtual_memory() 
				MemUsage = "Mem: "  + str(Mem.used >> 20) + "/" + str(Mem.total >> 20) + " " + str(Mem.percent) + "%"
				# cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
				# Disk = subprocess.check_output(cmd, shell = True )
				url = "http://api.coindesk.com/v1/bpi/currentprice.json"
				headers = {
					'User-Agent': 'AppleWebKit/537.36 (KHTML, like Gecko) ',
					'Accept': 'application/json'}
				BTC = '{0:,}'.format( int(requests.get(url, headers=headers).json()['bpi']['USD']['rate_float']) )
				c.release()
				timer=500
				for i in range(500):
					time.sleep(1)
					if kill == 1:
						return

			else:
				url = "http://api.coindesk.com/v1/bpi/currentprice.json"
				headers = {
					'User-Agent': 'AppleWebKit/537.36 (KHTML, like Gecko) ',
					'Accept': 'application/json'}
				c.acquire()
				BTC = '{0:,}'.format( int(requests.get(url, headers=headers).json()['bpi']['USD']['rate_float']) )
				c.release()
				timer=500
				for i in range(500):
					time.sleep(1)
					if kill == 1:
						return
				

class screenctl(threading.Thread):
	#Thread to refresh oled display
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name
	def stop(self):
		self._stop_event.set()
		return
	def run(self):
		global flip
		global mode	 
		global BTC
		global timer
		global kill
		try:
			while True:
				c.acquire()
				# Draw a black filled box to clear the image.
				draw.rectangle((0,0,width,height), outline=0, fill=0)
				if not GPIO.input(D_pin):
					kill = 1
					break
				if GPIO.input(U_pin): # button is released
					mode = mode
				else: # button is pressed:
					if mode == 0:
						mode = 1
					else:
						mode = 0
				if mode == 1:
					#Stats Mode
					font = ImageFont.load_default()
					# Writes text.
					draw.text((x, top),	   "IP: " + str(IP),  font=font, fill=255)
					draw.text((x, top+8),	 str(CPU), font=font, fill=255)
					draw.text((x, top+16),	str(MemUsage),  font=font, fill=255)
					# draw.text((x, top+24),	str(Disk),  font=font, fill=255)
					draw.text((x, top+25),	"______________________s	   ",  font=font, fill=255)
					draw.text((x, top+25),	"______________________	   ",  font=font, fill=255)
					draw.text((x, top+48),	"USD\BTC: "+ str(BTC),  font=font, fill=255)
					draw.text((x+110, top+55),	str(timer),  font=font, fill=255)
					timer = timer - 1
					disp.image(image.rotate(180)) #rotated 180
					disp.display()
					if kill == 1:
						c.release()
						return
					time.sleep(1)
					c.release()
				else:
					#Stats Mode
					font = ImageFont.load_default()
					draw.text((x, top),	"USD/BTC:",  font=font, fill=255)
					st = datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%y %H:%M:%S')
					draw.text((x, top+51),	str(st),  font=font, fill=255)
					draw.text((x, top+16),	str(BTC),  font=font35, fill=255)
					draw.text((x+110, top+55),	str(timer),  font=font, fill=255)
					timer = timer - 1
					disp.image(image.rotate(180)) #rotated 180
					disp.display()
					if kill == 1:
						c.release()
						return
					time.sleep(1)
					c.release()
					
		except KeyboardInterrupt: 
			GPIO.cleanup()
			
a = varupdate("varupdate")
b = screenctl("screenctl")
#a = reqthread()
#b = reqthread()
# b.daemon = True
# a.daemon = True
b.start()
a.start()
def bye( display ):
	"Program is exiting"
	print "Bye..."
	draw.rectangle((0,0,width,height), outline=0, fill=0)
	disp.image(image) 
	disp.display()
	draw.text((x, top+16),	str("Bye!"),  font=font35, fill=255)
	disp.image(image.rotate(180)) #rotated 180
	disp.display()
	time.sleep(1)
	draw.rectangle((0,0,width,height), outline=0, fill=0)
	disp.image(image) 
	disp.display()
	return
	
while True:
	try:
	#Keep main thread from exiting, trying to exit threads correctly...
		time.sleep(1)
		if kill == 1:
			bye(disp)
			kill = 1
			a.join()
			b.join()
			# Draw a black filled box to clear the image.
			break
	except (KeyboardInterrupt, SystemExit, kill):
		bye(disp)
		kill = 1
		a.join()
		b.join()
		break
