#!/usr/bin/env python

#netfpga.py - A simple web.py application allow remote debugging on Altera FPGA
#Project NetFPGA created by Shengye Wang, Fudan University 01/25/2013
#Inspired by Prof. Michael Taylor, UC San Diego
#See http://shengye.me for more information

#This file may be used or modified with no restriction.
#Raw copies as well as modified copies may be distributed without limitation.

import web
import time
import random
import socket
import os

render = web.template.render('templates')

#Change the following lines to meet actual 
MAX_PER_TIME = 60.0 #max protection time
filedir = '/home/shengye/netfpga/upload_files' # change this to the directory you want to store the file in.

HOST = 'localhost' 
PORT = 1337 #modify with the port number in tcl script

CMD_LEN = 47 #length of string send to jtag server
NUM_LEN = 34 #length data field

session_time = time.time()
session_id = '000000000'
status = "IDLE" #global variable holding current status.

def get_status(): #update and return status
	global status
	global session_time
	past_time = time.time() - session_time
	if (past_time < 0 or past_time > MAX_PER_TIME) and (status == "PROTECTED"):
		status = "UNPROTECTED"
	return status

def set_status(new_status): #set status
	global status
	global session_id
	status = new_status
	if (status == "IDLE"):
		session_id = '000000000'

def check_sid(sid): #check if client is the current user
	global session_id
	return sid == session_id

def conn(): #connect to TCP server
	global sock
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((HOST, PORT))
	except socket.error, msg:
		return ("[ERROR] %s\n" % msg[1])

def send_recv(buf): #send data to jtag server and get the response
	global sock
	#Send
	bcnt = sock.send(buf+'\n')
	#print "Send is " + buf + " len = " + str(bcnt)
	#Receive
	buf = sock.recv(1024)
	#print "Recv is " + buf + " len = " + str(len(buf))
	return buf

def num_to_str(num, leng = NUM_LEN): #convert integer to binary stored in string(reversed)
	rtn = ''
	for i in range(leng):
		rtn = str(1 if (num & (1 << i)) > 0 else 0) + rtn
	rtn = rtn[::-1] #Revert return value
	return rtn

def str_to_num(s, signext = False): #convert binary stored in string(reversed) to integer
	s = s[::-1] #Revert s
	rtn = 0
	if (s[0] == '1' and signext):
		for i in range(len(s)):
			rtn += 2**(len(s) - 1 - i) if (s[i] == '0') else 0
		rtn += 1
		rtn = -rtn
	else:
		for i in range(len(s)):
			rtn += 2**(len(s) - 1 - i) if (s[i] == '1') else 0
	return rtn


urls = (
	'/', 'index',
	'/new', 'New',
	'/giveup', 'GiveUp',
	'/upload', 'Upload',
	'/program', 'Program',
	'/startserver', 'StartServer',
	'/inittarget', 'InitTarget',
	'/interaction', 'Interaction',
	'/nav', 'Nav'
)

class index:
	def GET(self):
		global session_time
		global MAX_PER_TIME
		web.header("Content-Type","text/html; charset=utf-8")
		page = "Status is " + get_status()
		return render.index(get_status(), check_sid(web.cookies().get('sid')), "%.1f" % (time.time() - session_time), "%.1f" % (MAX_PER_TIME))

class New:
	def GET(self):
		global session_time
		global session_id
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		showNavBar = False #Should show the navigation bar
		if (get_status() == "PROTECTED"):
			if check_sid(web.cookies().get('sid')):
				content += "Serving current user. Please give up before creating new session.\n"
				showNavBar = True
			else:
				content += "Serving other user in protected period.\nACCESS DENIED.\n"
		else:
			content += "Killing background utilities.\n"
			content += os.popen("./stopall.sh").read()
			content += "Genearting new session ID.\n"
			session_time = time.time()
			new_sid = str(random.randint(100000000, 999999999)); #sid is 9 digits integer in string
			session_id = new_sid
			set_status("PROTECTED")
			content += "New seesion ID is " + str(new_sid) + ".\n"
			content += "Status is " + get_status() + ".\n"
			web.setcookie("sid", new_sid, expires=3600)
			showNavBar = True
		return render.new(get_status(), showNavBar, content)

