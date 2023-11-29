#!/usr/bin/env python3
'''
	Program:	DeviceControlSystem-Client-Pod.py, built in Python on top of the App.Net API.

				Copyright (C) 2013 Dale Weber. ALL Rights Reserved. License to be chosen.

	Author:		Dale Weber <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>

	Version:	0.3.0 (Unstable)
	Date:		10-Oct-2013
	Purpose:	Preliminary, VERY ALPHA release
	
	Requires:	Python v3.3.1, or later
				PyTZ 2013b, or later

'''
from os.path import expanduser
from datetime import datetime
from time import mktime, sleep

# You need the pytz 2013b version, or later
from pytz import utc, timezone

import pprint

import json
import requests
import os

# ADN Imports
from ADN_Authenticator import ADN_Authenticator
from ADN_Channel import ADN_Channel

# DCS Imports
from DCS_Device import DCS_Device

# This is specific to the Rasberry Pi
import RPi.GPIO as GPIO

'''
	Functions
'''

'''
	Parse a UTC creation date and convert it to local time. The timezone is read from
		/etc/timezone.  Returns a tuple of [date time timezone]. For instance, the Pacific
		timezone would have TZ=America/Los_Angeles . You really should have this set anyway. :)

		NOTICE: This ONLY handles the SPECIFIC case of creation dates that App.net uses.
'''
def local_datetime(iso_utc):
	fmt = '%m/%d/%Y %I:%M%p %Z'

	stime = iso_utc.split("T")

	sdate = stime[0]
	stime = stime[1]
	stime = stime[0 : len(stime) - 1]

	sdate = sdate.split("-")
	stime = stime.split(":")

	zyear = int(sdate[0])
	zmonth = int(sdate[1])
	zday = int(sdate[2])

	zhours = int(stime[0])
	zminutes = int(stime[1])
	zseconds = int(stime[2])

	utc_datetime = datetime(zyear, zmonth, zday, zhours, zminutes, zseconds)
	utc_timestamp = mktime(utc_datetime.timetuple())
	utc_localized = utc.localize(datetime.fromtimestamp(utc_timestamp))
	local_dt = local_timezone.normalize(utc_localized.astimezone(local_timezone))

	# You get the Date, Time, and Timezone
	local = local_dt.strftime(fmt)

	return local.split(" ")

def getTimeZone():
	tzpath = "/etc/timezone"
	tzone = "TIMEZONE"

	if os.path.islink(tzpath):
		tpath = os.path.realpath(tzpath)
		spath = os.path.split(tpath)
		tzone = spath[1]
	elif os.path.isfile(tzpath):
		t = open(tzpath, "r", encoding="utf-8")
		tzone = t.read()
		tzone = tzone[0 : len(tzone) - 1]
		t.close()

	return tzone

def clearScreen ():
    os.system(['clear','cls'][os.name == 'nt'])

    return None

'''
	Initialization
'''
dcsVersion = "0.3.0 (Unstable, 10-Oct-2013)"
clearScreen()

print ("======================================================================")
print ()
print ("Device Control System Client (Pod) v" + dcsVersion)
print ("Copyright (C) 2013 Dale Weber. ALL Rights Reserved")
print ("   <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>")
print ()
print ("======================================================================")

local_tz = getTimeZone()
local_timezone = timezone(local_tz)

'''
	Classes
'''

