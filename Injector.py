import datetime
import random
import math
import shutil
import sys
import getopt
import os

useSolar = False
useStorage = False
solarPercentage = 0
useBatteryLoadFollowing = False
useCES = False

#file names
battery_schedule_filename = "battery_schedule.glm"
feeder_line_configuration = "Test_Feeder_Line_Configurations.glm"
weather_csv_filename = 'weather_uk_2013.csv'
power_player_file = 'power_player.csv'
battery_loadfollowing_schedule_dist_filename = "battery_loadfollowing_schedule_dist.glm"
battery_loadfollowing_schedule_CES_filename = "battery_loadfollowing_schedule_CES.glm"


#Number of houses to populate. 100 by default
NumHouses = 100
nbHousesWithSolar = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "h:i:p:o:", ['solar', 'storage','player', 'help','useBatteryLoadFollowing','useCES'])
    print opts
except getopt.GetoptError:
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        print "test.py -o <outputfile> -p <solarPercentage> --solar <use solar> --storage <use storage> --player <use player for load profile> --useBatteryLoadFollowing --useCES <Use CES>"
        sys.exit()
    elif opt == '-i':
        input_folder_name = arg
    elif opt =='-o':
        destination_folder_name = arg
    elif opt == '--solar':
        useSolar = True
    elif opt in ("-p", "--solarPercentage"):
        solarPercentage = float(arg)/100
    elif opt == '--storage':
        useStorage = True
    elif opt == '--useBatteryLoadFollowing':
        useBatteryLoadFollowing = True
    elif opt == '--useCES':
        useCES = True


filename = input_folder_name + '\\Model.glm'

#Minimum timestep (seconds)
MinTimeStep = 60
#Recorder interval
RecorderInterval = 600


def createCES(fromNode, phase):
    cesMeterName = 'ces_%s_meter' % phase
    cesInverterName = 'ces_inverter_%s' % phase
    cesBatteryName = 'ces_battery_%s' % phase
    centerTapName = 'center_tap_%s' % phase

    file.write('/////////////////////////////////////////////\n')
    file.write('//START: Community Energy Storage Configuration \n')
    file.write('/////////////////////////////////////////////\n')
    file.write('object triplex_line {\n')
    file.write('\tname %s_node_triple_line_battery;\n' % phase)
    file.write('\tfrom %s;\n' % fromNode)
    file.write('\tto %s;\n' % cesMeterName)
    file.write('\tphases %s;\n' % phase)
    file.write('\tlength 10;\n')
    file.write('\tconfiguration triplex_line_configuration_1;\n')
    file.write('}\n\n')

    file.write('object triplex_meter {\n')
    file.write('\tname %s;\n' % cesMeterName)
    file.write('\tphases %s;\n' % phase)
    file.write('\tnominal_voltage 120;\n')
    file.write('\tgroupid CESMETERING;\n')

    file.write('\tobject inverter {\n')
    file.write('\t\tname %s;\n' % cesInverterName)
    file.write('\t\tphases %s;\n' % phase)
    file.write('\t\tgenerator_status ONLINE;\n')
    file.write('\t\tinverter_efficiency .95;\n')
    file.write('\t\tinverter_type FOUR_QUADRANT;\n')
    file.write('\t\trated_power 10000;\t\t//Per phase rating\n') 
    file.write('\t\tfour_quadrant_control_mode LOAD_FOLLOWING;\n')
    file.write('\t\tsense_object %s;\n' % centerTapName)
    file.write('\t\tcharge_on_threshold 15 kW;\n')
    file.write('\t\tcharge_off_threshold 18 kW;\n')
    file.write('\t\tdischarge_off_threshold 25 kW;\n')
    file.write('\t\tdischarge_on_threshold 28 kW;\n')
    file.write('\t\tcharge_lockout_time 1;\n')
    file.write('\t\tdischarge_lockout_time 1;\n')
    file.write('\t\tmax_discharge_rate 8 kW;\n')
    file.write('\t\tmax_charge_rate 8 kW;\n')

    file.write('\t\tobject battery {\n')
    file.write('\t\t\tname %s;\n' % cesBatteryName)
    file.write('\t\t\tbattery_type LI_ION;\n')
    file.write('\t\t\tuse_internal_battery_model TRUE;\n')
    file.write('\t\t\tpower_factor 1.0;\n')
    file.write('\t\t\tgenerator_mode SUPPLY_DRIVEN;\n')
    file.write('\t\t\tuse_internal_battery_model TRUE;\n')
    file.write('\t\t\trated_power 10 kW;\n')
    file.write('\t\t\tbattery_capacity 40 kWh;\n')
    file.write('\t\t\tround_trip_efficiency 0.81;\n')
    file.write('\t\t\tstate_of_charge 0.5;\n')

    file.write('\t\t};\n')
    file.write('\t};\n')
    file.write('}\n\n')

        #Multi Recorder
    file.write('object multi_recorder {\n')
    file.write('\tname ces_%s_data;\n' % phase)
    file.write('\tfile ces_%s_data.csv;\n' % phase)
    file.write('\tinterval %d;\n' % RecorderInterval)
    file.write('\tproperty %s:VA_Out.real, %s:state_of_charge, %s:power_out.real;\n' %(cesInverterName, cesBatteryName, centerTapName))
    file.write('}\n')

    file.write('/////////////////////////////////////////////\n')
    file.write('//END: CES\n')
    file.write('/////////////////////////////////////////////\n')