class GiveUp:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		showNavBar = False #Should show the navigation bar
		if check_sid(web.cookies().get('sid')):
			content += "Giving up.\n"
			content += "Killing background utilities.\n"
			content += os.popen("./stopall.sh").read()
			set_status("IDLE")
			content += "Status is " + get_status() + ".\n"
			showNavBar = True
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.giveup(get_status(), showNavBar, content)

class Upload:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			pass
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.upload(get_status(), check_sid(web.cookies().get('sid')), content, check_sid(web.cookies().get('sid')))

	def POST(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			x = web.input(myfile={})
			global filedir
			if 'myfile' in x: # to check if the file-object is created
				filepath=x.myfile.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
				filename=filepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)
				fout = open(filedir +'/current.sof','w') # creates the file where the uploaded file should be stored
				fout.write(x.myfile.file.read()) # writes the uploaded file to the newly created file.
				fout.close() # closes the file, upload complete.
				os.popen('cp ' + filedir +'/current.sof' + ' ' + filedir +'/' + web.cookies().get('sid') + '.sof').read() #make a copy to store sof file, comment this if not needed
				content += "File Accepted.\n"
			else:
				content += "File not received.\n"
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.upload(get_status(), check_sid(web.cookies().get('sid')), content, check_sid(web.cookies().get('sid')))

class Program:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			#content += "Killing background utilities.\n"
			content += os.popen("./stopall.sh").read()
			#content += "Programming.\n"
			content += os.popen("./program.sh").read()
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.program(get_status(), check_sid(web.cookies().get('sid')), content)

class StartServer:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			content += "Killing background utilities.\n"
			content += os.popen("./stopall.sh").read()
			content += "Starting server.\n"
			content += os.popen("./tcpserver.sh").read()
			content += "Please continue.\n"
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.startserver(get_status(), check_sid(web.cookies().get('sid')), content)

class InitTarget:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			connrtn = conn()
			if (connrtn == None):
				send_recv(46 * '0' + '1') # Reset
				send_recv(47 * '0')       # Release reset signal
				content += "Core reseted.\n"
			else:
				content += "Communication Failed.\n" + connrtn
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.inittarget(get_status(), check_sid(web.cookies().get('sid')), content)

class Interaction:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		inputReq = False
		autoRefresh = False
		inputChannel = ""
		tryMore = True
		if check_sid(web.cookies().get('sid')):
			connrtn = conn()
			if (connrtn == None):
				while tryMore:
					buf = send_recv(47 * '0')
					if (buf[42] == '1'): #output request
						res = "Output request #" + str(str_to_num(buf[34:38])) + " : " + str(str_to_num(buf[0:34], signext = True));
						buf = 44 * '0' + '100'; #set out_ack
						send_recv(buf)
						buf = 44 * '0' + '000'; #set out_ack
						send_recv(buf)

						io_history = open('interaction.txt', 'a')
						io_history.write(res + "\n")
						io_history.close()
					else:
						inputReq = buf[43] == '1'
						inputChannel = str(str_to_num(buf[38:42]))
						tryMore = False
				autoRefresh = not inputReq
				sock.close()
			else:
				content += "Communication Failed.\n" + connrtn

			io_history = open('interaction.txt', 'r')
			content += io_history.read()
			io_history.close()

		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.interaction(get_status(), check_sid(web.cookies().get('sid')), content, autoRefresh, inputReq, inputChannel)

	def POST(self):
		web.header("Content-Type","text/html; charset=utf-8")
		content = ""
		if check_sid(web.cookies().get('sid')):
			connrtn = conn()
			if (connrtn == None):
				try:
					num = int(web.input().get('val', None))
				except:
					content += "Invalid input, assuming 0\n"
					num = 0
				buf = send_recv(47 * '0')
				if (buf[43] == '1'): #input request
					res = "Input request #" + str(str_to_num(buf[38:42])) + " : " + str(num)
					buf = num_to_str(num) + 10 * '0' + '010'; #set in_ack
					send_recv(buf)
					buf = num_to_str(num) + 10 * '0' + '000'; #clr in_ack
					send_recv(buf)
					io_history = open('interaction.txt', 'a')
					io_history.write(res + "\n")
					io_history.close()
				sock.close()
				raise web.seeother('/interaction')
			else:
				content += connrtn
		else:
			content += "Serving other user.\nACCESS DENIED.\n"
		return render.interaction(get_status(), check_sid(web.cookies().get('sid')), content, False, False, '')

class Nav:
	def GET(self):
		return render.nav(get_status())

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()


