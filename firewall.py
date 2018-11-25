#!/usr/bin/env python

import requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit

def getResponse(url,choice):

	response = requests.get(url)

	if(response.ok):
		jData = json.loads(response.content)
		if(choice=="deviceInfo"):
			deviceInformation(jData)
		elif(choice=="findSwitchLinks"):
			findSwitchLinks(jData,switch[h2])
		
	else:
		response.raise_for_status()

def findSwitchLinks(data,s):
	global switchLinks
	global linkPorts
	global G

	links=[]
	for i in data:
		src = i['src-switch'].encode('ascii','ignore')
		dst = i['dst-switch'].encode('ascii','ignore')

		srcPort = str(i['src-port'])
		dstPort = str(i['dst-port'])

		srcTemp = src.split(":")[7]
		dstTemp = dst.split(":")[7]

		G.add_edge(int(srcTemp,16), int(dstTemp,16))

		tempSrcToDst = srcTemp + "::" + dstTemp
		tempDstToSrc = dstTemp + "::" + srcTemp

		portSrcToDst = str(srcPort) + "::" + str(dstPort)
		portDstToSrc = str(dstPort) + "::" + str(srcPort)

		linkPorts[tempSrcToDst] = portSrcToDst
		linkPorts[tempDstToSrc] = portDstToSrc

		if (src==s):
			links.append(dst)
		elif (dst==s):
			links.append(src)
		else:
			continue

	switchID = s.split(":")[7]
	switchLinks[switchID]=links

def deviceInformation(data):
	global switch
	global deviceMAC
	global hostPorts
	switchDPID = ""
	for i in data:
		if(i['ipv4']):
			ip = i['ipv4'][0].encode('ascii','ignore')
			mac = i['mac'][0].encode('ascii','ignore')
			deviceMAC[ip] = mac
			for j in i['attachmentPoint']:
				for key in j:
					temp = key.encode('ascii','ignore')
					if(temp=="switchDPID"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ip] = switchDPID
					elif(temp=="port"):
						portNumber = j[key]
						switchShort = switchDPID.split(":")[7]
						hostPorts[ip+ "::" + switchShort] = str(portNumber)

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	print "\n***", terminalOutput, "\n"



def flowRule():
	inp = {
		"src_ip" : "10.0.0.1",
		"dst_ip" : "10.0.0.3",
		"src_port" : "80",
		"dst_port" : "300",
		"priority" : ""
		}

	flow = {
			"ipv4_src":"10.0.0.1" ,

			"out_port":"6000",

			"ipv4_dst":"10.0.0.3",
		
			"name":"", 

			"switch":"",
		
			"priority":"32768",
	    
	    	'switch':"",
	    
	    	"eth_type": "0x0800",
	  	
	  		"actions":"DROP",

	    	"active":"true",
	    	}

	for i in range(1,9):
		flow["switch"] = str(i)
		flow["name"] = "flow"+str(i)
		jsonData = json.dumps(flow)
	
	 	cmd = "curl -X POST -d \'"+ jsonData+"\' " +"http://127.0.0.1:8080/wm/staticflowpusher/json"
	 	systemCommand(cmd)



def sdn_firewall():
	linkURL = "http://localhost:8080/wm/topology/links/json"
	getResponse(linkURL,"findSwitchLinks")
	flowRule()



global h1,h2,h3

h1 = ""
h2 = ""

print "Enter Host 1"
h1 = int(input())
print "\nEnter Host 2"
h2 = int(input())
print "\nEnter Host 3 (H2's Neighbour)"
h3 = int(input())

h1 = "10.0.0." + str(h1)
h2 = "10.0.0." + str(h2)
h3 = "10.0.0." + str(h3)


while True:

	switch = {}

	# Mac of H3 And H4
	deviceMAC = {}
	hostPorts = {}


	switchLinks = {}
	linkPorts = {}
	G = nx.Graph()

	try:

		deviceInfo = "http://localhost:8080/wm/device/"
		getResponse(deviceInfo,"deviceInfo")

		sdn_firewall()
		time.sleep(60)

	except KeyboardInterrupt:
		break
		exit()



