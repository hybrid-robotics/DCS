'''
	Program:	DCS_Device.py, the main class for the Device Control System.
				This class defines ALL devices using the Device Control System.

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
from ADN_Channel import ADN_Channel

# DCS Imports

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
	Globals
'''

local_tz = getTimeZone()
local_timezone = timezone(local_tz)

'''
	This is the class that defines a device. All device classes must inherit from this
		class.
'''
class DCS_Device():
	'''
		Class variables - these are accessible from the outside, using dot notation.
	'''

	'''
		This is our local DCS Message List. We extract just the information
			we need from each App.Net message. The contents of annotation[0],
			which is always the "address" annotation, is put in the main part
			of our message, since it is accessed so often. There is no longer
			a need to access annotation[0] after the message information has
			been extracted.

			dcsMessage = {
				"id" :						App.Net Message ID
				"cdate" :					App.Net Creation Date
				"dfrom" :					DCS From Address
				"dto" :						DCS To Address
				"private" :					DCS Message Private Flag
				"authorization" :			DCS Authorization Information
				"anotes" :					App.Net Annotations
				"text" :					App.Net Message Text
				"username" :				App.Net User Name
				"userid" :					App.Net User ID
			}
	'''
	dcsMessageList = []
	dcsMessageCount = 0
	dcsMessageIndex = 0

	# Set True in processAddress() if the device is authenticated
	connectionAuthorized = False

	# This will be set True to shutdown the network
	shuttingDown = False

	# We start out running!
	running = True

	# Set True to enable pprint variable code
	debugging = False

	debuggingAddress = False
	debuggingAnnounce = False
	debuggingAuthorize = False
	debuggingCommand = False
	debuggingControl = False
	debuggingError = False
	debuggingRequest = False
	debuggingResponse = False
	debuggingSecurity = False

	debuggingDevices = False
	debuggingProcess = False
	debuggingSend = False

	# This is for pprint - pretty prints all types of variables.
	pp = None

	'''
		These are error variable results used in various routines
	'''
	operationErrorCode = None
	operationErrorMessage = None
	operationErrorSlug = None
	operationErrorID = None
	operationResultText = None

	'''
		These variables tell all about me.
	'''
	myName = ""
	myNetwork = ""
	myAccount = ""
	myFQN = ""
	myChannel = ""
	myResources = []

	# For location (myLocation)
	myLocationDescription = "Outside, in the rose garden"
	myLattitude = None
	myLongitude = None

	# For status (myStatus)
	myCondition = "idle"							# "busy", "down", "idle", "working"
	myTemperature = 95
	myUnits = "metric"

	myDataCheckType = "crc64"
	myCRC = "0x0F9D250A"

	# For annotation type: net.hybotics.dcs.address
	myPrivacy = False
	myAuthorizationValid = False
	myAuthorization = {}

	'''
	***	Variables used to fill up the DCS annotations
	'''
	# For annotation type: net.hybotics.dcs.announce
	myAnnounceNumber = 0

	# For annotation type: net.hybotics.dcs.authorize
	myAuthorizeNumber = 0

	# For annotation type: net.hybotics.dcs.command
	myCommand = "shutdown"
	myCommandParams = [ "now" ]
	myCommandNumber = 0

	# For annotation type: net.hybotics.dcs.control
	myControl = "bits"
	myControlParams = [ "xor" ]
	myControlData = { "port" : "A", "mask" : "0xC0D1" }
	myControlNumber = 0

	# for annotation type: net.hybotics.dcs.error
	myErrorCode = 9012
	myErrorNumber = 0

	# For annotation type: net.hybotics.dcs.private
	myPackageType = "hex"
	myPackage = { "value" : "0x0FD4F67CEC2D331F" }
	myPrivateNumber = 0

	# For annotation type: net.hybotics.dcs.request
	myRequest = "read"
	myRequestParams = [ "sensors" ]
	myRequestData = { "value" : "all" }
	myRequestNumber = 0

	# For annotation type: net.hybotics.dcs.response
	myResponseDataType = "hex"
	myResponseData = { "value" : "0xFFF0D19A025F764E" }
	myResponseDataPackage = {}
	myResponseCheckType = "crc64"
	myResponseTo = 0
	myResponseType = "any"
	myResponseNumber = 0
	myResponseFinal = True

	# For annotation type: net.hybotics.dcs.security
	mySecurityType = "password"
	mySecurityNumber = 0
	mySecurityPassword = ""
	myPassword = ""
	myPublicKey = None

	'''
	***	Other data used in messages
	'''
	# For my permissions (myPermissions)
	myCommandOK = True
	myControlOK = False

	myPermissions = {
		"command" : myCommandOK,
		"control" : myControlOK
	}

	myLocation = {}

	myStatus = {}

	'''
	***	Message types to be sent or received.
	'''
	dcsAddress = {}
	dcsAnnounce = {}
	dcsAuthorize = {}
	dcsCommand = {}
	dcsControl = {}
	dcsError = {}
	dcsPrivateMessage = {}
	dcsRequest = {}
	dcsResponse = {}
	dcsSecurity = {}

	'''
	***	For device list support - other devices we are aware of and may be
	***		authorized to communicate directly with.
	'''
	deviceName = None
	deviceNetwork = None
	deviceFQN = None
	deviceGotAuthenticated = False

	deviceGotAnnounce = False
	deviceGotAuthorize = False
	deviceGotSecurity = False

	deviceCondition = None
	deviceChannel = None
	deviceResources = None
	deviceDataCheck = None
	deviceUnits = None
	deviceLocation = None
	devicePublicKey = None
	devicePassword = None
	deviceCommandOK = False							# True if the "command" message is OK
	deviceControlOK = False							# True if the "control" message is OK

	deviceWeSentAuthorize = False
	deviceWeSentSecurity = False

	deviceAuthorizationValid = False
	deviceSecurityType = "password"
	deviceSecurityPassword = None

	deviceAuthorization = {
		"valid" : deviceAuthorizationValid,
		"security" : deviceSecurityType,
		"password" : deviceSecurityPassword,
		"pubkey" : devicePublicKey 
	}

	# Counts authorized devices
	myDevicesCount = 0

	# Index count into the myDevices[] list
	myDevicesIndex = 0

	# A list of devices we are aware of, as well a authorized devices
	myDevices = []

	# How many seconds to sleep at the end of a run through the run loop
	delayRunLoop = 3

	yourFQN = ""

	lastMessageDisplayed = 0
	lastMessageListed = 0

	messagesCount = 0

	# Delay between API operations
	delaySecondsAPI = 3

	delaySend = 3

	'''
		The Pending Actions List - stores information on all actions ("command", "control",
			and "request" messages) that have not received a response yet.

			action = {
				"type" :		The type of action ("command", "control", or "request")
				"timestamp" :	Time in seconds since the epoch [ int(time.time()) ],
				"msgid" :		The message ID of the message this action pertains to,
				"fqn" :			The FQN (Fully Qualified Name) this message was sent to,
				"annotation" :	The actual annotation within the message.
			}
	'''
	myPendingActions = []
	myPendingActionsCount = 0

	'''
		The Pending Tasks List - stores information about all tasks ("command", "control",
			"request") we have not completed.

			task = {
				"type" :		The type of action ("command", "control", or "request")
				"timestamp" :	Time in seconds since the epoch [ int(time.time()) ],
				"msgid" :		The message ID of the message this action pertains to,
				"fqn" :			The FQN (Fully Qualified Name) of the sending device,
				"annotation" :	The actual annotation within the message.
			}
	'''
	myPendingTasks = []
	myPendingTasksCount = 0

	# This is a DEBUG variable, and it will eventually go away
	writeResultText = ""

	'''
		Code starts here.
	'''

	'''
		Class Constructor.
	'''
	def __init__(self, adnauth, mname, mnet, mresources, mcheck, mpassword=None, mkey=None):
		self.myADN = adnauth
		self.myName = mname
		self.myNetwork = mnet
		self.myAccount = adnauth.username
		self.myFQN = self.myName + "." + self.myNetwork
		self.myPublicKey = mkey
		self.myDataCheckType = mcheck
		self.myResources = mresources
		self.myPassword = mpassword

		# Setup our pretty printer for variables
		self.pp = pprint.PrettyPrinter(indent=4)

		return None

	'''
	***	Here is a nice little set of routines for working with annotations
	***		and messages.
	'''

	'''
		Returns a string of a parameters list
	'''
	def annotationParameters (self, params):
		st = params[0]
		pLen = len(params)
		index = 1

		while (index < pLen):
			st = st + ", " + params[index]
			index += 1

		return st

	'''
		Returns a string of the annotation permissions
	'''
	def annotationPermissions (self, perms):
		if (self.debugging):
			print ("(annotationPermissions) perms:")
			self.pp.pprint(perms)

		st = "Command: " + self.annotationTrueFalse(perms["command"], "True", "False") + ", Control: " + self.annotationTrueFalse(perms["control"], "True", "False")

		return st

	'''
		Returns a string holding the type of an annotation
	'''
	def annotationType (self, aNote):
		aType = aNote["type"]
		temp = aType.split(".")
		aType = temp[3]

		return aType

	'''
		Returns a string list of all the resources provided by a device
	'''
	def annotationResources (self, resources):
		resourcesLen = len(resources)

		resourceStr = "None"

		if (resourcesLen > 0):
			resourceStr = "[ " + resources[0]

			index = 1

			while (index < len(resources)):
				resourceStr = resourceStr + ", " + resources[index]
				index += 1

			resourceStr = resourceStr + " ]"

		return resourceStr

	'''
		Returns a string for a boolean value
	'''
	def annotationTrueFalse (self, tf, itrue, ifalse):
		if (tf == True):
			st = itrue
		elif (tf == False):
			st = ifalse
		else:
			st = "None"

		return st

	'''
		Returns "None" or the value of zilch - handles the possibility of a string = None
	'''
	def annotationZilch (self, zilch):
		if (zilch == None):
			st = "None"
		else:
			st = zilch

		return st

	'''
		Show an annotation
	'''
	def displayAnnotation (self, aNote):
		status = True

		aType = self.annotationType(aNote)
		aValue = aNote["value"]

		print ("  Annotation:")
		print ("    Type:          " + aNote["type"])
		print ("    Number:        " + str(aValue["number"]))
		print ("    FQN:           " + aValue["fqn"])

		if (aType == "announce"):
			print ("    Resources:     " + self.annotationResources(aValue["resources"]))
		elif (aType == "authorize"):
			print ("    Network:       " + aValue["network"])
			print ("    Data Check:    " + aValue["datacheck"])
			print ("    Permissions:   " + self.annotationPermissions(aValue["perms"]))
		elif (aType == "command"):
			print ("    Command:       " + aValue["command"])
			print ("    Parameters:    " + self.annotationParameters(aValue["params"]))
		elif (aType == "control"):
			print ("    Control:       " + aValue["control"])
			print ("    Parameters:    " + self.annotationParameters(aValue["params"]))
			print ("    Data:          " + aValue["data"])
		elif (aType == "error"):
			print ("    Error:         " + str(aValue["error"]))
		elif (aType == "private"):
			print ("    Type:          " + aValue["type"])
			print ("    Package:       " + aValue["package"])
		elif (aType == "request"):
			print ("    Request:       " + aValue["request"])
			print ("    Parameters:    " + self.annotationParameters(aValue["params"]))
			print ("    Data:          " + str(aValue["data"]))
		elif (aType == "response"):
			print ("    Response To:   " + str(aValue["respto"]))
			print ("    Response Type: " + aValue["resptype"])
			print ("    Ack:           " + self.annotationTrueFalse(aValue["ack"], "Ack", "Nack"))
			print ("	Data:          " + aValue["data"])
		elif (aType == "security"):
			print ("    Type:          " + aValue["type"])
			print ("    Password:      " + aValue["password"])
			print ("    Public Key:    " + self.annotationZilch(aValue["pubkey"]))
			
		print ()

		if (aType in [ "announce", "error", "response" ]):
			aStatus = aValue["status"]
			self.displayDeviceStatus(aStatus)

		return status

	'''
		Returns True, if a message is a broadcast message (addressed to "all")
	'''
	def isBroadcastMessage (self, dcsMsg):
		toFQN = dcsMsg["dto"]

		status = (toFQN == "all")

		return status

	'''
		Returns True, if this message is from deviceFQN
	'''
	def isMessageFrom (self, dcsMsg, deviceFQN):
		fromFQN = dcsMsg["dfrom"]

		status = (deviceFQN == fromFQN)

		return status

	'''
		Returns the value of the "private" field in the "address" annotation
	'''
	def isPrivateMessage (self, dcsMsg):
		status = dcsMsg["private"]

		return status

	'''
		Returns True, if this message is to deviceFQN
	'''
	def isMessageTo (self, dcsMsg, deviceFQN):
		toFQN = dcsMsg["dto"]

		status = (deviceFQN == toFQN)

		return status
	'''
	***	End of annotation and message utilities
	'''

	'''
	***	Start of Pending Action List routines
	'''

	'''
		Add a new action to the Pending Actions List
	'''
	def addPendingAction (self, action, msgid, fqn, annotation):
		status = True
		timestamp = 0

		newAction = {
			"type" : action,
			"timestamp" : timestamp,
			"msgid" : msgid,
			"fqn" : fqn,
			"annotation" : annotation
		}

		self.myPendingActions.append(newAction)
		self.myPendingActionsCount += 1

		return status

	'''
		Check the pending tasks list for things we still need to do.
	'''
	def checkPendingActions (self):
		status = True
		msgid = None

		nrActions = len(self.myPendingActions)

		if (nrActions > 0):
			print ()
			print ("Checking pending actions..")

			self.showPendingActions()

			actionIndex = 0

			while (actionIndex < nrActions):
				action = self.myPendingActions[actionIndex]
				actionFQN = action["fqn"]

				print ("  Action #" + str(actionIndex) + " (of " + str(nrActions) + " actions) for " + actionFQN)

				deviceIndex, device = self.checkDevice(actionFQN)
				self.setDevice(device)

				# Is this device a device?
				if (self.deviceGotAuthenticated):
					# Yes, so execute this action
					print ("  Executing action #" + str(actionIndex) + " for device " + actionFQN)
					self.executePendingAction(action)

				actionIndex += 1
			
		return ( status, msgid )

	def executePendingAction (self, action):
		status = True
		msgid = None

		actionFQN = action["fqn"]
		actionMsgID = action["msgid"]
		actionType = action["type"]

		message = self.channel.find(actionMsgID)

		if (message == None):
			# Message was not found
			self.displayError("executePendingAction", 9999, "Message " + actionMsgID + " was not found")
			status = False
		else:
			# Process the message, just like we just received it
			msgid = message["id"]
			status = self.process(message, True)

			if (status):
				# Remove this action from the pending tasks list
				self.removePendingAction(action)
			else:
				self.displayError("executePendingAction", 9999, "There was a problem processing a pending action (" + actionType +  ") for " + actionFQN + " in message " + actionMsgID)
				status = False

		return ( status, msgid )

	'''
		Find a pending action by, message ID, in the Pending Actions list
	'''
	def findPendingAction (self, msgid, atype):
		foundIndex = None
		index = 0

		while (foundIndex == None) and (index < self.myPendingActionsCount):
			action = self.myPendingActions[index]

			if (action["msgid"] == msgid) and (action["type"] == atype):
				foundIndex = index

			index += 1

		return foundIndex 

	'''
		Remove a pending action
	'''
	def removePendingAction (self, action):
		status = True

		self.myPendingActions.remove(action)
		self.myPendingActionsCount -= 1

		return status

	'''
		Show the pending actions list
	'''
	def showPendingActions (self):
		status = True
		actionsLen = len(self.myPendingActions)

		if (actionsLen > 0):
			print ()
			print ("My Pending Actions:")
			print ()

			for action in self.myPendingActions:
				print ("  Type:           " + action["type"])
				print ("  Timestamp:      " + str(action["timestamp"]))
				print ("  Message ID:     " + action["msgid"])
				print ("  FQN:            " + action["fqn"])
				print ()

				self.displayAnnotation(action["annotation"])
			
		return status
	'''
	***	End of Pending Action List routines
	'''

	'''
	***	Start of Pending Task List routines
	'''

	'''
		Add a new task to the Pending Tasks List
	'''
	def addPendingTask (self, taskType, msgid, fqn, annotation):
		status = True
		timestamp = 0

		newTask = {
			"type" : taskType,
			"timestamp" : timestamp,
			"msgid" : msgid,
			"fqn" : fqn,
			"annotation" : annotation
		}

		self.myPendingTasks.append(newTask)
		self.myPendingTasksCount += 1

		return status

	'''
		Check the pending tasks list for overdue things.
	'''
	def checkPendingTasks (self):
		status = True
		msgid = None

		nrTasks = len(self.myPendingTasks)

		if (nrTasks > 0):
			print ()
			print ("Checking pending tasks..")

			self.showPendingTasks()

			taskIndex = 0

			# Search for a task that matches
			while (taskIndex < nrTasks):
				task = self.myPendingTasks[taskIndex]
				taskFQN = task["fqn"]
				taskType = task["type"]
				taskMsgID = task["msgid"]

				print ("  Task #" + str(taskIndex) + " (of " + str(nrTasks) + " tasks) for " + taskFQN)

				deviceIndex, device = self.checkDevice(taskFQN)

				# Is this device a device?
				if (self.deviceGotAuthenticated):
					# Yes, so execute this task
					print ("  Executing task #" + str(taskIndex) + " for device " + taskFQN)
					status, msgid = self.executePendingTask(taskFQN, taskType, taskMsgID, task)

				taskIndex += 1

		return ( status, msgid )

	'''
		Execute a pending task for a devicely device
	'''
	def executePendingTask (self, taskFQN, taskType, taskMsgID, task):
		status = True
		msgid = None

		if (self.debugging):
			print ("(executePendingTask) taskFQN = " + taskFQN + ", taskType = " + taskType + ", taskMsgID = " + taskMsgID)
			print ("(executePendingTask) task:")
			self.pp.pprint(task)

		message = self.channel.find(taskMsgID)

		if (message == None):
			# Message was not found
			self.displayError("executePendingTask", 9999, "Message " + taskMsgID + " was not found")
		else:
			# Process the message, just like we just received it
			if (self.debugging):
				print ("Processing message " + message["id"] + " (" + taskType + ", " + taskMsgID + ")")

			status, msgid = self.process(message, True)

			if (msgid == None):
				self.displayError("executePendingTask", 9999, "There was a problem processing message " + taskMsgID)
			else:
				fromFQN = taskFQN
				msgid = taskMsgID
				aNote = task["annotation"]
				aType = self.annotationType(aNote)

				if (self.debugging):
					print ("(executePendingTask) aType = " + aType)
					print ()
					print ("(executePendingTask) showing aNote:")
					self.pp.pprint(aNote)

				if (status):
					# Remove this task from the pending tasks list
					self.removePendingTask(task)
				else:
					self.displayError("executePendingTask", 9999, "There was a problem processing a pending task (" + taskType +  ") for " + taskFQN + " in message " + taskMsgID)

		return ( status, msgid )

	'''
		Find a pending task, by message ID, in the Pending Actions list
	'''
	def findPendingTask (self, msgid, atype):
		foundIndex = None
		index = 0

		while (foundIndex == None) and (index < self.myPendingTasksCount):
			action = self.myPendingTasks[index]

			if (action["msgid"] == msgid):
				foundIndex = index

			index += 1

		return foundIndex 

	'''
		Remove a pending task
	'''
	def removePendingTask (self, task):
		status = True

		self.myPendingTasks.remove(task)
		self.myPendingTasksCount -= 1

		return status

	'''
		Show the pending tasks list
	'''
	def showPendingTasks (self):
		status = True
		tasksLen = len(self.myPendingTasks)

		if (tasksLen > 0):
			print ()
			print ("My Pending Tasks:")
			print ()

			for task in self.myPendingTasks:
				print ("  Type:           " + task["type"])
				print ("  Timestamp:      " + str(task["timestamp"]))
				print ("  Message ID:     " + task["msgid"])
				print ("  FQN:            " + task["fqn"])
				print ()

				self.displayAnnotation(task["annotation"])
			
		return status
	'''
	***	End of Pending Task List routines
	'''

	'''
		Connect to an App.Net channel, which must already exist.
	'''
	def connect (self, chanID):
		self.channel = ADN_Channel(self.myADN)

		status = self.channel.info(chanID)

		if (status):
			self.myChannel = chanID

		return status

	'''
		Display all messages, that have currently been read, in a detailed list
	'''
	def displayMyMessages (self):
		status = True
		dcsMsgCount = 0

		# Messages are already stored in ascending order
		for dcsMsg in self.dcsMessageList
			dcsTo = dcsMsg["dto"]

			if (self.myFQN == dcsTo):
				self.displayMessage(dcsMsg)

				# Count up the displayed messages
				dcsMsgCount += 1

		if (dcsMsgCount > 0):
			print ("Total messages displayed: " + str(dcsMsgCount))
			print ()

		return status

	'''
		Display a single message in detail
	'''
	def displayMessage (self, dcsMsg):
		status = True

		dcsAnnotations = dcsMsg["annotations"]
		alen = len(dcsAnnotations)

		dcsUser = dcsMsg["user"]
		dcsUserID = dcsMsg["userid"]
		dcsMsgDateUTC = dcsMsg["cdate"]

		timedate = local_datetime(dcsMsgDateUTC)
		time = timedate[1]

		print ("Message " + dcsMsg["id"] + ", created on " + timedate[0] + " at " + time.lower() + " " + timedate[2] + ": " + msg["text"])
		print ("  By: " + dcsUser + "(ID: " + dcsUserID + ")")

		if (alen > 0):
			print ("   There are " + str(alen) + " annotation(s):")

			# Display annotations - needs to be finished
			for aNote in dcsAnnotations:
				aType = self.annotationType(aNote)
				print ("      Type: " + aNote["type"])

				aValue = aNote["value"]

				# Display the information unique to each message type
				if (aType == "address"):
					print ("        Address:")
					print ("        (" + self.annotationTrueFalse(aValue["private"], "Private", "Public") + ") From: " + aValue["dfrom"] + ", To: " + aValue["dto"])
				elif (aType == "announce"):
					print ("        Announce:")
					print ("        FQN: " + aValue["fqn"] + ", Resources: " + self.annotationResources(aValue["resources"]))
				elif (aType == "authorize"):
					print ("Authorize:")
					perms = aValue["perms"]

					print ("        FQN: " + aValue["fqn"] + ", DataCheck: " + aValue["datacheck"] + ", Network: " + aValue["network"])
					print ("        Permissions: Command: " + self.annotationTrueFalse(perms["command"], "True", "False") + ", Control: " + self.annotationTrueFalse(perms["control"], "True", "False"))
				elif (aType == "command"):
					print ("        Command:")
				elif (aType == "control"):
					print ("        Control:")
				elif (aType == "error"):
					print ("Error:")
					print ("        Error Code: " + str(aValue["error"]))
				elif (aType == "private"):
					print ("        Private Message:")
				elif (aType == "request"):
					print ("        Request:")
				elif (aType == "response"):
					print ("        Response:")
				elif (aType == "security"):
					print ("Security:")
					print ("        FQN: " + aValue["fqn"] + ", Type: " + aValue["type"] + ", Password: '" + aValue["password"] + "', Public Key: " + self.annotationZilch(aValue["pubkey"]))

				# Display the status and location for the message types that include them.
				if (aType in ["announce", "error", "response"]):
					self.displayDeviceStatus(aValue["status"])

				print ()
		else:
			print ("   There are no annotations in this message.")

		return status

	'''
		Get channel info
	'''
	def info (self, chanID):
		status = True
		url = "https://alpha-api.app.net/stream/0/channels/" + chanID + self.accessToken

		result = requests.get(url)

		response = json.loads(result.text)

		meta = response["meta"]

		code = meta["code"]

		if (code == 200):
			self.setup(response)
		else:
			self.displayError("info", 9999, "Unhandled Error", meta)
			status = False

		return status

	'''
		This routine extracts just the information from each message that we
			need into a local list. We don't need to keep much information
			from each message.

			The dcsMessageList is rebuilt each time this routine is called.
	'''
	def extractMessageData (self):
		# Read messages from the channel
		msgCount = self.channel.read()

		self.dcsMessageList = []
		self.dcsMessageCount = 0
		self.dcsMessageIndex = 0

		for message in self.channel.messages:
			msgID = message["id"]
			msgDate = message["created_at"]
			msgText = message["text"]
			msgAnnotations = message["annotations"]

			'''
				This will ALWAYS be the "address" annotation. We break out
					all the information from the "address" annotation into
					the main part of the message to make it easier to get
					at, since we access this quite a lot.

					There is no longer any need to access annotation[0].
			'''
			addrAnnotation = msgAnnotations[0]
			addrValue = addrAnnotation["value"]
			addrFrom = addrValue["dfrom"]
			addrTo = addrValue["dto"]
			addrPrivate = addrValue["private"]
			addrAuthorization = addrValue["authorization"]

			msgUser = message["user"]
			msgUserName = msgUser["username"]
			msgUserID = msgUser["userid"]

			dcsMessage = {
				"id" : msgID,
				"cdate" : msgDate,
				"dfrom" : addrFrom,
				"dto" : addrTo,
				"private" : addrPrivate,
				"authorization" : addrAuthorization,
				"anotes" : msgAnnotations,
				"text" : msgText,
				"username" : msgUserName,
				"userid" : msgUserID,
			}

			dcsMessageList.append(dcsMessage)
			dcsMessageCount += 1

		return dcsMessageCount

	'''
		Find a message in the dcsMessageList, by message ID.
	'''
	def findMessage (self, dcsMsgID):
		status = True
		dcsFound = None
		dcsIndex = 0

		while (dcsFound == None) and (dcsIndex < self.dcsMessageCount):
			dcsMessage = dcsMessageList[dcsIndex]

		return status

	'''
		Get the next available sequential message, OR the next message for the recipient.

		Private messages are ignored when getting sequential messages.
	'''
	def getMessage (self, recipientFQN=None):
		foundMessage = None

		if (recipientFQN == None):
			# Get the next sequential NON private message
			if (self.dcsMessageIndex < self.dcsMessageCount):
				dcsIndex = self.dcsMessageIndex

				while (foundMessage == None) and self.isPrivateMessage(dcsMessage) and (dcsIndex < self.dcsMessageCount):
					# Get the next sequential message from the list
					dcsMsg = self.dcsMessageList[index]
					dcsIndex += 1
					
					if (not self.isPrivate(dcsMsg)):
						foundMessage = dcsMsg
		else:
			# Search for the next available message for the recipient
			if (self.dcsMessageIndex <= self.dcsMessageCount):
				dcsIndex = self.dcsMessageIndex

				while (foundMessage == None) and (dcsIndex < self.dcsMessageCount):
					dcsMsg = self.dcsMessageList[dcsIndex]
					dcsTo = dcsMsg["dto"]

					if (recipientFQN == dcsTo):
						# We found a message for the recipient
						foundMessage = dcsMsg

					dcsIndex += 1

				self.dcsMessageIndex = dcsIndex

		return foundMessage

	'''
	***	The following set of routines handles maintenence of the device
	***		list - those devices we are aware of.
	'''

	'''
		Add a new device

		Returns: the device record for the new device
	'''
	def addDevice (self, yname, ynet, ychannel, yresources, ycheck, ypassword, ylocation=None, ykey=None):
		self.initializeDevice()

		self.deviceName = yname
		self.deviceNetwork = ynet
		self.deviceChannel = ychannel
		self.deviceResources = yresources
		self.deviceDataCheck = ycheck
		self.deviceLocation = ylocation
		self.devicePassword = ypassword
		self.devicePublicKey = ykey
		self.deviceFQN = yname + "." + ynet

		self.mySecurityPassword = ""

		# This is a device that is new to us, not an authorized device yet
		newDevice = self.updateDevice()

		self.myDevices.append(newDevice)
		self.myDevicesCount += 1

		if (self.debuggingDevices):
			print ("(addDevice, exiting) newDevice:")
			self.pp.pprint(newDevice)

		return newDevice

	'''
		Check to see if we already have a device record for a device,
			and create one if not.

		Do not add ourselves to the devices list.

		Returns: the index into the devices list, and the device record
	'''
	def checkDevice (self, fqn):
		device = None
		deviceIndex = None

		if (fqn != "all") and (fqn != self.myFQN):
			deviceIndex, device = self.findDevice(fqn)

			if (self.debuggingDevices):
				print ("(checkDevice, entry) fqn = " + fqn)
				print ("(checkDevice, entry) deviceIndex:")
				self.pp.pprint(deviceIndex)
				print ("(checkDevice, entry) device:")
				self.pp.pprint(device)

			# We can't do this if we're sending a broadcast message (to == "all")
			if (deviceIndex == None) and (device == None):
				temp = fqn.split(".")
						
				self.deviceName = temp[0]
				self.deviceNetwork = temp[1] + "." + temp[2]
				self.deviceFQN = fqn

				device = self.addDevice(self.deviceName, self.deviceNetwork, "", [], "", "")

				deviceIndex, device = self.findDevice(fqn)

				self.setDevice(device)
				self.updateDevice(deviceIndex)
				
		if (self.debuggingDevices):
			print ("(checkDevice, before exit) fqn = " + fqn)
			print ("(checkDevice, before exit) deviceIndex:")
			self.pp.pprint(deviceIndex)
			print ("(checkDevice, before exit) device:")
			self.pp.pprint(device)

		# If there was no device found, deviceIndex must also be None
		if (device == None):
			deviceindex = None

		return ( deviceIndex, device )

	'''
		Check authentication for a device, and make sure everything that
			should be sent is or has been sent.
	'''
	def checkDeviceAuthentication (self, fqn):
		status = True
		msgid = None

		deviceIndex, device = self.checkDevice(fqn)

		if (deviceIndex == None) and (device == None):
			self.displayError("checkAuthentication", 9999, fqn + " was not found in my devices list")

		if (not self.deviceWeSentAuthorize) and (self.deviceNetwork == self.myNetwork):
			status, msgid = self.sendAuthorize(self.deviceFQN)

			if (msgid == None):
				self.displayError("checkAuthentication", 9999, "There was a problem sending authorization information to " + fqn)
			else:
				self.deviceWeSentAuthorize = True
				print ("Authorization request sent to " + self.deviceFQN)

		if self.deviceGotAuthorize and self.deviceWeSentAuthorize and (not self.deviceWeSentSecurity):
			status, msgid = self.sendSecurity(fqn)

			if (msgid == None):
				self.displayError("checkAuthentication", 9999, "There was a problem sending security information to " + fqn)
			else:
				self.deviceWeSentSecurity = True
				print ("Security information sent to " + self.deviceFQN)

		self.deviceGotAuthenticated = (self.deviceGotAuthorize and self.deviceGotSecurity and self.deviceWeSentAuthorize and self.deviceWeSentSecurity)

		if self.deviceGotAuthenticated:
			print ("Device " + self.deviceFQN + " has been authenticated!")

			self.deviceAuthorizationValid = True
			self.deviceSecurityPassword = self.devicePassword

			self.deviceAuthorization = {
				"valid" : self.deviceAuthorizationValid,
				"security" : self.deviceSecurityType,
				"password" : self.deviceSecurityPassword,
				"pubkey" : self.devicePublicKey 
			}

		# Check to see if the network is shutting down
		if self.deviceGotAuthenticated and self.shuttingDown and ("controller" in self.myResources) and (self.deviceNetwork == self.myNetwork):
			self.myCommand = "shutdown"
			self.myCommandParams = [ "now" ]

			status, msgid = self.send(self.deviceFQN, [ "command"] )

			if (msgid == None):
				self.displayError("checkAuthentication", 9999, "There was a problem sending the shutdown command to " + self.deviceFQN)

		self.updateDevice(deviceIndex)

		return ( status, msgid )

	'''
		Display the device list
	'''
	def displayDeviceList (self):
		dcsDeviceTotal = 0
		dcsAuthenticated = 0

		if (self.myDevicesCount > 0):
			print ()
			print ("My devices are:")
			print ()

			for device in self.myDevices:
				self.setDevice(device)

				print ("   Their FQN:           " + self.deviceFQN)
				print ("   Network:             " + self.deviceNetwork)
				print ("   Channel:             " + self.deviceChannel)
				print ("   DataCheck:           " + self.deviceDataCheck)
				print ("   Security type:       " + self.annotationZilch(self.deviceSecurityType))
				print ("   Password:            " + self.annotationZilch(self.devicePassword)
				print ()
				print ("   Fully Authenticated: " + self.annotationTrueFalse(self.deviceGotAuthenticated, "YES", "NO"))
				print ()
				print ("   Received Announce:   " + self.annotationTrueFalse(self.deviceGotAnnounce, "Yes", "No"))
				print ("   Received Authorize:  " + self.annotationTrueFalse(self.deviceGotAuthorize, "Yes", "No"))
				print ("   Received Security:   " + self.annotationTrueFalse(self.deviceGotSecurity, "Yes", "No"))
				print ()
				print ("   We sent Authorize:   " + self.annotationTrueFalse(self.deviceWeSentAuthorize, "Yes", "No"))
				print ("   We sent Security:    " + self.annotationTrueFalse(self.deviceWeSentSecurity, "Yes", "No"))
				print ()

				if (self.deviceResources == None):
					print ("   Resources:           None")
				else:
					print ("   Resources:           " + self.annotationResources(device["resources"]))

				location = self.deviceLocation

				if (location != None):
					print ("   Location:")
					print ("       Description:     " + location["description"])
					print ("       Lattitude:       " + self.annotationZilch(location["lattitude"]))
					print ("       Longitude:       " + self.annotationZilch(location["longitude"]))

				dcsDeviceTotal += 1

				print ()

				if (self.deviceGotAuthenticated):
					dcsAuthenticated += 1

			if (dcsAuthenticated > 0):
				self.myDevicesCount = dcsAuthenticated
				print ("       I know " + str(dcsAuthenticated) + " authenticated devices.")
				print ("       I am aware of a total of " + str(dcsDeviceTotal) + " devices.")

			print ()

		return dcsDeviceTotal

	'''
		Display a device's status
	'''
	def displayDeviceStatus (self, deviceStatus):
		status = True

		print ("  Status:")
		print ("    Channel:       " + deviceStatus["channel"])
		print ("    Condition:     " + deviceStatus["condition"])
		print ("    Temperature:   " + str(deviceStatus["temperature"]))
		print ("    Units:         " + deviceStatus["units"])
		print ()

		deviceLocation = deviceStatus["location"]

		print ("   Location:")
		print ("     Description:  " + deviceLocation["description"])
		print ("     Lattitude:    " + self.annotationZilch(deviceLocation["lattitude"]))
		print ("     Longitude:    " + self.annotationZilch(deviceLocation["longitude"]))
		
		print ()

		return status

	'''
		Find a device in the devices list.

		Returns: the index into the device list, and the device record
	'''
	def findDevice (self, deviceFQN):
		deviceIndex = None
		device = None
		
		dcsIndex = 0
		deviceLen = len(self.myDevices)

		while (deviceIndex == None) and (dcsIndex < deviceLen):
			device = self.myDevices[dcsIndex]

			if (device["fqn"] == deviceFQN):
				deviceIndex = dcsIndex
				self.setDevice(device)

			index += 1

		# These MUST both be None together
		if (deviceIndex == None):
			device = None

		return ( deviceIndex, device )

	'''
		Initalize the device system data to a known state
	'''
	def initializeDevice (self):
		status = True

		self.deviceName = None
		self.deviceNetwork = None
		self.deviceFQN = None

		self.deviceGotAuthenticated = False
		self.deviceGotAuthorize = False
		self.deviceGotAnnounce = False
		self.deviceGotSecurity = False

		self.deviceChannel = None
		self.deviceResources = None
		self.deviceDataCheck = None
		self.deviceUnits = None
		self.deviceLocation = None
		self.devicePublicKey = None
		self.devicePassword = None
		self.deviceCommandOK = False				# True if the "command" message is OK
		self.deviceControlOK = False				# True if the "control" message is OK
		self.deviceSecurityPassword = None

		self.deviceAuthorizationValid = False

		self.deviceAuthorization = {
			"valid" : self.deviceAuthorizationValid,
			"security" : self.deviceSecurityType,
			"password" : self.deviceSecurityPassword,
			"pubkey" : self.devicePublicKey 
		}

		self.deviceWeSentAuthorize = False
		self.deviceWeSentSecurity = False

		return status

	'''
		Remove a device from the devices[] list.
	'''
	def removeDevice (self, deviceFQN):
		status = True

		deviceIndex, device = self.findDevice(deviceFQN)

		if (deviceIndex == None):
			self.displayError("removeDevice", 9999, "Device " + deviceFQN + " was not found!")
			status = False
		else:
			self.myDevices.remove(device)
			self.myDevicesCount -= 1

		return status

	'''
		Set the global (class) variables for a device, so we can update the information
	'''
	def setDevice (self, device):
		status = True

		self.initializeDevice()		

		self.deviceName = device["name"]
		self.deviceNetwork = device["network"]
		self.deviceFQN = device["fqn"]

		self.deviceGotAuthenticated = device["authenticated"]
		self.deviceGotAuthorize = device["authorized"]
		self.deviceGotAnnounce = device["announced"]
		self.deviceGotSecurity = device["security"]

		self.deviceChannel = device["channel"]
		self.deviceCondition = device["condition"]
		self.deviceResources = device["resources"]
		self.deviceDataCheck = device["datacheck"]
		self.deviceUnits = device["units"]
		self.deviceLocation = device["location"]
		self.devicePublicKey = device["publickey"]
		self.devicePassword = device["password"]
		self.devicePermissions = device["permissions"]

		self.deviceAuthorization = device["authorization"]
		self.deviceAuthorizationValid = self.deviceAuthorization["valid"]

		self.deviceWeSentAuthorize = device["wesentauthorize"]
		self.deviceWeSentSecurity = device["wesentsecurity"]

		return status

	'''
		Update information for a devicely device

		Returns: the index into the devices list, and the device record
	'''
	def updateDevice (self, deviceIndex=None):
		device = {
			"name" : self.deviceName,
			"network" : self.deviceNetwork,
			"fqn" : self.deviceFQN,

			"authenticated" : self.deviceGotAuthenticated,
			"authorized" : self.deviceGotAuthorize,
			"announced" : self.deviceGotAnnounce,
			"security" : self.deviceGotSecurity,

			"securitytype" : self.deviceSecurityType,
			"channel" : self.deviceChannel,
			"condition" : self.deviceCondition,
			"resources" : self.deviceResources,
			"datacheck" : self.deviceDataCheck,
			"location" : self.deviceLocation,
			"publickey" : self.devicePublicKey,
			"password" : self.devicePassword,
			"units" : self.deviceUnits,
			"permissions" : self.myPermissions,

			"wesentauthorize" : self.deviceWeSentAuthorize,
			"wesentsecurity" : self.deviceWeSentSecurity,

			"authorization" : self.deviceAuthorization
		}

		# Update device list entry?
		if (deviceIndex != None):
			self.myDevices[deviceIndex] = device

		return ( deviceIndex, device )

	'''
		Validate the devices list and make sure we have all of the
			authorization information we need.
	'''
	def validateDevices (self):
		status = True
		msgid = None

		nrDevices = len(self.myDevices)

		if (nrDevices > 0):
			print ()
			print ("Validating authentication for known devices..")

			for device in self.myDevices:
				fqn = device["fqn"]

				print ("  Checking device " + fqn)

				deviceIndex, device = self.checkDevice(fqn)

				# Check to be sure we have sent all the necessary info to this device
				if (not self.deviceGotAuthenticated):
					self.deviceGotAuthenticated = (self.deviceGotAuthorize and self.deviceGotSecurity and self.deviceWeSentAuthorize and self.deviceWeSentSecurity)

					if (not self.deviceGotAuthenticated):
						status, msgid = self.checkAuthentication(fqn)

						if (not status) and (msgid == None):
							self.displayError("validateDevices", 9999, "There was a problem authenticating " + fqn)

				self.updateDevice(deviceIndex)

		return ( status, msgid )

	'''
		End of device list routines
	'''

	'''
		List all messages that have currently been read in a single line
			list with just the most important information.
	'''
	def listMessages (self):
		status = True

		dcsIndex = 0
		nrListed = 0

		# Messages are already stored in ascending order
		while (dcsIndex < self.dcsMessageCount):
			dcsMsg = self.dcsMessageList[dcsIndex]

			dcsUser = dcsMsg["username"]
			dcsDateUTC = dcsMsg["cdate"]

			timedate = local_datetime(dcsDateUTC)
			time = timedate[1]

			print ("Message " + dcsMsg["id"] + ", created on " + timedate[0] + " at " + time.lower() + " " + timedate[2] + ": " + dcsMsg["text"])

			nrListed += 1

		if (nrListed > 0):
			print ()
			print ("Total messages listed: " + str(nrListed))
			print ()

		return status

	def matchMessage (self, fqn, dcsMsg):
		dto = dcsMsg["dto"]

		status = (isBroadcastMessage(dcsMsg) or (dto == fqn))

		return status

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

	# Annotation type: net.hybotics.dcs.address
	def processAddress (self, aNote, fromFQN):
		status = True
		msgid = None
		theirPassword = None

		aValue = aNote["value"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (self.debuggingAddress):
#			print ("(processAddress) aNote:")
#			self.pp.pprint(aNote)
			print ("(processAddress) deviceIndex:")
			self.pp.pprint(deviceIndex)
			print ("(processAddress) device:")
			self.pp.pprint(device)

		if (deviceIndex == None) and (device == None):
			self.displayError("processAddress", 9999, fromFQN + " was not found in my devices list")
		else:
			self.deviceFQN = fromFQN

			# Check the authentication of this device
			status, msgid = self.checkAuthentication(self.deviceFQN)

			if ((not status) and (msgid == None)):
				self.displayError("processAddress", 9999, "There was a problem checking authentication for " + fromFQN)

			# Start out assuming this message won't be authenticated
			self.connectionAuthorized = False

			# If this device is authenticated, check their authorization information
			if self.deviceGotAuthenticated:
				# Get the device's authorization information
				deviceAuthInfo = device["authorization"]

				# Is their authorization information valid?
				if (deviceAuthInfo["valid"]):
					# Yes, so get their authorization password
					theirAuthPassword = deviceAuthInfo["password"]

					# These MUST MATCH!
					if (theirAuthPassword == self.myPassword):
						# This message is authentic, so connection is authorized
						self.connectionAuthorized = True

				if (self.debuggingAddress):
					print ("(processAddress) Connection with " + fromFQN + " (" + self.annotationTrueFalse(self.deviceGotAuthenticated, "authenticated", "not authenticated") + ") is " + self.annotationTrueFalse(self.connectionAuthorized, "authorized", "not authorized") + "!")

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.announce
	def processAnnounce (self, aNote, fromFQN):
		status = True
		msgid = None

		deviceIndex, device = self.checkDevice(fromFQN)

		if (self.debuggingAnnounce):
			print ("(processAnnounce) fromFQN = " + fromFQN)
			print ("Device:")
			self.pp.pprint(device)
			print ("Annotation:")
			self.pp.pprint(aNote)

		if (deviceIndex == None) and (device == None):
			self.displayError("processAnnounce", 9999, fromFQN + " was not found in my devices list")
		else:
			aValue = aNote["value"]

			deviceStatus = aValue["status"]

			# Always update a current device
			self.deviceResources = aValue["resources"]
			self.deviceCondition = deviceStatus["condition"]
			self.deviceUnits = deviceStatus["units"]
			self.deviceLocation = deviceStatus["location"]
			self.deviceChannel = deviceStatus["channel"]
			self.deviceGotAnnounce = True

			# Update this device
			self.updateDevice(deviceIndex)

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.authorize
	def processAuthorize (self, aNote):
		status = True
		msgid = None

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (self.debuggingAuthorize):
			print ("(processAuthorize) fromFQN = " + fromFQN)
			print ("Device:")
			self.pp.pprint(device)
			print ("Annotation:")
			self.pp.pprint(aNote)

		if (deviceIndex == None) and (device == None):
			self.displayError("processAuthorize", 9999, fromFQN + " was not found in my devices list")
		else:
			perms = aValue["perms"]

			self.deviceDataCheck = aValue["datacheck"]
			self.deviceCommandOK = perms["command"]
			self.deviceControlOK = perms["control"]
			self.deviceGotAuthorize = True

			# Check the authentication for this device
			self.checkAuthentication(fromFQN)

			# Update this device
			self.updateDevice(deviceIndex)

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.command
	def processCommand (self, aNote, msgid):
		status = True
		msgid = None

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (self.debuggingCommand):
			print ("(processCommand) device is " + fromFQN + ", and connection is " + self.annotationTrueFalse(self.connectionAuthorized, "authorized", "not authorized"))
			print ("(processCommand) deviceIndex:")
			self.pp.pprint(deviceIndex)
			print ("(processCommand) device:")
			self.pp.pprint(device)
			print ("(processCommand) aNote:")
			self.pp.pprint(aNote)

		if (deviceIndex == None) and (device == None):
			self.displayError("processCommand", 9999, fromFQN + " was not found in my devices list")
		elif (self.deviceGotAuthenticated and self.connectionAuthorized):
			cmd = aValue["command"]

			if (cmd == "shutdown"):
				# Only accepted from a network Controller if they have the
				#	command permission.
				if (self.deviceCommandOK) and ("controller" in self.deviceResources):
					if ("now" in aValue["params"]):
						# Shutdown this device
						self.running = False
			else:
				self.displayError("processCommand", 9999, "Unknown Command: " + cmd)

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.control
	def processControl (self, aNote, msgid):
		status = True

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (deviceIndex == None) and (device == None):
			self.displayError("processControl", 9999, fromFQN + " was not found in my devices list")
		else:
			if (self.deviceGotAuthenticated and self.connectionAuthorized):
				# Process message
				status = True

		return ( status, None )

	# Annotation type: net.hybotics.dcs.error
	def processError (self, aNote, msgid, toFQN):
		status = True
		msgid = None

		aValue = aNote["value"]
		aType = self.annotationType(aNote)
		fromFQN = aValue["fqn"]

		errorCode = aValue["error"]

		print ("*** Processing error " + str(errorCode) + " from " + fromFQN + "..")

		if (errorCode == 1001):
			errorMessage = "Authentication with " + fromFQN + " failed"

			# Resend our authorization information
#			status, msgid = self.sendSecurity(fromFQN)
		elif (errorCode == 1002):
			errorMssage = "There was a problem sending an acknowledgement to " + fromFQN

			if (aType == "response"):
				# Try to resend the acknowledgement
				status = True
#				status, msgid = self.sendAcknowledgement(fromFQN, aValue["resptype"], aValue["number"])
		elif (errorCode == 1003):
			errorMessage = "Device " + fromFQN + " is not authorized to make requests from " + self.myFQN

			# Send our authorization information, and try becoming devices
#			status, msgid = self.sendAuthorize(fromFQN)
		elif (errorCode == 1004):
			errorMessage = "The password for " + fromFQN + " does not match my password"

			# Resend our authorization and security information
#			status, msgid = self.sendSecurity(fromFQN)
		elif (errorCode == 1005):
			errorMessage = "We got an authorize record, but no security information from " + toFQN

#			self.sendSecurity(fromFQN)
		elif (errorCode == 1006):
			errorMessage = fromFQN + " is not on my network (" + self.myNetwork + ")"

		# Display the error information locally
		self.displayError("processError", errorCode, "Error " + str(errorCode) + ": '" + errorMessage + "' reported by " + fromFQN + " regarding message " + msgid)
		print ()
		print ("The status of " + fromFQN + " is:")
		self.displayDeviceStatus(aValue["status"])

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.private
	def processPrivate (self, aNote, msgid):
		status = True
		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (deviceIndex == None) and (device == None):
			self.displayError("processControl", 9999, fromFQN + " was not found in my devices list")
		else:
			if (self.deviceGotAuthenticated and self.connectionAuthorized):
				# Process message
				status = True
			else:
#				self.sendError("processPrivate", fromFQN, 1003)
				status = False

			return ( status, None )

	# Annotation type: net.hybotics.dcs.request
	def processRequest (self, aNote, msgid):
		status = True
		msgid = None

		aValue = aNote["value"]
		req = aValue["request"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (deviceIndex == None) and (device == None):
			self.displayError("processControl", 9999, fromFQN + " was not found in my devices list")
		elif (self.deviceGotAuthenticated and self.connectionAuthorized):
			# Process message
			status = True

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.response
	def processResponse (self, aNote, msgid, fromFQN):
		status = True
		msgid = None

		aValue = aNote["value"]

		deviceIndex, device = self.checkDevice(theirFQN)

		if (deviceIndex == None) and (device == None):
			self.displayError("processResponse", 9999, fromFQN + " was not found in my devices list")
		else:
			if (self.deviceGotAuthenticated and self.connectionAuthorized):
				self.deviceFQN = fromFQN

				theirFQN = fromFQN
				theirResponseType = aValue["resptype"]
				theirResponseNumber = aValue["number"]
				theirResponseTo = aValue["respto"]
				theirStatus = aValue["status"]
				theirResponseDataPackage = aValue["data"]

				# Make the appropriate response to a message
				if (theirResponseType == "announce"):
					status = True
				elif (theirResponseType == "authorize"):
					status = True
				elif (theirResponseType == "command"):
					status = True
				elif (theirResponseType == "control"):
					status = True
				elif (theirResponseType == "error"):
					status = True
				elif (theirResponseType == "private"):
					status = True
				elif (theirResponseType == "request"):
					status = True
				elif (theirResponseType == "security"):
					status = True

			# Always update a device's status
			deviceStatus = aValue["status"]

			self.deviceChannel = deviceStatus["channel"]
			self.deviceCondition = deviceStatus["condition"]
			self.deviceLocation = deviceStatus["location"]
			self.deviceUnits = deviceStatus["units"]

			self.updateDevice(deviceIndex)

		return ( status, msgid )

	# Annotation type: net.hybotics.dcs.security
	def processSecurity (self, aNote, msgid):
		if (self.debuggingSecurity):
			print ("Showing aNote:")
			pp.pprint(aNote)

		status = True
		msgid = None

		aValue = aNote["value"]
		fromFQN = aValue["fqn"]

		deviceIndex, device = self.checkDevice(fromFQN)

		if (self.debuggingSecurity):
			print ("(processSecurity) fromFQN = " + fromFQN)
			print ("Device:")
			self.pp.pprint(device)
			print ("Annotation:")
			self.pp.pprint(aNote)

		if (deviceIndex == None) and (device == None):
			self.displayError("processSecurity", 9999, fromFQN + " was not found in my devices list")
		else:
			self.deviceSecurityType = aValue["type"]
			self.devicePassword = aValue["password"]
			self.devicePublicKey = aValue["pubkey"]
			self.deviceGotSecurity = True

			# Update this device
			self.updateDevice(deviceIndex)

		return ( status, msgid )
		
	'''
		This is the main driver for message processing. It needs to call one
			routine for each message type you have. It will be called to
			process each message read from the active channel.

		The message to be processed is a standard App.Net channel message,
			with annotations. This routine processes a single message.
	'''
	def process (self, dcsMsg, execute=None):
		status = True
		sentMsgID = None

		msgid = dcsMsg["id"]
		msgDateUTC = dcsMsg["cdate"]

		timedate = local_datetime(msgDateUTC)
		time = timedate[1].lower()

		'''
			Annotations are a list (array) within the message. Every DCS message will
				have at least two annotations - an "address" type plus one, or more, others.
		'''
		annotations = dcsMsg["annotations"]
		alen = len(annotations)

		# This will ALWAYS be an "address" annotation
		addr = annotations[0]
		addrV = addr["value"]

		fromFQN = addrV["dfrom"]
		toFQN = addrV["dto"]

		if (self.debuggingProcess):
			if execute:
				print ("Called from executePendingTask()")

		print ("Processing message " + dcsMsg["id"] + " (" + self.annotationTrueFalse(self.isPrivateMessage(dcsMsg), "Private", "Public") + ") from " + fromFQN + ", created on " + timedate[0] + " at " + time + " " + timedate[2])

		# Process each annotation in the current message.
		for index in range(alen):
			aNote = annotations[index]
			aType = self.annotationType(aNote)
			aValue = aNote["value"]

			'''
				Make sure this message is really addressed to us or to
					"all" (a broadcast message), or it's an "announce"
					annotation (in a *public* message only).

					I do not want to process my own messages!
			'''
			if (fromFQN != self.myFQN) and ((toFQN == self.myFQN) or (toFQN == "all") or ((aType == "announce") and (not self.isPrivateMessagePrivate(msg)))):
				'''
					Now we have the information needed to select a message processor, and the
						data to pass to it.
				'''
				if (aType == "address"):
					print ("    Address annotation")
					status, sentMsgID = self.processAddress(aNote, fromFQN)
				elif (aType == "announce"):
					print ("    Announce annotation")
					status, sentMsgID = self.processAnnounce(aNote, fromFQN)
				elif (aType == "authorize"):
					print ("    Authorize annotation")
					status, sentMsgID = self.processAuthorize(aNote)
				elif (aType == "command"):
					print ("    Command annotation")
					status, sentMsgID = self.processCommand(aNote, msgid)
				elif (aType == "control"):
					print ("    Control annotation")
					status, sentMsgID = self.processControl(aNote, msgid)
				elif (aType == "error"):
					print ("    Error annotation")
					status, sentMsgID = self.processError(aNote, msgid, toFQN)
				elif (aType == "private"):
					print ("    Private Message annotation")
					status, sentMsgID = self.processPrivate(aNote, msgid)
				elif (aType == "request"):
					print ("    Request annotation")
					status, sentMsgID = self.processRequest(aNote, msgid)
				elif (aType == "response"):
					print ("    Response annotation")
					status, sentMsgID = self.processResponse(aNote, msgid, fromFQN)
				elif (aType == "security"):
					print ("    Security annotation")
					status, sentMsgID = self.processSecurity(aNote, msgid)
				else:
					print ("    Invalid annotation type (" + aType + ") in message " + msgid)

				if (not execute) and (aType in [ "authorize", "command", "control", "error", "request", "security" ]):
					# Add this task to the pending tasks list
					self.addPendingTask(aType, msgid, fromFQN, aNote)

		return ( status, sentMsgID )

	'''
		Send a message to a device. It is expected that the device will have set any
			class (global) variables before trying to send a message.

			You can now pass in previously prepared data that will just be
				written out in a message.

				aNoteInfo is the annotation to write out
				deviceAuthInfo is the device's authorization information

				These must either BOTH be present or BOTH not present (set to None)
	'''
	def send (self, toFQN, msgTypes, aNoteInfo=None, deviceAuthInfo=None):
		status = True
		msgid = None

		textMessageType = ""
		annotations = []

		# Is this a broadcast message?
		broadcastMessage = (toFQN == "all")

		self.yourFQN = toFQN

		if (self.debuggingSend):
			print ("(send) toFQN = " + toFQN)
			print ("(send) This is a " + self.annotationTrueFalse(broadcastMessage, "broadcast", "normal") + " message")

		deviceIndex, device = self.checkDevice(toFQN)

		if (self.debuggingSend):
			print ("(send) deviceIndex:")
			self.pp.pprint(deviceIndex)
			print ("(send) device:")
			self.pp.pprint(device)

		if (status and broadcastMessage):
			print ()
			print ("Sending a broadcast message..")
			print ()

			if (self.debuggingSend):
				pp = pprint.PrettyPrinter(indent=4)
				print ("(send) deviceIndex:")
				pp.pprint(deviceIndex)
				print ("(send) device:")
				pp.pprint(device)

		if (aNoteInfo != None) and (deviceAuthInfo != None):
			# We have previously prepared authorization information for this device
			self.myAuthorization = deviceAuthInfo
		else:
			# Send current device's authorization information
			self.myAuthorization = self.deviceAuthorization

			if (self.debuggingSend):
				print ("(send, after auth) deviceIndex:")
				self.pp.pprint(deviceIndex)
				print ("(send, after auth) device:")
				self.pp.pprint(device)
				print ("(send, after auth) deviceAuthorization:")
				self.pp.pprint(self.deviceAuthorization)

		# All annotations are serialized - increment the appropriate serial number(s)
		if ("announce" in msgTypes):
			self.myAnnounceNumber += 1

		if ("authorize" in msgTypes):
			self.myAuthorizeNumber += 1

		if ("command" in msgTypes):
			self.myCommandNumber += 1

		if ("control" in msgTypes):
			self.myControlNumber += 1

		if ("error" in msgTypes):
			self.myErrorNumber += 1

		if ("private" in msgTypes):
			self.myPrivateNumber += 1

		if ("request" in msgTypes):
			self.myRequestNumber += 1

		if ("response" in msgTypes):
			self.myResponseNumber += 1

		if ("security" in msgTypes):
			self.mySecurityNumber += 1
			self.mySecurityPassword = self.myPassword

		# These annotations are *always* sent in a private message
		if ("authorize" in msgTypes) or ("private" in msgTypes) or ("security" in msgTypes):
			self.myPrivacy = True

		# Make sure everything is updated before we write the message
		self.update()

		if (not broadcastMessage):
			self.updateDevice(deviceIndex)

		# The "address" annotations is ALWAYS the FIRST annotation of a message
		annotations.append(self.dcsAddress)

		if (aNoteInfo == None) and (deviceAuthInfo == None):
			for mType in msgTypes:
				# Add the right annotation into the message
				if (mType == "announce"):
					# Type: net.hybotics.dcs.announce - announce presense and resources
					textMessageType = textMessageType + " Announce"
					anote = self.dcsAnnounce	
				elif (mType == "authorize"):
					# Type: net.hybotics.dcs.authorize - identification and key exchange
					textMessageType = textMessageType + " Authorize"
					anote = self.dcsAuthorize
				elif (mType == "command"):
					# Type: net.hybotics.dcs.command - commanding a device to do something
					textMessageType = textMessageType + " Command"
					anote = self.dcsCommand
				elif (mType == "control"):
					# Type net.hybotics.dcs.control - Control command for a device to change its state and/or status
					textMessageType = textMessageType + " Control"
					anote = self.dcsControl
				elif (mType == "error"):
					# Type net.hybotics.dcs.error - Send an error code
					textMessageType = textMessageType + " Error"
					anote = self.dcsError
				elif (mType == "private"):
					# Private Message
					textMessageType = textMessageType + " Private Message"
					anote = self.dcsPrivateMessage
				elif (mType == "request"):
					# Type: net.hybotics.dcs.request - requesting something from a device
					textMessageType = textMessageType + " Request"
					anote = self.dcsRequest
				elif (mType == "response"):
					# Type: net.hybotics.dcs.responce - responding to a request or command from another device
					textMessageType = textMessageType + " Response"
					anote = self.dcsResponse
				elif (mType == "security"):
					# Type: net.hybotics.dcs.security - exchange security information
					textMessageType = textMessageType + " Security"
					anote = self.dcsSecurity
				else:
					# Whoops! We didn't get a proper annotation type!
					self.displayError("send", 9999, "Invalid annotation type: " + mType)

				# Append the annotation to the annotations for this message
				annotations.append(anote)
		else:
			anote = aNoteInfo
			aType = self.annotationType(aNoteInfo)
			textMessageType = textMessageType + " " + aType
			status = True

		if (not broadcastMessage):
			self.updateDevice(deviceIndex)

		if (status):
			self.operationResultText = ""

			# Setup the logging text for this message
			text = self.myFQN + " --> " + self.yourFQN + " for:" + textMessageType

			# Write the messaage to the channel
			msgid = self.channel.write(text, annotations)

			if (msgid == None):
				# Error - we did not successfully write a message to the channel
				self.displayError("send", 9999, "There was a problem creating a new message")
				status = False
			else:
				# Add the "command", "control", "request" annotations
				#	to our Pending Actions list
				if (mType in [ "command", "control", "request" ]):
					self.addPendingAction(mType, msgid, toFQN, anote)

		# Make sure no sensitive data items (like passwords) hang around
		self.myPrivacy = False
		self.mySecurityPassword = None
		self.update()

		# Delay a bit for the API
		sleep(self.delaySecondsAPI)

		return ( status, msgid )

	'''
		Send a simple acknowledgement to a received message.
	'''
	def sendAcknowledgement (self, toFQN, responseType, responseNumber):
		status = True
		msgid = None

		self.myResponseDataType = "boolean"
		self.myResponseData = { "value" : True }
		self.myResponseDataPackage = None
		self.myResponseCheckType = self.myDataCheckType
		self.myResponseTo = responseNumber
		self.myResponseType = responseType

		# This is just an acknowledgement. No response required!
		self.myResponseFinal = True

		self.update()

		status, msgid = self.send(toFQN, [ "response" ])

		if (msgid == None):
			self.displayError("sendAcknowledgement", 9999, "Unable to send acknowledgement to " + toFQN)

		return ( status, msgid )

	'''
		Send and authorization request
	'''
	def sendAuthorize(self, toFQN):
		status = True
		msgid = None

		deviceIndex, device = self.checkDevice(toFQN)
		self.setDevice(device)

		status, msgid = self.send(toFQN, [ "announce", "authorize" ])

		if (msgid == None):
			self.displayError("sendAuthorize", 9999, "There was a problem sending an authorization to " + toFQN)
			status = False
		else:
			self.deviceWeSentAuthorize = True
			self.updateDevice(deviceIndex)

		return ( status, msgid )

	'''
		Send an error to a device
	'''
	def sendError (self, routine, toFQN, errorCode, meta=None):
		status = True
		msgid = None

		self.myErrorCode = errorCode
		self.update()

		if (errorCode != 9999):
			if (errorCode == 1001):
				errorMessage = "Authentication with " + toFQN + " failed"
			elif (errorCode == 1002):
				errorMessage = "There was a problem sending an acknowledgement to " + toFQN
			elif (errorCode == 1003):
				errorMessage = "Device " + toFQN + " is not authorized to contact " + self.myFQN
			elif (errorCode == 1004):
				errorMessage = "The password for " + toFQN + " does not match my password"
			elif (errorCode == 1005):
				errorMessage = "We got an authorization record, but no security information"
			elif (errorCode == 1006):
				errorMessage = "You are not in my network (" + self.myNetwork + ")"

			self.displayError(routine, errorCode, errorMessage, meta)

		status, msgid = self.send(toFQN, [ "error" ])

		if (msgid == None):
			actionMessage = "Unable to send error '" + str(errorCode) + ": " + errorMessage + "' to " + toFQN
			displayError("sendError", 9999, actionMessage, meta)
			status = False

		return ( status, msgid )

	'''
		Send security information to a device
	'''
	def sendSecurity (self, toFQN):
		status = True
		msgid = None

		deviceIndex, device = self.checkDevice(toFQN)

		# Send our security information
		status, msgid = self.send(toFQN, [ "security" ])

		if (msgid == None):
			self.displayError("sendSecurity", 9999, "There was a problem sending authorization/security information to " + toFQN)
			status = False
		else:
			self.deviceWeSentSecurity = True
			self.updateDevice(deviceIndex)

		return ( status, msgid )

	'''
		Show the main attributes of a device.
	'''
	def show (self):
		print ("My name is:          '" + self.myName + "'")
		print ("My network is:       '" + self.myNetwork + "'")
		print ("My FQN is:           '" + self.myFQN + "'")
		print ("My account is:       '" + self.myAccount + "'")
		print ()
		print ("My channel is:        " + self.channel.chanID)
		print ()

		print ("My resources are:     " + self.annotationResources(self.myResources))

		print ()
		print ("My data check:       '" + self.myDataCheckType + "'")
		print ()
		print ("My security is:      '" + self.mySecurityType + "'")
		print ("   My password is    '" + self.annotationZilch(self.myPassword) + "'")
		print ("   My public key is: '" + self.annotationZilch(self.myPublicKey) + "'")
		print ()

		return None

	'''
		Display a detailed error message
	'''
	def displayError (self, dcsRoutine, dcsErrorCode, dcsErrorMessage, meta=None):
		print ("DCS Error in the '" + dcsRoutine + "' routine - " + str(dcsErrorCode) + ": " + dcsErrorMessage + "!")

		if (meta != None):
			self.operationErrorCode = meta["code"]
			self.operationErrorMessage = meta["error_message"]
#			self.operationErrorSlug = meta["error_slug"]
			self.operationErrorID = meta["error_id"]

			print ()
			print ("Additional API related information:")
			print ()
			print ("API Error:   " + str(self.operationErrorCode))
			print ("API Message: " + self.operationErrorMessage)
#			print ("API Slug:  " + self.operationErrorSlug) 
			print ("API ID:      " + self.operationErrorID)

		if (self.operationResultText != ""):
			print ()
			print ("Raw JSON:")

			self.pp.pprint(self.operationResultText)

		return True

	'''
		This is the device run loop, where the device will spend all of its time.
	'''
	def run (self):
		# Initialize
		status = True
		msgid = None
		readMessages = False

		self.startup()

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

				self.displayDeviceList()

			if (self.running):
				# Check pending actions
				status, msgid = self.checkPendingActions()

				# Check pending tasks
				status, msgid = self.checkPendingTasks()

				self.displayDeviceList()
				
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

				# Delay a little bit to allow for new messages to come in.
				sleep(self.delayRunLoop)
			else:
				print ("I have received the shutdown command - shutting down..")
				status = self.shutdown()

		return status

	'''
		Routine to properly shut down and save data
	'''
	def shutdown (self):
		status = True

		print ("Device " + self.myFQN + "is shutting down now..")

		return status

	def startup (self):
		status = True

		print ("Device " + self.myFQN + "is starting up..")

		# Read messages from the channel
		self.extractMessageData()

		if (self.debugging):
			self.parseReadResult(1)
		
		print ()
		print ("Entering run mode..")
		print ()

		return status

	'''
		Update data used in messages.
	'''
	def update (self):
		'''
			Other data used in messages
		'''
		# My special permissions
		self.myPermissions = {
			"command" : self.myCommandOK,
			"control" : self.myControlOK
		}

		# My data package for a response
		self.myResponseDataPackage = {
			"type" : self.myResponseDataType,
			"datacheck" : self.myResponseCheckType,
			"data" : self.myResponseData
		}

		# My current location
		self.myLocation = {
			"description" : self.myLocationDescription,
			"lattitude" : self.myLattitude,
			"longitude" : self.myLongitude
		}

		# My current status
		self.myStatus = {
			"channel" : self.myChannel,
			"condition" : self.myCondition,
			"location" : self.myLocation,
			"temperature" : self.myTemperature,
			"units" : self.myUnits
		}

		'''
			Message annotations and types
		'''
		# Type: net.hybotics.dcs.address - address a message to a device
		self.dcsAddress = {
			"type" : "net.hybotics.dcs.address",

			"value"	: {
				"dfrom" : self.myFQN,
				"dto": self.yourFQN,
				"private" : self.myPrivacy,
				"authorization" : self.myAuthorization
			}
		}

		# Type: net.hybotics.dcs.announce - announce presence and resources
		self.dcsAnnounce = {
			"type" : "net.hybotics.dcs.announce",

			"value"	: {
				"number" : self.myAnnounceNumber,
				"fqn" : self.myFQN,
				"resources" : self.myResources,
				"status" : self.myStatus
			}
		}

		# Type: net.hybotics.dcs.authorize - identification and security information exchange
		self.dcsAuthorize = {
			"type" : "net.hybotics.dcs.authorize",

			"value" : {
				"number" : self.myAuthorizeNumber,
				"fqn" : self.myFQN,
				"perms" : self.myPermissions,
				"network" : self.myNetwork,
				"datacheck" : self.myDataCheckType
			}
		}

		# Type: net.hybotics.dcs.command - (low level) commanding a device to do something
		self.dcsCommand = {
			"type" : "net.hybotics.dcs.command",

			"value"	: {
				"number" : self.myCommandNumber,
				"fqn" : self.myFQN,
				"command" : self.myCommand,
				"params" : self.myCommandParams
			}
		}

		# Type net.hybotics.dcs.control - (low level) command for a device to change its state and/or status
		self.dcsControl = {
			"type" : "net.hybotics.dcs.control",

			"value" : {
				"number" : self.myControlNumber,
				"fqn" : self.myFQN,
				"control" : self.myControl,
				"params" : self.myControlParams,
				"data" : self.myControlData,
			}	
		}

		# Type net.hybotics.dcs.error - Send an error condition
		self.dcsError = {
			"type" : "net.hybotics.dcs.error",

			"value" : {
				"number" : self.myErrorNumber,
				"fqn" : self.myFQN,
				"error" : self.myErrorCode,
				"status" : self.myStatus
			}
		}

		# Type net.hybotics.dcs.private - Private Message
		self.dcsPrivateMessage = {
			"type" : "net.hybotics.dcs.private",

			"value" : {
				"number" : self.myPrivateNumber,
				"fqn" : self.myFQN,
				"type" : self.myPackageType,
				"package" : self.myPackage,
				"status" : self.myStatus
			}
		}

		# Type: net.hybotics.dcs.request - requesting something or an action from a device
		self.dcsRequest = {
			"type" : "net.hybotics.dcs.request",

			"value" : {
				"number" : self.myRequestNumber,
				"fqn" : self.myFQN,
				"request" : self.myRequest,
				"params" : self.myRequestParams,
				"data" : self.myRequestData
			}
		}

		# Type: net.hybotics.dcs.response - responding to a request, command, or
		#	control message from another device
		self.dcsResponse = {
			"type" : "net.hybotics.dcs.response",

			"value" : {
				"number" : self.myResponseNumber,
				"respto" : self.myResponseTo,
				"resptype" : self.myResponseType,
				"status" : self.myStatus,
				"data" : self.myResponseDataPackage,
				"ack" : self.myResponseFinal
			}
		}

		# Type net.hybotics.dcs.security - exchange security information
		self.dcsSecurity = {
			"type" : "net.hybotics.dcs.security",

			"value" : {
				"number" : self.mySecurityNumber,
				"fqn" : self.myFQN,
				"type" : self.mySecurityType,
				"password" : self.mySecurityPassword,
				"pubkey" : self.myPublicKey
			}
		}

		return None

	def updateAuthorization (self):
		authInfo = {
			"valid" : self.myAuthorizationValid,
			"security" : self.mySecurityType,
			"password" : self.mySecurityPassword,
			"pubkey" : self.myPublicKey 
		}

		return authInfo

# This makes DCS_Device runnable as a script
if __name__ == "__main__":
	status = True

	print ("This is DCS_Device() running as a script!")