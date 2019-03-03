#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
import math
import array

#array sorting func
def getkey(item):
	return item[0]

# inode=INUM  errors=ERR  errorsize=SZ  FILE   name=FNAME
if len(sys.argv) == 1:
	sys.exit("Parameter missing!")
ex=sys.argv[1].lower()
expr=re.compile(ex)

filelist=open("f2d_filelist.txt","w+")
filelist.write("# Regexp is "+sys.argv[1]+"\n\n")

with open("ntfsfindbad.log", "rb") as log:
	array = []
	total_sz = 0
	failed_sz = 0
	for byte_line in log:
		try:
			line=byte_line.decode('utf-8')
		except UnicodeDecodeError as uderr:
			line=byte_line[:uderr.args[2]].decode('utf-8')

		spl=line.split("name=")
		if re.search(expr,spl[1].lower()):
			array.append(int(line.split()[0].split("=")[1]))
			total_sz += int(line.split()[2].split("=")[1])
			filelist.write("###+++### "+spl[1])
		else:
			filelist.write("###---### "+spl[1])

print("Inodes match:",len(array),"Total size",total_sz,"bytes")

#to speed up lookups  we need a set not list
array=set(array)
print("Runlists selecting...",)
with open("ntfsfindbad_debug.log","r", encoding='utf-8') as log2:
#inode=0  part=0  offset=0xBFFFF000  fulloffset=0xBFFFF000  size=0x1000  type=0xB0  errors=1  errorsize=4096
	out_arr=[]
	for line in log2:
		spl=line.split()
		if line[:5] != "inode" or int(spl[0].split("=")[1]) not in array:
			continue

		out_arr.append([int(spl[3].split("=")[1],0), int(math.ceil(int(spl[4].split("=")[1],0)/512)*512)])

oasort=sorted(out_arr,key=getkey)

prev=[0,0]
output=[]

for value in oasort:
	delta=value[0]-(prev[0]+prev[1])
	if delta <= 0:
		prev=[prev[0],max(value[0]+value[1],prev[0]+prev[1])-prev[0]]
		try:
			output[-1] = prev

		except IndexError:
			output.append(prev)
	else:
		output.append(value)
		prev=value

print("done!")

fh=open("f2d.domain","w+")
fh.write("# Created by filelist2domain v.20170217\n")
fh.write("# Regexp is "+sys.argv[1]+"\n\n")
fh.write("0 ?\n")
prev=[0,0]

for value in output:
	fh.write("0x{0:08x} 0x{1:08x} ?\n".format(prev[0]+prev[1],value[0]-(prev[0]+prev[1])))
	fh.write("0x{0:08x} 0x{1:08x} +\n".format(value[0],value[1]))
	prev=value

print("Output file is saved as f2d.domain.")
