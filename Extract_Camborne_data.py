import shutil
import sys
import os

os.chdir("D:\Temp\weather_2013")
raw_profile_file = open('midas_wxhrly_201301-201312.txt', 'r')
output_file = open('Camborne_data.txt', 'w')
line = raw_profile_file.readline()  # skipping header
while True:
    line = raw_profile_file.readline()
    if line == "" or line == "\n":
        break
    if line.find('1395') != -1:
        output_file.write(line)
output_file.close()
raw_profile_file.close()
    