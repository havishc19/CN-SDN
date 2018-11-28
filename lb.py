#!/usr/bin/env python

import requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit

class LoadBalancer:

	def __init__(self, h1, h2, h3):
		self.G = nx.Graph() 
		self.h1 = h1
		self.h2 = h2
		self.h3 = h3
		self.deviceInfoURL = "http://localhost:8080/wm/device/"
		self.linkURL = "http://localhost:8080/wm/topology/links/json"
		self.ruleURL = "http://127.0.0.1:8080/wm/staticflowpusher/json"
		
		self.ipMac = {} # Maps ip to MAC
		self.switchIDMap = {} # Maps ip to Switch DPID its connected to
		self.ipPortMap = {} # Maps ip to the port of the switch its connected to
		
		self.linkPortMap = {} #Maps link (tuple of switch DPIDs) to tuple of Port Numbers
		self.links = {}


		self.path = {}
		self.pathCost = {}
		self.enableStats()

	def enableStats(self):
		enableStats = "http://localhost:8080/wm/statistics/config/enable/json"
		requests.put(enableStats)

	def prettyPrint(self, m):
		for i in m:
			print(i, m[i])

	def getDeviceInformation(self):
		resp = requests.get(self.deviceInfoURL)
		if(resp.ok):
			data = json.loads(resp.content)
			for i in data:
				if(i["ipv4"]):
					ipAddr = i["ipv4"][0]
					ipAddr = ipAddr.encode('ascii','ignore')
					macAddr = i["mac"][0]
					macAddr = macAddr.encode('ascii', 'ignore')
					self.ipMac[ipAddr] = macAddr
					attachmentData = i["attachmentPoint"][0]
					# print(attachmentData)
					try:
						dataPathID = attachmentData["switchDPID"].encode('ascii', 'ignore')
						self.switchIDMap[ipAddr] = dataPathID
					except Exception as e:
						print(e)
						pass
					try:
						portNumber = str(attachmentData["port"])
						self.ipPortMap[ipAddr + "::" + dataPathID.split(":")[7]] = portNumber
					except Exception as e:
						print(e)
						pass
				# print(i["ipv4"])
			# print(self.ipMac)
			# print(self.switchIDMap)
			# print(self.ipPortMap)
		else:
			resp.raise_for_status()


	def findCommonLinks(self):
		resp = requests.get(self.linkURL)
		s = self.switchIDMap[self.h2]
		links = []
		if(resp.ok):
			data = json.loads(resp.content)
			# self.prettyPrint(data)
			for linkInfo in data:
				# print(linkInfo)

				srcSwitch = linkInfo['src-switch'].encode('ascii','ignore')
				dstSwitch = linkInfo['dst-switch'].encode('ascii','ignore')

				srcPort = str(linkInfo['src-port'])
				dstPort = str(linkInfo['dst-port'])

				srcDPID = srcSwitch.split(":")[7]
				dstDPID = dstSwitch.split(":")[7]

				self.G.add_edge(int(srcDPID,16), int(dstDPID,16))

				linkSrcDst = srcDPID + "::" + dstDPID
				linkDstSrc = dstDPID + "::" + srcDPID

				portSrcDst = str(srcPort) + "::" + str(dstPort)
				portDstSrc = str(dstPort) + "::" + str(srcPort)

				self.linkPortMap[linkSrcDst] = portSrcDst
				self.linkPortMap[linkDstSrc] = portDstSrc


				if(srcSwitch == s):
					links.append(dstSwitch)
				elif(dstSwitch == s):
					links.append(srcSwitch)
				else:
					continue

		else:
			resp.raise_for_status()

		sourceSwitchDPID = s.split(":")[7]
		self.links[sourceSwitchDPID] = links
		# print(self.links)


	def convertToHex(self, path):
		ans = []
		for i in path:
			temp = str(hex(i)).split("x",1)[1]
			ans.append(temp)
		return ans

	def findSwitchRoute(self):

		srcSwitchDPID = int(self.switchIDMap[self.h2].split(":")[7], 16)
		dstSwitchDPID = int(self.switchIDMap[self.h1].split(":")[7], 16)
		for path in nx.all_shortest_paths(self.G, source = srcSwitchDPID, target = dstSwitchDPID):
			switchDPIDs = self.convertToHex(path)
			pathID = ""
			tempPath = []
			for dpid in switchDPIDs:
				if(int(dpid,16) <= 15):
					pathID = pathID + "0" + dpid + "::"
					tempPath.append("00:00:00:00:00:00:00:0" + dpid)
				else:
					pathID = pathID + dpid + "::"
					tempPath.append("00:00:00:00:00:00:00:" + dpid)
			self.path[pathID[:-2]] = tempPath
		# print(self.path)

	def getDPID(self, switchID):
		return switchID.split(":")[7]


	def getCost(self, statsURL, portKey):
		response = requests.get(statsURL)
		if(response.ok):
			data = json.loads(response.content)
			# print(data)
			port = self.linkPortMap[portKey]
			port = port.split("::")[0]
			for i in data:
				# print(i)
				if(i["port"] == port):
					self.cost = self.cost + (int)(i['bits-per-second-tx'])
					# print((int)(i['bits-per-second-tx']))
		else:
			response.raise_for_status()

	def getLinkCost(self):

		for pathID in self.path:
			self.cost = 0
			srcSwitchID = self.switchIDMap[self.h2]
			srcDPID = self.getDPID(self.switchIDMap[self.h2])
			path = self.path[pathID]
			for link in path:
				tempDPID = self.getDPID(link)
				if(tempDPID == srcDPID):
					continue
				else:
					portKey = srcDPID + "::" + tempDPID
					statsURL = "http://localhost:8080/wm/statistics/bandwidth/" + srcSwitchID + "/0/json"
					self.getCost(statsURL, portKey)
					srcDPID = tempDPID
					srcSwitchID = link
			self.pathCost[pathID] = self.cost

		# print(self.pathCost)


	def systemCommand(self, cmd):
		terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
		terminalOutput, stderr = terminalProcess.communicate()
		# print "\n***", terminalOutput, "\n"



	

	def addRule(self, currentNode, src, dst, inPort, outPort):

		# print("Adding Rule: ", currentNode, src, dst, inPort, outPort)

		flow = {
				'switch':"00:00:00:00:00:00:00:" + currentNode,
			    "name":"flow" + str(self.count),
			    "cookie":"0",
			    "priority":"32768",
			    "in_port":inPort,
				"eth_type": "0x0800",
				"ipv4_src": src,
				"ipv4_dst": dst,
				"eth_src": self.ipMac[src],
				"eth_dst": self.ipMac[dst],
			    "active":"true",
			    "actions":"output=" + outPort
			}

		jsonData = json.dumps(flow)

		cmd = "curl -X POST -d \'" + jsonData + "\' " + self.ruleURL

		# print(cmd)
		self.systemCommand(cmd)

		self.count = self.count + 1


	def addFlow(self):
		self.count = 1
		shortestPath = min(self.pathCost, key=self.pathCost.get)
		print("Shortest Path: ", shortestPath)
		currNode = shortestPath.split("::")[0]
		nextNode = shortestPath.split("::")[1]
		port = self.linkPortMap[currNode + "::" + nextNode].split("::")
		outPort = port[0]
		inPort = port[1]
		# self.addRule(currNode, inPort, outPort)
		# self.addRule(currNode)
		self.addRule(currNode, self.h2, self.h1, inPort, outPort)
		self.addRule(currNode, self.h1, self.h2, outPort, inPort)

		

		bestPath = self.path[shortestPath]
		prevNode = currNode

		for i in range(0,len(bestPath)):
			currNode = bestPath[i]
			currNodeDPID = self.getDPID(currNode)
			if prevNode == self.getDPID(currNode):
				continue
			else:
				port = self.linkPortMap[currNodeDPID+"::"+prevNode]
				inPort = port.split("::")[0]
				outPort = ""
				if( i+1 < len(bestPath) and currNode == bestPath[i+1] ):
					# Stupid stuff!!
					i = i + 1
					continue
				elif( i+1 < len(bestPath) ): 
					# Not the last node
					port = self.linkPortMap[currNodeDPID + "::" + self.getDPID(bestPath[i+1]) ]
					outPort = port.split("::")[0]
				elif( currNode == bestPath[-1]): 
					#Last Node
					outPort = str(self.ipPortMap[ self.h1 + "::" + self.getDPID(self.switchIDMap[self.h1]) ])
					# outPort = str(hostPorts[h1+"::"+switch[h1].split(":")[7]])

				# self.addRule( currNodeDPID,str(inPort),str(outPort))
				self.addRule(currNodeDPID, self.h2, self.h1, inPort, outPort)
				self.addRule(currNodeDPID, self.h1, self.h2, outPort, inPort)
				# self.count += 2
				prevNode = currNodeDPID
		print("Done adding rule for path %s" %(shortestPath))



