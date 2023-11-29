Project:					Device Control System (DCS)

Author:						Dale Weber <hybotics.pdx@gmail.com> <@hybotics on Twitter and App.Net>

Purpose:					To provide an easily expandable way to control and connect smart devices
								in an "internet of things," built on top of App.net using the power
								of channel messages with annotations. Many devices can be run under a
								single App.net account.
								
Language:					Python v3.3.1 or later.

Description:				The Device Control System (DCS) defines a way for smart devices to connect and
								communicate with each other. The DCS understands the concept of Networks of
								Devices, Friends (devices that have authenticated with each other), Pending
								Tasks, and Pending Actions. The DCS contains a complete protocol for device
								authentication. 

Network:					App.Net (http://join.app.net), a paid platform for building applications for all
								types of uses, including (but not limited to) blogging, social media, photo
								galleries, group chat, and much more.

Dependencies:				Python v3.3.1 or later, and Pytz (2013b version, or later)

Files:
	ADN_Authenticator.py	Authenticates a user with App.net using the Password Flow method
	ADN_Channel.py			Encapsulates the App.net Channel and Message APIs
	ADN_File.py				Encapsulates the App.net File API
	
	DCS_Device.py			This is the main class for the Device Control System, and defines a
								device. ALL device classes in the DCS *MUST* inherit from this
								class.
									
Programs:
	DCS-Master.py			This is the DCS Master program. It does not do very much right now,
								other than just authenticate with clients, and send an occasional
								message to Pod (my Rasberry Pi).
										
	DCS-Client-Pod.py		This is my active client for Pod, my Rasberry Pi. It has two LEDs
								attached, green and red. The states of these LEDs can be changed
								by sending a message with a "request" annotation formatted as
								follows:
								
								myRequest			"request"
								myRequestParams		[ "green", "red" ]
								myRequestData  		{ "green" : "on" or "off", "red" : "on" or "off" }
# DCS