def CreateNetMeteringRecorder(netMeteringGroup):
    file.write('object collector {\n')
    file.write('\tfile global_%s.csv;\n' % netMeteringGroup.lower())
    file.write('\tgroup "class=triplex_meter AND groupid=%s";\n' % netMeteringGroup)
    file.write('\tproperty "sum(measured_real_power),sum(measured_real_energy),avg(measured_real_power),avg(measured_real_energy)";\n')
    file.write('\tinterval %d;\n' % RecorderInterval)
    file.write('}\n\n')
    return

# def createHouseMultiRecorder(houseName, houseNodeName, solarInverterMeterName, houseMeterName, houseBatteryInverterName, batteryName, batteryInverterMeterName):
#     file.write('\tobject multi_recorder {\n')
#     file.write('\t\tname %s_data;\n' % houseName)
#     file.write('\t\tfile %s_data.csv;\n' % houseName)
#     file.write('\t\tinterval %d;\n' % RecorderInterval)
#     file.write('\t\tproperty %s:air_temperature, %s:outdoor_temperature, %s:measured_real_power, %s:measured_real_energy, %s:monthly_energy' %(houseName, houseName, houseNodeName, houseNodeName, houseMeterName))
#     if houseUsingSolar == True:
#         file.write(',%s:measured_real_power, %s:measured_real_energy\n' %(solarInverterMeterName, solarInverterMeterName))
        
#     if houseUsingStorage == True:
#         file.write(',%s:VA_Out.real, %s:state_of_charge, %s:measured_real_energy, %s:VA_Out.real, %s:measured_real_energy;\n' %(houseBatteryInverterName, batteryName,batteryInverterMeterName, houseSolarInverterName, solarInverterMeterName))
#     file.write(';\n')
#     file.write('\t};\n')
#     return


#schedule include files
battery_file = ''
if useStorage == True:
    if useBatteryLoadFollowing == True:
        battery_file = battery_loadfollowing_schedule_dist_filename
    else:
        battery_file = battery_schedule_filename
elif useCES == True:
    if useBatteryLoadFollowing == True:
        battery_file = battery_loadfollowing_schedule_CES_filename

use_solar_array = []
if useSolar == True:
    for i in range(1, NumHouses + 1):
        perc = random.uniform(0, 1)
        if perc < solarPercentage:
            use_solar_array.append(True)
        else:
            use_solar_array.append(False)


inputFile = open(filename, "r")
contents = inputFile.readlines()
inputFile.close()
newContents = []


