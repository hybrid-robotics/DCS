#!/usr/bin/env python3
'''
	Program:	DeviceControlSystem-Client-Stargazer.py, built in Python on top of the App.Net API.

				Copyright (C) 2013 Dale Weber. ALL Rights Reserved. License to be chosen.

	Author:		Dale Weber <hybotics.pdx@gmail.com, @hybotics on App.Net>

	Version:	0.3.3 (Unstable)
	Date:		04-Apr-2014
	Purpose:	Preliminary, VERY ALPHA release
	
	Requires:	Python v3.3.1, or later
				PyTZ 2013b, or later

'''
# These to imports are specific to the BeagleBone (Black)
import Adafruit_BBIO.GPIO as GPIO

from LED_bone import LED
#from LedPlay_bone import LedPlay
# End device specific imports

from os.path import expanduser
from datetime import datetime
from time import mktime, sleep

# You need the pytz 2013b version, or later
from pytz import utc, timezone

import pprint

import json
import requests
#import os

# My utilities used in various projects
from Hybotics_Utils import getTimeZone, clearScreen, stringBoolean

# ADN Imports
from ADN_Authenticator import ADN_Authenticator
from ADN_Channel import ADN_Channel
from ADN_Utilities import local_datetime

# Device Control System imports
from DCS_Device import DCS_Device

'''
	Functions
'''

'''
	Initialization
'''
dcsVersion = "0.3.2 (Unstable, 26-Nov-2013)"
clearScreen()

print ("======================================================================")
print ("")
print ("Device Control System Client (Stargazer) v" + dcsVersion)
print ("Copyright (C) 2013 Dale Weber. ALL Rights Reserved")
print ("   <hybotics.pdx@gmail.com, @hybotics on App.Net>")
print ("")
print ("======================================================================")

#local_tz = getTimeZone()
#local_timezone = timezone(local_tz)

'''
	Classes
'''