'''
	Class for the regular controller(s) on the network
'''
class DCS_Controller (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	Class for the MASTER controller(s) on the network
'''
class DCS_Master (DCS_Controller):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	Yes, robots are also devices!
'''
class DCS_Robot (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	This is the class for all small microcontroller boards
'''
class DCS_Microcontroller (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	This is the class for a specific device, named Pod, which
		is a Rasberry Pi running Adafruit's version of Rasbian
'''
class DCS_Pod (DCS_Device):
	myLeds = []
	myLedsProcess = []

	myFileName = "pod-hybotics-org.settings"
	myFileType = "net.hybotics.dcs.file.setttings"
	myFileMimeType = "text/plain"
	myFileID = "212674"
	myFileToken = "arb-0gcjRV1VcDfAnNlum7xxY8zjjHIpl8GmzKlHVWpM70wNBy3mUprB2txZ52M5KqNuVfyCaGOQWEqIH97D0_8__TMl_VBnhb2qzBZETWFTkXl4k7sXO65QsYqklCgq2lhXt7DjBRpvdhexkloKaB3ZP3S57evVtXGKY2-RAO5ITlHt5d4zvM5d6DKHx5wKK"

	# This is the number of seconds to delay at the end of each run() iteration
	delayRunLoop = 5

	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		ledName = "green"
		ledPin = 18
		GPIO.setup(ledPin, GPIO.OUT)
		ledColor = "Green"
		ledState = "off"
		ledBlinkRate = 0
		ledProcess = None

		ledInfo = self.ledUpdate(ledName, ledPin, ledColor, ledState, ledBlinkRate, ledProcess)

		self.myLeds.append(ledInfo)

		ledName = "red"
		ledPin = 23
		GPIO.setup(ledPin, GPIO.OUT)
		ledColor = "Red"

		ledInfo = self.ledUpdate(ledName, ledPin, ledColor, ledState, ledBlinkRate, ledProcess)

		self.myLeds.append(ledInfo)

		return None

	def ledBlink (self, ledPin, ledRate):
		status = True
		ledProcess = None

		return ledProcess

	def ledChangeState (self, ledName, newLedState, newLedRate=None):
		status = True

		ledNr = self.ledFind(ledName)
		led = self.myLeds[ledNr]
		ledName = led["name"]
		ledPin = led["pin"]
		ledColor = led["color"]
		ledState = led["state"]
		ledRate = led["rate"]
		ledProcess = led["process"]

		if (ledRate == None):
			ledRate = 0

		if (ledState == "on"):
			GPIO.output(ledPin, True)
		elif (ledState == "off"):
			GPIO.output(ledPin, False)
		elif (ledState == "blink") and (ledRate != None):
			if (ledRate != None):
				self.ledProcess[ledNr] = ledBlink(ledPin, ledRate)
		else:
			self.displayError("ledChangeState", 9999, "Invalid LED state: " + ledState)
			status = False

		if (status):
			# Update the LED information
			ledInfo = self.ledUpdate(ledName, ledPin, led["color"], ledState, ledRate, ledProcess)
			self.myLeds[ledNr] = ledInfo

		return status

	def ledFind (self, ledName):
		foundLedNumber = None

		for index in range(len(self.myLeds)):
			led = self.myLeds[index]

			if (led["name"] == ledName):
				foundLedNumber = index
				break

		return foundLedNumber

	def ledShow (self):
		lenLeds = len(self.myLeds)
		ledCount = 0

		print ("Here are my LEDs:")
		print ()

		for i in range(lenLeds):
			led = self.myLeds[i]
			ledCount += 1

			print ("     Name: " + led["name"])
			print ("     On Pin: " + str(led["pin"]))
			print ("     Color: " + led["color"])
			print ("     State: " + led["state"])
			print ("     Blink Rate: " + str(led["rate"]))
			print ()

		if (ledCount > 0):
			print ("I have " + str(ledCount) + " LEDs")
		else:
			print ("I don't have any LEDs!")

		print ()

		return None

	def ledUpdate (self, ledName, ledPin, ledColor, ledState, ledRate, ledProcess):
		ledInfo = {
			"name" : ledName,
			"pin" : ledPin,
			"color" : ledColor,
			"state" : ledState,
			"rate" : ledRate,
			"process" : ledProcess
		}

		return ledInfo

	'''
		Message processing routines:

		These are unique to each device, so will have to be written
			to handle the unique capabilities of each of the devices in
			your "network of things." You may have more or fewer
			message types to handle, so will need to adjust the code
			as needed to accomodate differences.

		A return status of None means an operation was successful. Otherwise,
			an error code will be returned, the error code will be set in
			self.operationErrorCode and the result text will be set in
			self.operationResultText.
	'''

	# Annotation type: net.hybotics.dcs.request
	def processRequest (self, aNote, msgid):
		status = True
		ackMsgID = None

		action = "request"

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (deviceIndex == None) and (device == None):
			displayError("processRequest", 9999, fromFQN + " was not found in my device list")
		elif (self.deviceGotAuthenticated and self.connectionAuthorized):
			req = aValue[action]
			reqNumber = aValue["number"]

			if (req == "led"):
				if ("green" in aValue["params"]):
					ledName = "green"
					data = aValue["data"]
					ledAction = data[ledName]

					if (ledAction == "on"):
						self.ledChangeState(ledName, "on")
					elif (ledAction == "off"):
						self.ledChangeState(ledName, "off")
					elif (ledAction == "blink"):
						ledRate = self.myRequestData[ledName + "rate"]

				if ("red" in aValue["params"]):
					ledName = "red"
					data = aValue["data"]
					ledAction = data[ledName]

					if (ledAction == "on"):
						self.ledChangeState(ledName, "on")
					elif (ledAction == "off"):
						self.ledChangeState(ledName, "off")
					elif (ledAction == "blink"):
						ledRate = self.myRequestData[ledName + "rate"]

			# We send an immediate acknowledgement for these requests
			if (req in [ "led" ]):
				status, ackMsgID = self.sendAcknowledgement(fromFQN, action, reqNumber)

				if (ackMsgID == None):
					self.displayError("processRequest", 1002, "There was a problem sending an acknowledgement to " + fromFQN)

		return ( status, ackMsgID )

	def parseReadResult (self, number):
		print ("     (" + str(number) + ") Parsing result.text from the last read() operation")
		print ()
		print ("     Read #1 URL = '" + self.channel.readURL + "'")
		print ()

		readJSON = json.loads(self.channel.readResultText)

		data = readJSON["data"]
		dataLen = len(data)

		meta = readJSON["meta"]
		code = meta["code"]

		print ("     Result code = " + str(code))

		print ("     " + str(dataLen) + " messages were read")

		for dmsg in data:
			print ("     Message ID " + dmsg["id"])

		self.channel.readURL = ""
		self.channel.readResultText = ""

		return None

	'''
		This is the device run loop, where the device will spend all of its time.
	'''
	def run (self):
		# Initialize
		status = True
		msgid = None
		readMessages = False

		status, msgid = self.startup()

		while (self.running):
			print ("Getting message for " + self.myFQN)

			message = self.get(self.myFQN)

			if (message == None):
				print ("There aren't any new messages for me to process.")
				readMessages = True
			else:
				status = self.process(message)
				
				if (status):
					msgid = message["id"]
					print ("Message " + msgid + " was processed successfully.")
				else:
					self.displayError("run", 9999, "There was a problem processing this message.")

				self.showDevices()

			if (self.running):
				# Check pending actions
				action = self.checkPendingActions()

				# Check pending tasks
				task = self.checkPendingTasks()

				self.showDevices()
				
				if (readMessages):
					# Try reading more messages from the channel, if none were processed on this pass
					print ("Looking for new messages to process..")
        
					# Read messages from the channel and extract data
					self.extractMessageData()

					if (self.debugging):
						self.parseReadResult(2)

					readMessages = False

				# Validate the devices list and make sure we have the authorization
				#	information we need.
				self.validateDevices()

				# Delay a little bit to allow for new messages to come in.
				sleep(self.delayRunLoop)
			else:
				print ("I have received the shutdown command - shutting down..")
				status = self.shutdown()

		return ( status, msgid )

	'''
		Device shutdown routine
	'''
	def shutdown (self):
		status = True

		print ("Device " + self.myFQN + " is shutting down..")

		return status

	'''
		Device startup and initialization routine
	'''
	def startup (self):
		status = True
		msgid = None

		self.running = True

		print ("Device " + self.myFQN + " is starting up..")

#		self.debuggingDevices = True
#		self.debuggingProcess = True

		# Every device has to announce themselves on the network
		toFQN = "all"
		status, msgid = self.send(toFQN, [ "announce" ])

		if (msgid == None):
			self.weGoofed(1, "Announce", toFQN)
		else:
			print ("Announce message has been sent!")

		# Read messages from the channel and extract data
		self.extractMessageData()

		if (self.debugging):
			self.parseReadResult(1)

		print ()
		print ("Entering run mode..")
		print ()

		return ( status, msgid )
'''
	End of DCS_Pod (DCS_Device) class
'''

'''
	Put YOUR user name and password in these
'''
u_name = "snappy"
userpw = "PRIVATE"

#u_name = "hybotics"
#userpw = "PRIVATE"

# Authenticate the user account with App.Net
adn = ADN_Authenticator(u_name, userpw)

# DCS Test #1
#patterChannel = "25178"

# DCS Test #2
#patterChannel = "26692"

# DCS Test #3
patterChannel = "26918"

#print ()
#rint ("Connecting to Patter channel " + patterChannel)
#print ()

# Connect to our Patter channel
#patter = ADN_Channel(adn)							# Get a channel object
#patter.info(patterChannel)							# REQUIRED when not creating a channel

'''
	Create the device.
'''

print ()
print ("Creating pod.hybotics.org, a mobile device..")
print ()

podName = "pod"
podNetwork = "hybotics.org"
podCheckType = "crc64"
podResources = [ "fixed", "leds", "camera" ]
podPassword = "fbs6dE!P8u443V^@jsN*PQZ^h"
podPublicKey = None

pod = DCS_Pod(adn, podName, podNetwork, podResources, podCheckType, podPassword, podPublicKey)

status = pod.connect(patterChannel)

if (status):
	pod.show()

	print ("======================================================================")

	pod.ledShow()

	pod.run()
else:
	print ("I am unable to run, due to an error ocurring while connecting to channel " + patterChannel + "!")
