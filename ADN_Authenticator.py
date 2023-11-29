'''
	Program:	ADN_Authenticator.py, an App.net authenticator using the Password Flow method.

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
	Authenticates the current user by using the Password Flow authentication
'''
class ADN_Authenticator():
	token = ""
	username = ""
	userid = ""

	urlbase = "https://account.app.net/oauth/access_token"
	scopes = "stream messages write_post basic follow"

	def __init__ (self, username, userpassword):
		app_id = "qMjVyqk9A45Kwdn92bLMD6UagFc6j7GV"				#os.environ["APPNET_SNAPPYID"]

		pw_grant_secret = "ggSwEDCPQ6z4NUBvzFwr79rj2Q8b7k6u"		#os.environ["APPNET_DEV_PWGRANT"]

		pwflow_data = {
			"client_id" : app_id,											#os.environ["APPNET_SNAPPYID"],
			"password_grant_secret" : pw_grant_secret,					#os.environ["APPNET_DEV_PWGRANT"],
			"grant_type" : "password",
			"username" : username,										#os.environ["APPNET_HYBOTICSID"],
			"password" : userpassword,									#os.environ["APPNET_HYBOTICSPW"],
			"scope" : self.scopes
		}

		result = requests.post(self.urlbase, data=pwflow_data)

		auth_data = json.loads(result.text)

		self.username = auth_data["username"]
		self.userid = auth_data["user_id"]
		self.token = auth_data["access_token"]

		return None