'''
	Class for the regular controller(s) on the network
'''
class DCS_Controller (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
#		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	Class for the MASTER controller(s) on the network
'''
class DCS_Master (DCS_Controller):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
#		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	Yes, robots are also devices!
'''
class DCS_Robot (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
#		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	This is the class for all small microcontroller boards
'''
class DCS_Microcontroller (DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
#		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	This is the class for a specific device, named Pod, which
		is a Rasberry Pi running Adafruit's version of Rasbian
'''
class DCS_Stargazer (DCS_Device):
	myLeds = []
	myLedsProcess = []

	'''
		LED Information
	'''
	myLedName = None
	myLedPin = None
	myLedColor = None
	myLedState = None
	myLedBlinkRate = None
	myLedProcess = None

	# The default LED on/off duration in ms
	msDuration = 500

	myFileName = "pod-hybotics-org.settings"
	myFileType = "net.hybotics.dcs.file.setttings"
	myFileMimeType = "text/plain"
	myFileID = "212674"
	myFileToken = "arb-0gcjRV1VcDfAnNlum7xxY8zjjHIpl8GmzKlHVWpM70wNBy3mUprB2txZ52M5KqNuVfyCaGOQWEqIH97D0_8__TMl_VBnhb2qzBZETWFTkXl4k7sXO65QsYqklCgq2lhXt7DjBRpvdhexkloKaB3ZP3S57evVtXGKY2-RAO5ITlHt5d4zvM5d6DKHx5wKK"

	# This is the number of seconds to delay at the end of each run() iteration
	delayRunLoop = 5

	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
#		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		'''
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		'''
		
		# Green LED
		green = LED("green", "P8_12", False, "Green", "Green LED", 0, None, None)
		self.myLeds.append(green)

		# Red LED
		red = LED("red", "P8_14", False, "Red", "Red LED", 0, None, None)
		self.myLeds.append(red)

		# Yellow LED
		yellow = LED("blue", "P8_16", False, "Blue", "Blue LED", 0, None, None)
		self.myLeds.append(yellow)

		# White LED
		white = LED("white", "P8_18", False, "White", "White LED", 0, None, None)
		self.myLeds.append(white)

		return None

	'''
	***	Begin LED Management routines
	'''

	'''
		Perform an action on an LED
	'''
	def actionLED (self, ledNr, ledAction, ms=None):
		status = True
		led = self.myLeds[ledNr]

		if (ledAction == "on"):
			led.bit(True)
		elif (ledAction == "off"):
			led.bit(False)
		elif (ledAction == "blink") and (ms != None):
			led.bit.toggle(ms)
		elif (ledAction == "blink") and (ms == None):
			print ("A duration in ms is required for the " + ledAction + " operation!")
			status = False
		else:
			print (ledAction + " is an invalid operation for an LED!")
			status = False

		return status

	'''
		Blink an LED - have not figured out how to do this yet
	'''
	def blinkLED (self, ledName):
		status, ledNr = self.findLED(ledName)

		if status and (ledNr != None):
			led = self.myLeds[ledNr]
			
			led.state = "blinking"
			print ("Blinking the " + led.color + " LED..")

			# Launch as a separate process or thread
			status = blinkLedProcess(led.bit.pin, led.blinkRate)
		else:
			self.displayError("blinkLED", 9999, "Invalid LED name: " + ledName)

		return status

	'''
		Blink an LED at the set rate
	'''
	def blinkLedProcess (self, pin, rate):
		status = True
		
		return status

	'''
		Find an LED in the LED list by name
	'''
	def findLED (self, ledName):
		status = True
		foundLedNr = None
		ledIndex = 0
		nrLeds = len(self.myLeds)

		while (foundLedNr == None) and (ledIndex < nrLeds):
			if self.myLeds[ledIndex].name == ledName:
				foundLedNr = ledIndex
			else:
				ledIndex += 1

		if foundLed == None:
			status = False

		return ( status, foundLedNr )

	'''
		Display the LED List
	'''
	def displayLEDs (self):
		status = True
		lenLEDs = len(self.myLeds)

		ledCount = 0

		if (lenLEDs > 0):
			print ()
			print ("Here are my LEDs:")
			print ()

			for led in self.myLeds:
				ledCount += 1

				print ("     Name:       " + led.name)
				print ("     On Pin:     " + str(led.bit.pin))
				print ("     Color:      " + led.color)
				print ("     State:      " + stringBoolean(led.bit.state, "On", "Off"))
				print ("     Blink Rate: " + str(led.blinkRate))
				print ()

		if (ledCount > 0):
			print ("I have " + str(ledCount) + " LEDs")
		else:
			print ("I don't have any LEDs!")

		print ()

		return status

	'''
		Set the global LED variables
	'''
	def setLED (self, ledName):
		status, ledNr = self.findLED(ledName)

		if status:
			led = self.myLeds[ledNr]

			self.myLedName = led.name
			self.myLedPin = led.bit.pin
			self.myLedColor = led.color
			self.myLedState = led.bit.state
			self.myLedProcess = led.process
			self.myLedBlinkRate = led.blinkRate
		else:
			self.displayError("setLED", 9999, "LED " + ledName + " was not found")

		return status

	'''
		Update LED information.
	'''
	def updateLED (self, ledIndex=None):
		status = True
		nrLeds = len(self.myLeds)
		ledInfo = None

		if (nrLeds > 0) :
			ledInfo = {
				"name" : self.myLedName,
				"pin" : self.myLedPin,
				"color" : self.myLedColor,
				"state" : self.myLedState,
				"blinkrate" : self.myLedBlinkRate,
				"process" : self.myLedProcess
			}

			# Update the LED in the LED list
			if (ledIndex != None) and (ledIndex >= 0) and (ledIndex < nrLeds):
				self.myLeds[ledIndex] = ledInfo
		else:
			self.displayError("updateLED", 9999, "There are no LEDs")
			status = False

		return ( status, ledInfo )
	'''
		End of LED management routines 
	'''

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

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (deviceIndex == None) and (device == None):
			displayError("processRequest", 9999, fromFQN + " was not found in my device list")
		elif (self.deviceGotAuthenticated and self.connectionAuthorized):
			req = aValue[action]
			reqNumber = aValue["number"]
			reqParams = aValue["params"]
			nrParams = len(reqParams)
			reqData = aValue["data"]

			ledNr = None

			if (req == "led"):
				for ledName in reqParams:
					status, ledNr = self.findLED[ledName]
					
					if status:
						led = self.myLeds[ledNr]

						ledAction = reqData[ledName]

						if (ledName in [ "green", "red", "yellow" ]):
							actionLED(ledNr, ledAction, self.msDuration)
					else:
						self.displayError("processRequest", 9999, "LED '" + ledName + "' was not found")
			else:
				self.displayError("processRequest", 9999, "Invalid request: " + req)

			# We send an immediate acknowledgement for these requests
			if (req in [ "led" ]):
				status, ackMsgID = self.sendAcknowledgement(fromFQN, action, reqNumber)

				if (not status) and (ackMsgID == None):
					self.displayError("processRequest", 1002, "There was a problem sending an acknowledgement to " + fromFQN)
		else:
			self.displayError("processRequest", 9999, "Nothing was done, due to " + fromFQN + "'s connection not being authorized")	
			status = False
			ackMsgID = None

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

			message = self.getMessage(self.myFQN)

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

				self.displayDeviceList()

			if (self.running):
				# Check pending actions
				action = self.checkPendingActions()

				# Check pending tasks
				task = self.checkPendingTasks()

				self.displayDeviceList()
				
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

		print ()
		print ("Device " + self.myFQN + " is starting up..")

		self.debuggingAddress = True
#		self.debuggingDevices = True
#		self.debuggingProcess = True

		# Every device has to announce themselves on the network
		toFQN = "all"
		status, msgid = self.sendMessage(toFQN, [ "announce" ])

		if (msgid == None):
			self.weGoofed(1, "Announce", toFQN)
		else:
			print ("Announce message has been sent!")

		# Read messages from the channel, and extract data
		self.extractMessageData()

		if (self.debugging):
			self.parseReadResult(1)

		print ("")
		print ("Entering run mode..")
		print ("")

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
#u_name = "quark"
#userpw = "PRIVATE"

# Authenticate the user account with App.Net
adn = ADN_Authenticator(u_name, userpw)

# DCS Test #1
patterChannel = "25178"

# DCS Test #2
#patterChannel = "26692"

# DCS Test #3
#patterChannel = "26918"

#print ()
#rint ("Connecting to Patter channel " + patterChannel)
#print ()

# Connect to our Patter channel
#patter = ADN_Channel(adn)							# Get a channel object
#patter.info(patterChannel)							# REQUIRED when not creating a channel

'''
	Create the device.
'''

stargazerName = "stargazer"
stargazerNetwork = "hybotics.org"
stargazerCheckType = "crc64"
stargazerResources = [ "fixed", "leds" ]
stargazerPassword = "ePq@7g40lqmq*0R@^rlQMw91P"
stargazerPublicKey = None

print ("")
print ("Creating device " + stargazerName + "." + stargazerNetwork + ", a fixed device..")
print ("")

stargazer = DCS_Stargazer(adn, stargazerName, stargazerNetwork, stargazerResources, stargazerCheckType, stargazerPassword, stargazerPublicKey)

status = stargazer.connect(patterChannel)

if (status):
	stargazer.displayDevice()

	print ("======================================================================")

	stargazer.displayLEDs()

	stargazer.run()
else:
	print ("I am unable to run, due to an error ocurring while connecting to channel " + patterChannel + "!")
