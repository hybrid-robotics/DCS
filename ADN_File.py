'''
	Program:	ADN_File.py, Encapsulates the App.net Files API.

				Copyright (C) 2013 Dale Weber. ALL Rights Reserved. License to be chosen.

	Author:		Dale Weber <hybotics.pdx@gmail.com, @hybotics (App.Net and Twitter)>

	Version:	0.2.0 (Unstable)
	Date:		04-Oct-2013
	Purpose:	Preliminary, VERY ALPHA release
	
	Requires:	Python v3.3.1 or later
				PyTZ 2013b or later

'''
import json
import requests
import os

from datetime import datetime
from time import mktime, sleep, time

# You need the pytz 2013b version, or later
#from pytz import utc, timezone

'''
	App.net File class
'''
class ADN_File():
	account = ""
	token = ""

	accessToken = ""

	myFileName = "pod-hybotics-org.settings"
	myFileType = "net.hybotics.dcs.file.setttings"
	myFileMimeType = "text/plain"
	myFileID = "212674"
	myFileToken = "arb-0gcjRV1VcDfAnNlum7xxY8zjjHIpl8GmzKlHVWpM70wNBy3mUprB2txZ52M5KqNuVfyCaGOQWEqIH97D0_8__TMl_VBnhb2qzBZETWFTkXl4k7sXO65QsYqklCgq2lhXt7DjBRpvdhexkloKaB3ZP3S57evVtXGKY2-RAO5ITlHt5d4zvM5d6DKHx5wKK"

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

	fileBaseUrl = "https://alpha-api.app.net/stream/0/files"
	fileUrlSuffix = "&include_annotations=1&include_private=1&include_incomplete=1"
	fileHeaders = { "Content-Type" : "application/json" }

	def __init__(self, adnauth, fileName=None, fileType=None, mimeType=None, fileCreate=None):
		status = True

		# Channel data we save
		self.account = adnauth.username
		self.token = adnauth.token

		# Used in url creation
		self.accessToken =  "?access_token=" + self.token

		if (fileCreate):
			self.create(fileName, fileType)

		return None

	def create (self, fileName, fileType, filePublic, mimeType):
		status = True

		url = self.fileBaseUrl + self.accessToken + self.fileUrlSuffix
		headers = self.fileHeaders

#		{ "Content-Type: multipart/form-data; boundary=82481319dca6" }

		fileData = {
			"type" : fileType,
			"name" : fileName,
			"mime_type" : mimeType,
			"kind" : "other",
			"annotations" : [],
			"public" : filePublic
		}

		fileJSON = json.dumps(fileData)

		result = requests.post(url, headers=headers, data=fileJSON)

		self.operationResultText = result.text

		fileResult = json.loads(result.text)

		meta = fileResult["meta"]
		code = meta["code"]

		if (code == 200):
			data = fileResult["data"]
			self.myFileID = data["id"]
			self.myFileToken = data["file_token"]
		else:
			self.displayError("create", 9999, "There was a problem creating file" + fileName, meta)
			status = False

		return self.myFileID

	def open (self, fileID):
		status = True
		url = self.fileBaseUrl + "/" + fileID + "?file_token=" + self.myFileToken + self.fileUrlSuffix

		result = requests.get(url)

		fileJSON = json.loads(result.text)
		meta = fileJSON["meta"]
		code = meta["code"]

		if (code == 200):
			data = fileJSON["data"]
		else:
			self.displayError("open", 9999, "Problem opening file with ID " + fileID, meta)
			status = False

		return result.text

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
	End of class ADN_File()
'''