for index in range(0, len(contents)):
    idx = index
    if idx and index < idx:
        continue
    line = contents[index]
    newContents.append(line)
    if line.find('End header') != -1:
        newContents.append('\n')
        newContents.append('#include "%s"\n\n' % battery_file)   
    if line.find('PV entry point') != -1:   
        houseID = int(contents[index+1].split(',')[1])
        houseNodeName = contents[index+2].split(',')[1]
        phaseStr = contents[index+3].split(',')[1]
        idx += 4
        # houseName = 'house_%d' % houseID
        tripleMeterName = "trip_meter_"+phaseStr
        houseMeterName = "house%i_%s" % (houseID, tripleMeterName)
        solarInverterMeterName = houseMeterName + '_solar'
        batteryInverterMeterName = houseMeterName + '_battery'
        # houseNodeName = "house_%d_node" % houseID
        houseBatteryInverterName = 'house%i_battery_inv' % houseID
        houseSolarInverterName = 'house%i_solar_inv' % houseID
        batteryName = 'house%i_battery' % houseID


        #solar branch
        houseUsingSolar = useSolar == True and use_solar_array[houseID - 1]
        houseUsingStorage = houseUsingSolar and useStorage

        if  houseUsingSolar == True:
            nbHousesWithSolar += 1
            newContents.append('/////////////////////////////////////////////\n')
            newContents.append('//START: Solar Configuration for House%d\n' % houseID)
            newContents.append('/////////////////////////////////////////////\n')
            newContents.append('object triplex_line {\n')
            newContents.append('\tname house_%d_triple_line_solar;\n' % houseID)
            newContents.append('\tfrom %s;\n' % houseNodeName)
            newContents.append('\tto %s;\n' % solarInverterMeterName)
            newContents.append('\tphases %s;\n' % phaseStr)
            newContents.append('\tlength 10;\n')
            newContents.append('\tconfiguration triplex_line_configuration_1;\n')
            newContents.append('}\n\n')

            newContents.append('object triplex_meter {\n')
            newContents.append('\tname %s;\n' % solarInverterMeterName)
            newContents.append('\tphases %s;\n' % phaseStr)
            newContents.append('\tgroupid SOLARMETERING;\n')
            newContents.append('\tnominal_voltage 120;\n')
            newContents.append('}\n\n')

            newContents.append('object inverter {\n')
            newContents.append('\tname %s;\n' % houseSolarInverterName)
            newContents.append('\tphases %s;\n' % phaseStr)
            newContents.append('\tparent %s;\n' % solarInverterMeterName)
            newContents.append('\tgenerator_status ONLINE;\n')
            newContents.append('\tinverter_type FOUR_QUADRANT;\n')
            newContents.append('\tfour_quadrant_control_mode CONSTANT_PF;\n')
            newContents.append('\tgenerator_mode SUPPLY_DRIVEN;\n')
            newContents.append('\tinverter_efficiency .95;\n')
            newContents.append('\trated_power 3000;\n')
            newContents.append('}\n\n')

            newContents.append('object solar {\n')
            newContents.append('\tname house%i_solar;\n' % houseID)
            newContents.append('\tphases %s;\n' % phaseStr)
            newContents.append('\tparent %s;\n' % houseSolarInverterName)
            newContents.append('\tgenerator_status ONLINE;\n')
            newContents.append('\tgenerator_mode SUPPLY_DRIVEN;\n')
            newContents.append('\tpanel_type SINGLE_CRYSTAL_SILICON;\n')
            newContents.append('\tarea 150 ft^2;\n')
            newContents.append('\ttilt_angle 40.0;\n')
            newContents.append('\tefficiency 0.135;\n')
            newContents.append('\torientation_azimuth 270; //equator-facing (South)\n')
            newContents.append('\torientation FIXED_AXIS;\n')
            newContents.append('\tSOLAR_TILT_MODEL SOLPOS;\n')
            newContents.append('\tSOLAR_POWER_MODEL FLATPLATE;\n')
            newContents.append('}\n\n')

            newContents.append('/////////////////////////////////////////////\n')

            
            #add storage
            if useStorage == True:
                newContents.append('/////////////////////////////////////////////\n')
                newContents.append('//START: Storage Configuration for House%d\n' % houseID)
                newContents.append('/////////////////////////////////////////////\n')
                newContents.append('object triplex_line {\n')
                newContents.append('\tname house_%d_triple_line_battery;\n' % houseID)
                newContents.append('\tfrom %s;\n' % houseNodeName)
                newContents.append('\tto %s;\n' % batteryInverterMeterName)
                newContents.append('\tphases %s;\n' % phaseStr)
                newContents.append('\tlength 10;\n')
                newContents.append('\tconfiguration triplex_line_configuration_1;\n')
                newContents.append('}\n\n')

                newContents.append('object triplex_meter {\n')
                newContents.append('\tname %s;\n' % batteryInverterMeterName)
                newContents.append('\tphases %s;\n' % phaseStr)
                newContents.append('\tgroupid BATTERYMETERING;\n')
                newContents.append('\tnominal_voltage 120;\n')
                newContents.append('}\n\n')

                newContents.append('object inverter {\n')
                newContents.append('\tname %s;\n' % houseBatteryInverterName)
                newContents.append('\tgenerator_status ONLINE;\n')
                newContents.append('\tparent %s;\n' % batteryInverterMeterName)
                newContents.append('\tinverter_efficiency .95;\n')
                newContents.append('\tinverter_type FOUR_QUADRANT;\n')
                newContents.append('\trated_power 3000;\t\t//Per phase rating\n') 

                if useBatteryLoadFollowing == True:
                    newContents.append('\tfour_quadrant_control_mode LOAD_FOLLOWING;\n')
                    newContents.append('\tsense_object %s;\n' % houseNodeName)
                    newContents.append('\tcharge_on_threshold charge_on_schedule;\n')
                    newContents.append('\tcharge_off_threshold charge_off_schedule;\n')
                    newContents.append('\tdischarge_off_threshold discharge_off_schedule;\n')
                    newContents.append('\tdischarge_on_threshold discharge_on_schedule;\n')
                    newContents.append('\tmax_discharge_rate 2 kW;\n')
                    newContents.append('\tmax_charge_rate 3 kW;\n')
                    newContents.append('\tcharge_lockout_time 1;\n')
                    newContents.append('\tdischarge_lockout_time 1;\n')
                else:
                    newContents.append('\tgenerator_mode CONSTANT_PQ;\n')
                    newContents.append('\tfour_quadrant_control_mode CONSTANT_PQ;\n')
                    newContents.append('\tP_Out battery_schedule*3000;\n')
                    newContents.append('\tQ_Out 0;\n')

                newContents.append('}\n\n')
    
                newContents.append('object battery {\n')
                newContents.append('\tname %s;\n' % batteryName)
                newContents.append('\tparent %s;\n' % houseBatteryInverterName)
                newContents.append('\tbattery_type LI_ION;\n')
                newContents.append('\tuse_internal_battery_model TRUE;\n')
                newContents.append('\tpower_factor 1.0;\n')
                newContents.append('\tgenerator_mode SUPPLY_DRIVEN;\n')

                if useBatteryLoadFollowing == True:
                    newContents.append('\tuse_internal_battery_model TRUE;\n')
                    newContents.append('\trated_power 3 kW;\n')
                    newContents.append('\tbattery_capacity 7 kWh;\n')
                    newContents.append('\tround_trip_efficiency 0.81;\n')
                    newContents.append('\tstate_of_charge 0.5;\n')
                else:
                    #newContents.append('\tscheduled_power battery_schedule*3000;\n')
                    newContents.append('\tV_Max 260;\n')
                    newContents.append('\tI_Max 15;\n')
                    #newContents.append('\tP_Max 3000;\n')
                    newContents.append('\tE_Max 7000;\n')
                    #newContents.append('\tEnergy 7000;\n')
                    newContents.append('\tbattery_capacity 7000;\n')
                    newContents.append('\tround_trip_efficiency 0.9;\n')
                    newContents.append('\tpower_type DC;\n')
                    newContents.append('\tgenerator_status ONLINE;\n')
                    newContents.append('\tstate_of_charge 0.5;\n')

                newContents.append('}\n\n')
                newContents.append('/////////////////////////////////////////////\n')
                newContents.append('//END: Storage Configuration for House%d\n' % houseID)
                newContents.append('/////////////////////////////////////////////\n')

