Setup:
You need a couple of pip dependencies to run this project. So to get started with the setup process, follow the below steps (all in the current working directory of the project):
1.) virutalenv venv
2.) source venv/bin/activate
3.) pip install -r requirements.txt

There are two modules in this folder:
1. Load Balancer (lb.py)
2. Firewall (firewall.py)

Steps to run the firewall.py code:

1. Refer to this link to download and setup the Floodlight VM which comes pre-installed with Mininet.
	https://floodlight.atlassian.net/wiki/spaces/floodlightcontroller/pages/8650780/Floodlight+VM

2. The code requires floodlight version 1.2, which is not available in the VM. After installing floodlight VM, download floodlight V1.2 from this link
	http://www.projectfloodlight.org/download/

3. Change to the directory where floodlight V1.2 is installed and run the following in one terminal to start floodlight
	java -jar target/floodlight.jar


4. In another terminal, run the following command to start mininet
	make
	sudo mn --custom topology.py --topo mytopo --controller=remote,ip=127.0.0.1,port=6653

5. Run 'pingall' inside mininet to check if all packets are being sent to all hosts. (There should be no 'X' indicating a packet drop)

6. In another terminal execute the firewall code by typing the following with specified source and destination IP addresses and an 'allow' flag to enable or disable the flow.
 For example: python firewall.py --src_ip=10.0.0.1 --dst_ip=10.0.0.3 --allow=1

7. From the terminal that is running mininet, type xterm <src host>, say h1. This opens a new xterm terminal.

8. Inside the xterm terminal type ping <dst IP address>, say 10.0.0.3

9. Based on the value of allow, you will observe that the corresponding flow will either allow packets or disallow packets to be sent from source to destination.


Steps to run the lb.py code:

1.) Please start with a clean slate if you are coming from testing the firewall (bring down the floodlight controller, mininet and wireshark if they are still running).

2.) Change to the directory where floodlight V1.2 is installed and run the following in one terminal to start floodlight.
	java -jar target/floodlight.jar

3.) In another terminal, run the following command to start mininet
	make
	sudo mn --custom topology.py --topo mytopo --controller=remote,ip=127.0.0.1,port=6653

4.) Run 'pingall' inside mininet to check if all packets are being sent to all hosts. (There should be no 'X' indicating a packet drop). Repeat this a couple of times.

5.)  Type the following command in Mininet:
	xterm h1 h1

6.) In the first console, type 'ping 10.0.0.3' and in the second console, type 'ping 10.0.04'

7.) In a new tab, bring up a wireshark instance by running 'sudo wireshark'. Now inspect the s4-eth4 by selecting the same in 'Capture->Interfaces'. Check if you are receiving packets from both h1->h3 & h1->h4, if not do the same for s4-eth3. The point is you are supposed to notice traffic only on one link.

8.) Now in a new tab, run the lb.py script and give it the inputs 1,3,4 where 1 is host 1, 3 is host 2 and 4 is host 2's neighbor. Let the loadbalancer run for a few iterations to gather statistics about the network and push rules based on that.

9.) After a couple of iterations, inspect both links s4-eth4 & s4-eth3. Now you should notice packets of h1->h3 on one link and h1->h4 on another link.  