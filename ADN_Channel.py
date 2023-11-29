'''
	Program:	ADN_Channel.py, Encapsulates the App.net Channel and Message APIs.

				Copyright (C) 2013 Dale Weber. ALL Rights Reserved. License to be chosen.

	Author:		Dale Weber <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>

	Version:	0.2.4 (Unstable)
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
#from pytz import utc, timezone

'''
	App.Net Channels and Messages
'''
class ADN_Channel():
	'''
		These are error variable results used in various routines
	'''
	operationErrorCode = None
	operationErrorMessage = None
	operationErrorSlug = None
	operationErrorID = None
	operationResultText = None

	# We have to do special stuff on the first read from the channel
	firstRead = True

	# The logged in account
	account = ""

	# The channel owner
	owner = ""

	# The access token for API operations
	token = ""

	# The access token string added to the URL for all API operations
	accessToken = ""

	# Headers for API post operations
	postHeaders = { "Content-Type" : "application/json" }

	# The ID of the last message read from the channel by the channel read() routine.
	lastMessageRead = "0"

	lastMessageDisplayed = 0
	lastMessageListed = 0

	# Delay between API operations
	delaySecondsAPI = 3

	'''
		I think these three variables are the only channel variables that have to be
			unique to each device. I'd like to find a way these can be moved into
			the ADN_Device class so each device can use the same channel instance.
	'''
	# The last message "read" from the messages[] list.
	lastMessageGet = -1

	'''
		Error code and full JSON from result.text of an API operation that generated an
			error. These variables contain all the information App.Net returns in the
			case of an error.
	'''
	operationErrorCode = 0
	operationErrorMessage = ""
	operationErrorSlug = ""
	operationErrorID = ""

	# In addition, this is the raw JSON returned in the case of an App.Net error
	operationResultText = ""

	'''
		This contains the all messages read from the channel, and the number of messageSendSleep
			read to date.
	'''
	messages = []
	messagesCount = 0

	'''
		Start of Debug variables
	'''
	readURL = ""
	readResultText = ""
	
	writeURL = ""
	writeResultText = ""
	'''
		End of Debug variables
	'''

	'''
		Constructor
	'''
	def __init__ (self, adnauth, chanReaders=None, chanWriters=None, chanType=None):
		# Channel data we save
		self.account = adnauth.username
		self.token = adnauth.token

		# Used in url creation
		self.accessToken =  "?access_token=" + self.token

		if (chanReaders != None) and (chanWriters != None) and (chanType != None):
			# Creating a new channel
			channel = {
				"readers" : chanReaders,
				"writers" : chanWriters,
				"type" : chanType
			}
 
			chanJSON = json.dumps(channel)

			self.create(chanJSON)
		
		return None

	'''
		Create a new channel - internal function, not meant to be called from the outside
	'''
	def create (self, channelJSON):
		url = "https://alpha-api.app.net/stream/0/channels" + self.accessToken

		result = requests.post(url , data=channelJSON, headers=self.postHeaders)
		responseJSON = json.loads(result.text)

		self.setup(responseJSON)

		return self.chanID

	'''
		Delete a message from the channel
	'''
	def delete (self, msgid):
		result = ""
		error = False
		status = True

		url = "https://alpha-api.app.net/stream/0/channels/" + self.chanID + "/messages/"

		foundMessage = self.find(msgid)

		if (foundMessage != None):
			# We have a message to work with.
			user = foundMessage["user"]
			creator = user["username"]

			# Make sure the channel owner is also the creator of this message
			if (creator == self.account):
				# Delete the message.
				url = url + msgid + self.accessToken + "&include_annotations=1"

				result = requests.delete(url)

				deleteJSON = json.loads(result.text)
				deleteMeta = deleteJSON["meta"]

				self.operationErrorCode = deleteMeta["code"]

				if (self.operationErrorCode == 200):
					# Remove the message from the channel messages list.
					self.messages.remove(foundMessage)
					self.messagesCount -= 1
				else:
					# Error - unable to delete message
					error = True
					self.operationResultText = "API Result is " + result.text
			else:
				print ("Unable to delete message #" + msgid + " (the creator is '" + creator + "', not '" + self.account + "'')")
		else:
			# Error - message does not exist
			print ("Message #" + msgid + " created by '" + self.account + "'' does not exist!")

		if (error):
			status = False

		# Delay a bit for the API
		sleep(self.delaySecondsAPI)

		return status

	'''
		Display a detailed error message
	'''
	def displayError (self, dcsRoutine, dcsErrorCode, dcsErrorMessage, meta=None):
		print ("DCS Error in the '" + dcsRoutine + "' routine - " + str(dcsErrorCode) + ": " + dcsErrorMessage + "!")

		if (meta == None):
			print ()
			print ("No additional API information about this error is available.")
			print ("  Please contact your support organization for additional assistance.")

			self.operationErrorCode = 0
			self.operationErrorMessage = ""
			self.operationErrorSlug = ""
			self.operationErrorID = ""
		else:
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
			print ("Raw JSON: " + self.operationResultText)

		return True

	'''
		Find a message by ID in the channel mesasge list.
	'''
	def find (self, msgid):
		foundMessage = None
		messageIndex = 0

		while (foundMessage == None) and (messageIndex < self.messagesCount):
			message = self.messages[messageIndex]

			if (message == None):
				self.displayError("findMessage", 9999, "Message " + msgid + " was not found")
				foundMessage = None
			elif (message["id"] == msgid):
				foundMessage = message

			messageIndex += 1

		return foundMessage

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
		List all messages that have currently been read in a single line list
	'''
	def list (self):
		index = 0
		nrListed = 0

		if (self.messagesCount > self.lastMessageListed) and (self.lastMessageListed > 0):
			self.lastMessageListed += 1

		# Messages are already stored in ascending order
		for index in range(self.lastMessageListed, self.messagesCount):
			msg = self.messages[index]

			msgOwner = msg["user"]
			msgCreator = msgOwner["username"]
			msgDateUTC = msg["created_at"]

			timedate = local_datetime(msgDateUTC)
			time = timedate[1]

			print ("Message " + msg["id"] + ", created by '" + msgCreator + "' on " + timedate[0] + " at " + time.lower() + " " + timedate[2])
			print ("  Text:" + msg["text"])
			print ()

			nrListed += 1

		if (index > self.lastMessageListed):
			self.lastMessageListed = index

		if (nrListed > 0):
			print ("Total messages listed: " + str(nrListed))
			print ()

		return None

	'''
		Returns True IF the address annotation matches the FQN or it is addressed
			to all (a broadcast message)
	'''
	def match (self, fqn, annotations):
		# This is ALWAYS the "address" annotation
		aNote = annotations[0]
							
		aValue = aNote["value"]
		dto = aValue["dto"]
									
		if (dto == fqn) or (dto == "all"):
			status = True
		else:
			status = False
													
		return status																

	'''
		Read messages from the channel and add the account owner's messages to the
			message list.
	'''
	def read (self):
		status = True

		since_id = "&since_id=" + self.lastMessageRead

		newMessagesLen = 0
		newMessagesCount = 0
		newMessagesList = []

		url = "https://alpha-api.app.net/stream/0/channels/" + self.chanID + "/messages" + self.accessToken + since_id + "&include_annotations=1&include_html=0&include_deleted=0&include_machine=1"

		result = requests.get(url)

		# For debugging purposes
		self.readURL = url
		self.readResultText = result.text
						
		responseJSON = json.loads(result.text)

		meta = responseJSON["meta"]
		self.operationErrorCode = meta["code"]

		if (self.operationErrorCode == 200):
			# We have new messages!
			newMessagesList = responseJSON["data"]
			newMessagesLen = len(newMessagesList)

			if (newMessagesLen > 0):
				newMessage = newMessagesList[0]

				# Check for last message read
				if (int(newMessage["id"]) == int(self.lastMessageRead)):
					# No new messages
					newMessagesLen = 0
					newMessagesList = []
					status = None
				else:
					# Add new messages in ascending order
					for index in range(newMessagesLen - 1, -1, -1):
						newMessage = newMessagesList[index]

						self.messages.append(newMessage)
						newMessagesCount += 1

						# Update last message read
						self.lastMessageRead = newMessage["id"]

					self.messagesCount += newMessagesCount
		else:
			# Bad read or request
			newMessagesList = []
			self.operationResultText = result.text
			status = False

		# Delay a bit for the API
		sleep(self.delaySecondsAPI)

		return newMessagesCount

	'''
		Write a new message to the channel, with annotations.
	'''
	def write (self, text, annotations):
		msgid = None

		url = "https://alpha-api.app.net/stream/0/channels/" + self.chanID + "/messages" + self.accessToken + "&include_annotations=1"

		# Create the data to put
		newMessage = {
			"text" : text,
			"annotations" : annotations
		}

		newMessageJSON = json.dumps(newMessage)

		# Write the new messaga to the channel.
		result = requests.post(url, data=newMessageJSON, headers=self.postHeaders)

		# For debugging purposes
		self.writeURL = url
		self.writeResultText = result.text

		messageJSON = json.loads(result.text)
		meta = messageJSON["meta"]

		self.operationErrorCode = meta["code"]

		if (self.operationErrorCode == 200):
			data = messageJSON["data"]
			msgid = data["id"]

			self.operationResultText = ""
		else:
			# Error - there was a problem creating the new message
			self.operationResultText = result.text
			self.displayError("write", 9999, "There was a problem writing a new message to channel " + self.chanID, meta)

		# Delay a bit for the API
		sleep(self.delaySecondsAPI)

		return msgid

	'''
		Setup channel information - internal function, not meant to be called from the outside
	'''
	def setup (self, response):
		meta = response["meta"]
		data = response["data"]

		self.readers = data["readers"]
		self.writers = data["writers"]
		self.ownerData = data["owner"]

		# This is information about the channel we need
		self.owner = self.ownerData["username"]
		self.chanID = data["id"]

		return None
'''
	End of Class ADN_Channel()
'''