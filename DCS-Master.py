#!/usr/bin/env python3
'''
	Program:	DeviceControlSystem-Master.py, built in Python on top of the App.Net API.

				Copyright (C) 2013 Dale Weber. ALL Rights Reserved. License to be chosen.

	Author:		Dale Weber <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>

	Version:	0.3.0 (Unstable)
	Date:		10-Oct-2013
	Purpose:	Preliminary, VERY ALPHA release
	
	Requires:	Python v3.3.1 or later
				PyTZ 2013b or later

'''

# JSON Pretty Printer
import pprint

import json
import requests
import os

from datetime import datetime
from time import mktime, sleep, time

# You need the pytz 2013b version, or later
from pytz import utc, timezone

# ADN Imports
from ADN_Authenticator import ADN_Authenticator
from ADN_Channel import ADN_Channel

# DCS Imports
from DCS_Device import DCS_Device

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

'''
	Delete all the messages!
'''
def deleteAllMessages (channel, account):
	status = True

	messagesLen = len(channel.messages)

	if (messagesLen > 0):
		index = 0

		print ()
		print ("Deleting ALL messages for account '" + account + "' on channel " + channel.chanID + "!")
		print ("There are " + str(messagesLen) + " messages on channel " + channel.chanID + ".")
		print ()

		for index in range(messagesLen):
			msg = channel.messages[index]

			owner = msg["user"]
			creator = owner["username"]

			if (account == creator):
				msgid = msg["id"]

				status = channel.delete(msgid)

				if (status):
					print ("    Message #" + msgid + " for account '" + account + "' has been deleted.")
					index += 1

					if (index == messagesLen):
						messagesLen = len(channel.messages)

						if (index >= messagesLen) and (messagesLen > 0):
							index = 0
						else:
							index = messagesLen + 1
				else:
					print ("ERROR: " + str(patter.operationErrorCode) + ", " + patter.operationResultText)
					status = False
					break
			else:
				print ("    Message #" + msgid + " was created by account '" + creator + "', not account '" + account + "' - can not delete!")
	else:
		print ("    There are no messages on channel " + channel.chanID + " to delete!")
		status = True

	return status

def clearScreen ():
    os.system(['clear','cls'][os.name == 'nt'])

    return None

local_tz = getTimeZone()
local_timezone = timezone(local_tz)

'''
	Initialization
'''
dcsVersion = "0.3.0 (Unstable, 10-Oct-2013)"
clearScreen()

print ("======================================================================")
print ()
print ("Device Control System Master v" + dcsVersion)
print ("Copyright (C) 2013 Dale Weber. ALL Rights Reserved")
print ("   <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>")
print ()
print ("======================================================================")

'''
	Classes
'''

