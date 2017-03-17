import shutil
import sys
import getopt
import os

input_folder_name = "."
output_folder_name = input_folder_name
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o:h:")
except getopt.GetoptError:
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print "load_profile_generator.py -i <inputFolder> -o <outputFolder>"
        sys.exit()
    elif opt == "-i":
        input_folder_name = arg
    elif opt == '-o':
        output_folder_name = arg

filename_list = []
houseId_list = []


def createfilename(line):
    values = line.split(',')
    classification = values[5].strip('\n')
    newfilename = "%s-%s-%s.csv" % (values[0], values[4], classification)
    return newfilename


def extract_date_value(line):
    values = line.split(',')
    newHouseId = values[0]
    # if len(values) < 6:
    #     print line
    #     return "", "", ""
    try:
        datetime = values[2][0:19]
        newLoad = -9999
        if values[3] != 'Null':
            newLoad = float(values[3])
            newLoad = newLoad * 2 #load needs to be multiplied by to con convert from W/halfhour to W/h
    except IndexError:
        print 'invalid line:' + line + '!\n'
    return newHouseId, datetime, newLoad


def create_file(filenameStr):
    if filenameStr in filename_list:
        # open existing file and append
        new_file = open(filenameStr, 'a')
        print 'I should not be here in theory for ' + filenameStr
    else:
        # create new file
        filename_list.append(filenameStr)
        new_file = open(filenameStr, 'w')
    return new_file

def add_newline(fileToWrite, datetime, load):
    if datetime[0:4] == '2013':
        fileToWrite.write('%s,%s\n' % (datetime, load))
    return


os.chdir(input_folder_name)

for root, dirs, files in os.walk(input_folder_name):
    for raw_filename in files:
        if raw_filename.endswith((".csv")):
            raw_profile_file = open(raw_filename, 'r')
            line = raw_profile_file.readline()  # skipping header
            line = raw_profile_file.readline()  # reading first line of data
            filename = createfilename(line)
            load_profile_file = create_file(filename)
            houseId, datetime, load = extract_date_value(line)
            currentHouseId = houseId
            add_newline(load_profile_file, datetime, load)

            while True:
                line = raw_profile_file.readline()
                if line == "" or line == "\n":
                    break
                houseId, datetime, load = extract_date_value(line)
                if load == -9999:  #ignore bad entries
                    continue

                if houseId != currentHouseId:
                    currentHouseId = houseId
                    load_profile_file.close()
                    filename = createfilename(line)
                    load_profile_file = create_file(filename)
                add_newline(load_profile_file, datetime, load)

            load_profile_file.close()
            # end of file; close raw data file
            raw_profile_file.close()

print filename_list
