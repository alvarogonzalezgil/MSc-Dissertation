import shutil
import sys
import os
import random

comfortable = []
affluent = []
adversity = []

input_folder_name = "D:\Temp\Load profiles"
for root, dirs, files in os.walk(input_folder_name):
    for profile_filename in files:
        if profile_filename.endswith((".csv")):
            if profile_filename.find('Comfortable') != -1:
                comfortable.append(profile_filename)
            elif profile_filename.find('Affluent') != -1:
                affluent.append(profile_filename)
            elif profile_filename.find('Adversity') != -1:
                adversity.append(profile_filename)
load_profiles = []

for i in range(0, 100):
    print i
    rand = random.uniform(0, 1)
    print rand
    if rand < 0.3:
        load_profiles.append(adversity[i%len(adversity)])
    elif rand < 0.6:
        load_profiles.append(affluent[i%len(affluent)])
    else:
        load_profiles.append(comfortable[i%len(comfortable)])

