import os
import string

fileName = input("Please enter the name of the file: ")
STPfileName = "STP_" + fileName

lineBylineCopy = []
switchesInFile = []
writeSTP = False
secondLine = False
a = 0

if (os.path.exists(fileName) == True):
	newFile = open(STPfileName, 'w+')
	with open(fileName) as f:
		for line in f:
			if "net.get" in line:
				temp = line[13:16]
				temp = str.replace(temp, "'", "")
				switchesInFile.append(temp)
	with open(fileName) as f:
		lastValue = switchesInFile[-1]
		stringToFind = ("net.get('" + lastValue) 
		for line in f:
			if (secondLine == True and a != -1):
				newFile.write("import os\nos.system(")
				newFile.write("\"gnome-terminal -e 'bash -c \\\"sudo ~/pox/pox.py forwarding.l2_pairs info.packet_dump samples.pretty_log log.level --DEBUG   ; exec bash\\\"'\")")
				a = -1
			newFile.write(line)
			if stringToFind in line:
				writeSTP = True
				newFile.write("\n")
				continue
			if writeSTP == True:
				for i in switchesInFile:
					newFile.write("    " + i + ".cmd('ovs-vsctl set bridge " + i + " rstp-enable=true')\n")
				writeSTP = False
			secondLine = True
	print("Script completed successfully. Output file's name is " + STPfileName)
else:
	print("File doesn't exist")