#create folder
if os.path.exists(destination_folder_name):
    shutil.rmtree(destination_folder_name)
os.mkdir(destination_folder_name) 

outputfile = destination_folder_name + '\\Model.glm'
file = open(outputfile , "w")
newContents = "".join(newContents)
file.write(newContents)

#createHouseMultiRecorder(houseName, houseNodeName, solarInverterMeterName, houseMeterName, houseBatteryInverterName, batteryName, batteryInverterMeterName)

if useCES == True:
    createCES('trip_node_AS','AS')
    createCES('trip_node_BS','BS')
    createCES('trip_node_CS','CS')


if useSolar == True:
    CreateNetMeteringRecorder('SOLARMETERING')

if useStorage:
    CreateNetMeteringRecorder('BATTERYMETERING')

if useCES:
    CreateNetMeteringRecorder('CESMETERING')       

#close the file handle
file.close()

#additional information
detailsFile = open("%s\\Details.out" % destination_folder_name, 'w')
detailsFile.write('Number of houses %d:\n' % NumHouses)

if useSolar == True:
    detailsFile.write('Number of solar panels: %d\n' % nbHousesWithSolar)
detailsFile.write('Using CES: %s\n' % useCES)
detailsFile.write('Using distributed storage: %s\n' % useStorage)
detailsFile.close()

print battery_file
if os.path.exists(input_folder_name + battery_file) == False:
    shutil.copy(battery_file, destination_folder_name)
if os.path.exists(input_folder_name + feeder_line_configuration) == False:
    shutil.copy(feeder_line_configuration, destination_folder_name)
if os.path.exists(input_folder_name + weather_csv_filename) == False:
    shutil.copy(weather_csv_filename, destination_folder_name)
if os.path.exists(input_folder_name + power_player_file) == False:
    shutil.copy(power_player_file, destination_folder_name)