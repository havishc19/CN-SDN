#!/usr/bin/env python

import requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
from sys import exit
import argparse

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	print "\n***", terminalOutput, "\n"

def add_firewall_rule(inp_dict, switches):
	flow = {
			"ipv4_src": inp_dict["src_ip"] ,
			"out_port": inp_dict["src_port"],
			"ipv4_dst":	inp_dict["dst_ip"],
			"in_port": inp_dict["dst_port"],
			"name":"", 
			"switch":"",
			"priority": "32768",
	    	"eth_type": "0x0800",
	  		"actions":"DROP",
	    	"active":"true",
	    	}

	for key in flow.keys():
		if (flow[key] == "" or flow[key] is None) and (key not in ("name", "switch")):
			del flow[key]

	for switch in switches:
		flow["switch"] = str(switch)
		flow["name"] = "flow"+str(i)
		jsonData = json.dumps(flow)
	
	 	cmd = "curl -X POST -d \'"+ jsonData+"\' " +"http://127.0.0.1:8080/wm/staticflowpusher/json"
	 	systemCommand(cmd)

def getSwitchIds():
	switchIDs = []
	url = "http://localhost:8080/wm/core/controller/switches/json"
	resp = requests.get(url)
	switches = json.loads(resp.text)
	for switch in switches:
		switchIDs.append(switch["switchDPID"])
	return switchIDs

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--src_ip', help='ipv4 for the source')
	parser.add_argument('--dst_ip', help='ipv4 for the destination')
	parser.add_argument('--src_port', help='tcp port for the source')
	parser.add_argument('--dst_port', help='tcp port for the destination')
	args = parser.parse_args()
	args = vars(args)
	switches = getSwitchIds()
	add_firewall_rule(args, switches)