'''
	Class for the regular controller(s) on the network
'''
class DCS_Controller(DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None
'''
	End of Class DCS_Controller()
'''

'''
	Yes, robots are also devices!
'''
class DCS_Robot(DCS_Device):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

'''
	End of Class DCS_Robot(DCS_Device)
'''

'''
	Class for the MASTER controller(s) on the network - there should be only ONE
'''
class DCS_Master(DCS_Controller):
	def __init__ (self, adnauth, mname, mnet, mserv, mcheck, mpassword=None, mkey=None):
		super().__init__(adnauth, mname, mnet, mserv, mcheck, mpassword, mkey)

		return None

	'''
		Check to see if we have an authorized device, and send a
			command to them.
	'''
	def sendAuthenticatedMessage (self, aNote, toFQN):
		status = True
		msgid = None

		nrDevices = len(self.myDevices)

		if (nrDevices > 0):
			validated = False
			foundDevice = None
			index = 0

			while (not validated) and (index < nrDevices):
				validated = False
				device = self.myDevices[deviceIndex]
				self.setDevice(device)

				if (self.deviceGotAuthenticated) and (self.deviceFQN == toFQN):
					deviceAuthInfo = self.deviceAuthorization
					validated = deviceAuthInfo["valid"]

				if (validated):
					foundDevice = device
					deviceIndex = index

				index += 1

		if (validated):
			# We found our device, and they have authorization information
			#	for us. Send the command.
			aType = self.annotationType(aNote)
			aValue = aNote["value"]

			self.setDevice(foundDevice)

			status, msgid = send(toFQN, [ aType ], aNote, self.deviceAuthorization)

			if (msgid == None):
				self.displayError("run", 9999, "I could not send the message to " + self.deviceFQN)
				status = False

		return ( status, msgid )

	'''
		Parses the result.text from the last read() call
	'''
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
		Check the messages list for anything we may have missed.

		This routine should NOT be run too often, since it uses considerable
			processing time on a device.
	'''
	def checkMessages (self):
		status = True
		msgid = None

		# This is our new device check list
		newFQN = []

		# We want to make a list of any devices we don't already know about
		for msg in self.channel.messages:
			annotations = msg["annotations"]

			# This is ALWAYS the "address" annotation
			aNote = annotations[0]
			aValue = aNote["value"]

			fromFQN = aValue["dfrom"]

			'''
				Check to see if this device is already in our list. We
					don't use checkDevice() here, because it automatically
					adds new devices to our devices list. We just want to
					know if it is in our devices list now, but not to add it.
			'''
			deviceIndex, device = findDevice(fromFQN)

			if (deviceIndex == None) and (device == None):
				# No, we now know this device is new to us. Now we can add it
				deviceIndex, device = self.checkDevice(fromFQN)

				# Make a list of new devices we find.
				newFQN.append(fromFQN)

		'''
			Yes, we have to go through the complete messages list again.\

			This time we process messages addressed to us, broadcast messags, or
				from new devices.
		'''
		msgIndex = 0

		while (msgIndex < self.channel.messagesCount):
			msg = self.channel.messages[msgIndex]
			# We have to go through the newFQN list for each mesasge
			status = False
			msgid = None
			fqnIndex = 0
			lenNewFQN = len(newFQN)

			while (not status) and (msgid == None) and (fqnIndex < lenNewFQN):
				if (isBroadcastMessage(msg) or isMessageTo(msg, self.myFQN)) and isMessageFrom(msg, newFQN[fqnIndex]):
					# We missed this message, so process it as if it just arrived
					status, msgid = self.process(msg)

				fqnIndex += 1

			msgIndex += 1

		return status

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

			msg = self.get(self.myFQN)

			if (msg == None):
				print ("There aren't any new messages for me to process.")
				readMessages = True
			else:
				status = self.process(msg)
				
				if (status):
					msgid = msg["id"]
					print ("Message " + msgid + " was processed successfully.")
				else:
					self.displayError("run", 9999, "There was a problem processing this message.")

				self.showDevices()

			if (self.running):
				# Check the Pending Tasks list
				task = self.checkPendingTasks()

				# Check the Pending Actions list
				action = self.checkPendingActions()

				self.showDevices()
				
				if (readMessages):
					# Try reading more messages from the channel, if none were processed on this pass
					print ("Looking for new messages to process..")
        
					newMessageCount = self.extractMessageData()

					if (self.debugging):
						self.parseReadResult(2)

					readMessages = False

				# Validate the devices list and make sure we have the authorization
				#	information we need.
				self.validateDevices()

				# Shutdown the network
				self.shuttingDown = True

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

		# We want to watch what comes in on messages
		self.debuggingAddress = True
#		self.debuggingDevices = True
#		self.debuggingProcess = True

		# Every device has to announce themselves on the network
		toFQN = "all"
		status, msgid = self.send(toFQN, [ "announce" ])

		if (msgid == None):
			self.weGoofed(1, "Announce", toFQN)
		else:
			print ("Announce message has been sent!")

		# Write out some test messages to be processed
		self.writeTestMessages()

		# Read messages from the channel
		newMessageCount = self.extractMessageDatad()

		if (self.debugging):
			self.parseReadResult(1)
		
		print ()
		print ("Entering run mode..")
		print ()

		return ( status, msgid )

	'''
		Houston, we have a problem..
	'''
	def weGoofed (self, mNr, mType, toFQN):
		print ("[" + self.myName + "] ERROR: (" + str(mNr) + ") type " + mType + ", code " + str(self.channel.operationErrorCode) + " to " + toFQN)
		print ("Result = " + self.channel.operationResultText)
		print ()

		return None

	'''
		Write out some test messages to be processed.
	'''
	def writeTestMessages (self):
		toFQN = "pod.hybotics.org"
		self.myRequest = "led"
		self.myRequestParams = [ "green", "red" ]
		self.myRequestData = { "green" : "on", "red" : "off" }

		status, msgid = self.send(toFQN, [ "request" ])

		if (msgid == None):
			self.weGoofed(1, "Request", toFQN)
		else:
			print ("Request message " + msgid + " was sent to " + toFQN + "!")

		return status

	'''
		Populate the channel with some messages we can play with and process.
	'''
	def populateChannelMessages (self):
		status = True
		print ("Populating channel " + self.channel.chanID + " with messages!")

		msgNr = 1
		master.myCommand = "reboot"
		master.myCommandParams = [ "now" ]
		status = master.send("intrepid.hybotics.org", ["command"])

		if (not status):
			weGoofed(msgNr, "Command", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		status = intrepid.send("master.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "master.hybotics.org")

		msgNr += 1
		status = intrepid.send("pod.hybotics.org", ["authorize"])

		if (not status):
			weGoofed(msgNr, "Authorize", "pod.hybotics.org")

		msgNr += 1
		quark.send("pod.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Authorize", "pod.hybotics.org")

		msgNr += 1
		pod.myResponseDataType = "sensors"
		pod.myResponseData = {
			"distance" : "cm",
			"infrared" : 15,
			"ultrasonic" : 14,
			"temperature" : 56,
			"humidity" : 90,
			"barometer" : 29.69
		}
		pod.send("quark.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "quark.hybotics.org")

		msgNr += 1
		pod.mySecurityPassword = pod.myPassword
		pod.myRequest = "use"
		pod.myRequestParams = [ "laser", "relative" ]
		pod.myRequestData = { "elevation" : 10, "rotate" : -15, "fire" : 1 }
		status = pod.send("intrepid.hybotics.org", ["announce", "security", "request"])

		if (not status):
			weGoofed(msgNr, "Announce Security", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.mySecurityPassword = intrepid.myPassword
		intrepid.send("pod.hybotics.org", ["announce", "security"])

		if (not status):
			weGoofed(msgNr, "Announce Security", "pod.hybotics.org")

		msgNr += 1
		pod.myRequest = "move"
		pod.myRequestParams = [ 250 ]					# Metric: 1 = mm, 10 = cm, 250 = 1/4m,
														# 	500 = 1/2m, 1000 = 1m
														# English: 1 = inches, 12 = feet
														#	36 = yards, 5280 * 12 = miles
		pod.myRequestData = { "distance" : 2, "bearing" : 270, "speed" : 2 }
		status = pod.send("intrepid.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		status = intrepid.send("pod.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "pod.hybotics.org")

		msgNr += 1
		quark.myRequest = "read"
		quark.myRequestParams = [ "temperature", "humidity" ]
		quark.myRequestData = {}
		status = quark.send("pod.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "pod.hybotics.org")

		msgNr += 1
		pod.myResponseDataType = "sensors"
		pod.myResponseData = { "temperature" : 69, "humidity" : 53 }
		status = pod.send("quark.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response","quark.hybotics.org" )

		msgNr += 1
		status = quark.send("master.hybotics.org", ["announce"])

		if (not status):
			weGoofed(msgNr, "Announce", "master.hybotics.org")

		msgNr += 1
		quark.myRequest = "move"
		quark.myRequestParams = [ "arm", "relative" ]
		quark.myRequestData = { "base" : -10, "shoulder" : 5, "elbow" : -5, "wrist" : 5, "rotate" : -10, "gripper" : "open" }
		status = quark.send("intrepid.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		intrepid.send("quark.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "quark.hybotics.org")

		msgNr += 1
		master.myPrivacy = True
		master.send("quark.hybotics.org", ["control"])

		if (not status):
			weGoofed(msgNr, "Control", "quark.hybotics.org")

		msgNr += 1
		intrepid.myRequest = "use"
		intrepid.myRequestParams = [ "airgun", "absolute" ]
		intrepid.myRequestData = { "elevation" : 40, "rotate" : -30, "fire" : 3 }
		status = intrepid.send("quark.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "quark.hybotics.org")

		msgNr += 1
		quark.myResponseDataType = "boolean"
		quark.myResponseData = { "value" : True }
		status = quark.send("intrepid.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "intrepid.hybotics.org")

		msgNr += 1
		starbase.send("master.hybotics.org", ["announce"])

		if (not status):
			weGoofed(msgNr, "Announce")

		msgNr += 1
		master.myCommand = "reset"
		master.myCommandParams = [ "sensors" ]
		status = master.send("intrepid.hybotics.org", ["command"])

		if (not status):
			weGoofed(msgNr, "Command", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		status = intrepid.send("master.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "master.hybotics.org")

		msgNr += 1
		quark.myRequest = "search"
		quark.myRequestParams = [ "gripper" ]
		quark.myRequestData = { "get" : "ball", "color" : "blue" } 
		status = quark.send("intrepid.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "intrepid.hybotics.org")

		msgNr += 1
		master.myPrivacy = True
		master.myCommand = "reset"	
		master.myCommandParams = [ "airgun", "arm" ]
		status = master.send("quark.hybotics.org", ["command", "control"])

		if (not status):
			weGoofed(msgNr, "Command Control", "quark.hybotics.org")

		msgNr += 1
		intrepid.myErrorCode = 2001
		status = intrepid.send("master.hybotics.org", ["error"])

		if (not status):
			weGoofed(msgNr, "Error", "master.hybotics.org")

		msgNr += 1
		master.myCommand = "home"
		master.myCommandParams = [ "now" ]
		status = master.send("pod.hybotics.org", ["command"])

		if (not status):
			weGoofed(msgNr, "Command", "pod.hybotics.org")

		msgNr += 1
		pod.myResponseDataType = "boolean"
		pod.myResponseData = { "value" : True }
		status = pod.send("quark.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "quark.hybotics.org")

		msgNr += 1
		intrepid.send("pod.hybotics.org", ["private"])

		if (not status):
			weGoofed(msgNr, "Private Nessage", "pod.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		intrepid.send("quark.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "quark.hybotics.org")

		msgNr += 1
		quark.myResponseDataType = "boolean"
		quark.myResponseData = { "value" : False }
		quark.send("master.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "master.hybotics.org")

		msgNr += 1
		quark.myErrorCode = 1019
		quark.send("master.hybotics.org", ["error"])

		if (not status):
			weGoofed(msgNr, "Error", "master.hybotics.org")

		msgNr += 1
		master.myRequest = "use"
		master.myRequestParams = ["camera", "video", "hd"]
		master.myRequestData = { "length" : 5, "units" : "minutes" }
		master.send("intrepid.hybotics.org", ["request"])

		if (not status):
			weGoofed(msgNr, "Request", "intrepid.hybotics.org")

		msgNr += 1
		intrepid.myResponseDataType = "boolean"
		intrepid.myResponseData = { "value" : True }
		intrepid.send("master.hybotics.org", ["response"])

		if (not status):
			weGoofed(msgNr, "Response", "master.hybotics.org")

		print ()
		print ("Total messages written to channel " + self.channel.chanID + ": " + str(msgNr))
		print ()

		return status
'''
	End of Class DCS_Master(DCS_Controller)
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
#print ("Connecting to Patter channel " + patterChannel)

# Connect to our Patter channel
#patter = ADN_Channel(adn)							# Get a channel object
#status = patter.info(patterChannel)					# REQUIRED when not creating a channel

print ()
print ("Creating shuttle.hybotics.org, a network Controller")
print ()

'''
	This is the DCS Master accessor for the channel and device functions. It allows
		getting in and doing control and maintenence functions, displaying internal
		variables, displaying and listing messages, etc.
'''

shuttleName = "shuttle"
shuttleNetwork = "hybotics.org"
shuttleChecktype = "crc64"
shuttlePassword = "wV&3m7THsSK45Ew93@qcPtY-f"
shuttlePubKey = None
shuttleResources = ["fixed", "controller", "wifi" ]

shuttle = DCS_Master(adn, shuttleName, shuttleNetwork, shuttleResources, shuttleChecktype, shuttlePassword, shuttlePubKey)

status = shuttle.connect(patterChannel)

if (status):
	shuttle.show()

	print ("======================================================================")

	shuttle.run()
else:
	print ("I am unable to run, due to an error ocurring while trying to connect to channel " + patterChannel + "!")

#	print ("Starting File API test..")
#	print ()

#	myFileName = "pod_hybotics_org.settings"
#	myFileType = "net.hybotics.dcs.file.setttings"
#	myFileMimeType = "text/plain"
#	myFileID = "212674"
#	myFileToken = "arb-0gcjRV1VcDfAnNlum7xxY8zjjHIpl8GmzKlHVWpM70wNBy3mUprB2txZ52M5KqNuVfyCaGOQWEqIH97D0_8__TMl_VBnhb2qzBZETWFTkXl4k7sXO65QsYqklCgq2lhXt7DjBRpvdhexkloKaB3ZP3S57evVtXGKY2-RAO5ITlHt5d4zvM5d6DKHx5wKK"

#	settingsFile = ADN_File(adn)

#	print ("Creating file " + myFileName + " with ID " + myFileID)
#	result = settingsFile.create(myFileName, myFileType, False, myFileMimeType)
#	print ("Result of file creation = " + result)

#	print ("Opening file " + myFileName + " with ID " + myFileID)
#	result = settingsFile.open(myFileID)
#	print ("Result of open = " + result)

#	print ("======================================================================")
#	print ()

'''
	This is the monitoring loop. There will eventually be some sort of Curses or other
		GUI wrapped around this code, as the DCS software grows. Right now, this is
		just a very bare minimum for monitoring what is happening in an "internet of
		things" I have here, or that you might have.
'''

'''
print ("Entering channel watch loop..")
print ()

loopDelaySec = 5
error = False
status = True

while True:
	# Read new message(s) and display them
	status = patter.read()

	if (status == True) or (status == None):
		# List the last messages read
		patter.list()

		if (status == True):
			error_location = "NO ERROR"
			# Delete ALL messages on the channel created by the current account
			status = deleteAllMessages(patter, adn.username)

			if (status):
				sleep(loopDelaySec)
			else:
				error_location = "DELETION"
				error = True

	if (error):
		print ("ERROR on " + error_location + ", code = " + str(patter.operationErrorCode) + "!")
		print ()
		print ("JSON = "'' + patter.operationResultText + "'")
		error = False

	sleep(loopDelaySec)

else:
	print ("There was an error trying to connect to Patter channel " + patterChannel + "!")
'''