def printPaths(paths):
	counter = 1
	for i in paths:
		print("Path %s; Path ID: %s" %(str(counter), i))
		temp = ""
		for path in paths[i]:
			temp = temp + path + "->"
		temp = temp[:-2]
		print(temp)
		counter += 1

def main():
	h1 = ""
	h2 = ""
	h3 = ""
	print "Enter Host 1"
	h1 = int(input())
	print "\nEnter Host 2"
	h2 = int(input())
	print "\nEnter Host 3 (H2's Neighbour)"
	h3 = int(input())

	h1 = "10.0.0." + str(h1)
	h2 = "10.0.0." + str(h2)
	h3 = "10.0.0." + str(h3)

	lb = LoadBalancer(h1, h2, h3)

	i = 0
	while(1):
		i += 1
		lb.getDeviceInformation()
		lb.findCommonLinks()
		lb.findSwitchRoute()
		lb.getLinkCost()
		
		print("====================== Iteration %s =====================" %str(i))

		# Print Switch To Which H4 is Connectedk
		# print("H1: %s; Switch H2: %s; Switch H3: %s", lb.switchIDMap[h1]"Switch H4: ",lb.switchIDMap[h3], "\tSwitchH3: ", lb.switchIDMap[h2]


		# IP & MAC
		# print "\nIP & MAC\n\n", self.ipMac

		# Host Switch Ports
		# print "\nHost::Switch Ports\n\n", self.ipPortMap

		# Link Ports
		# print "\nLink Ports (SRC::DST - SRC PORT::DST PORT)\n\n", self.linkPortMap

		# Alternate Paths
		printPaths(lb.path)

		# Final Link Cost
		print("Past Costs: ", lb.pathCost)
		lb.addFlow()

		print "==========================================================================\n\n"

		time.sleep(10)

if __name__ == "__main__":
	main()