#!/usr/bin/env python

import re
import sys
import os

path = sys.argv[1]
if not os.path.exists(path):
    print "File does not exist: " + path
    sys.exit()

# print "Processing: " + path.split("/")[-1]

## ===== DaCapo evaluation-git+309e1fa cassandra PASSED in 5484 msec =====
# regex = re.compile(r"^===== DaCapo evaluation-git\+309e1fa (.+) PASSED in (\d+) msec =====$")
# file = open(path, "r")
# time_list = []
# for line in file:
#     result = regex.match(line)
#     if result:
#         time_list.append(int(result.group(2)))

# print time_list
# print sum(time_list) / len(time_list)

## ===== DaCapo evaluation-git+309e1fa cassandra completed warmup 17 in 5567 msec =====
regex = re.compile(r"^===== DaCapo evaluation-git\+309e1fa (.+) completed warmup (\d+) in (\d+) msec =====$")
file = open(path, "r")
time_list = []
for line in file:
    result = regex.match(line)
    if result and int(result.group(2)) >= 10:
        time_list.append(int(result.group(3)))

# print time_list
print sum(time_list) / len(time_list)
