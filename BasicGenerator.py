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
usePlayer = False
useBatteryLoadFollowing = False
useCES = False

#Number of houses to populate. 100 by default
NumHouses = 100
nbHousesWithSolar = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "h:o:", ['player', 'help'])
    print opts
except getopt.GetoptError:
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-h", "--help"):
        print "test.py -o <outputfile> -p <solarPercentage> --solar <use solar> --storage <use storage> --player <use player for load profile> --useBatteryLoadFollowing --useCES <Use CES>"
        sys.exit()
    elif opt in ("-o", "--oFolder"):
        destination_folder_name = arg
    elif opt == '-n':
        NumHouses = int(arg)
    elif opt == '--player':
        usePlayer = True



#file names
filename = destination_folder_name + '\\Model.glm'
waterheater_schedule_filename = "waterheater_schedule.glm"
appliances_schedule_filename = "appliances_schedule.glm"
feeder_line_configuration = "Test_Feeder_Line_Configurations.glm"
Price_Player_Filename = 'Price.player'
weather_Filename = 'WA-Seattle.tmy2'
weather_csv_filename = 'weather_uk_2013.csv'
power_player_file = 'power_player.csv'



#Minimum timestep (seconds)
MinTimeStep = 60
#Recorder interval
RecorderInterval = 600

#Time Parameters
StartTime = '2013-01-01 00:00:00'
EndTime = '2013-12-31 23:59:59'
TimeZone = 'GMT0BST'


#0 = FBS, 1 = NR
PowerflowSolver = 1  # NR
#Use controllers; yes = 1
Use_Controllers = False 
#Single or double market
Use_Singlemarket = True
MarketVerbose = False
MarketPeriod = 300  # market intervall = 5 minutes
MarketPriceCap = 3.5  # max. bid price = $3.5
MarketInitialPrice = 0.065  # Statistics initialization
MarketInitialStdDev = 0.1  # Statistics initialization
MarketCapacityReferenceBid = 1200
MarketMaxCapacityReferenceQuantity = 0

#house parameters
#dimesions
floor_area_mean = 900
#skew
residential_skew_std = 2700
residential_skew_max = 8100
#cooling/heating setpoints
cooling_setpoint_std = 77
heating_setpoint_std = 60
setpoint_deviation = 3

#Pause at exit?
PauseAtExit = 1

#demographic distribution
AAffluent = 'A-Affluent'
BAffluent = 'B-Affluent'
CAffluent = 'C-Affluent'
DAffluent = 'D-Affluent'
EAffluent = 'E-Affluent'
FComfortable = 'F-Comfortable'
GComfortable = 'G-Comfortable'
HComfortable = 'H-Comfortable'
IComfortable = 'I-Comfortable'
JComfortable = 'J-Comfortable'
KAdverse = 'K-Adversity'
LAdverse = 'L-Adversity'
MAdverse = 'M-Adversity'
NAdverse = 'N-Adversity'
OAdverse = 'O-Adversity'
PAdverse = 'P-Adversity'
QAdverse = 'Q-Adversity'

demographicGroupDistribution = {
    AAffluent : 9,
    BAffluent : 8,
    CAffluent : 9,
    DAffluent : 2,
    EAffluent : 6,
    FComfortable : 3,
    GComfortable : 4,
    HComfortable : 15,
    IComfortable : 6,
    JComfortable : 3,
    KAdverse : 6,
    LAdverse : 5,
    MAdverse : 7,
    NAdverse : 13,
    OAdverse : 4,
    PAdverse : 2,
    QAdverse : 2
    }

demographicGroupDistributionActual = {
    AAffluent : 0,
    BAffluent : 0,
    CAffluent : 0,
    DAffluent : 0,
    EAffluent : 0,
    FComfortable : 0,
    GComfortable : 0,
    HComfortable : 0,
    IComfortable : 0,
    JComfortable : 0,
    KAdverse : 0,
    LAdverse : 0,
    MAdverse : 0,
    NAdverse : 0,
    OAdverse : 0,
    PAdverse : 0,
    QAdverse : 0
    }

def createIEEE4NodeFeeder():
    #IEEE-4
    ieee4FeederStr = '///////////////////////////////////////////\n'
    ieee4FeederStr +='// BEGIN: IEEE-4 Feeder - main part\n'
    ieee4FeederStr +='///////////////////////////////////////////\n\n'
    ieee4FeederStr +='object node {\n'
    ieee4FeederStr +='\tname node1;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tbustype SWING;\n'
    ieee4FeederStr +='\tnominal_voltage 7200;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object overhead_line {\n'
    ieee4FeederStr +='\tname ohl12;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tfrom node1;\n'
    ieee4FeederStr +='\tto node2;\n'
    ieee4FeederStr +='\tlength 2000;\n'
    ieee4FeederStr +='\tconfiguration lc300;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object node {\n'
    ieee4FeederStr +='\tname node2;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tnominal_voltage 7200;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object transformer {\n'
    ieee4FeederStr +='\tname controller_9999;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tfrom node2;\n'
    ieee4FeederStr +='\tto node3;\n'
    ieee4FeederStr +='\tconfiguration tc400;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object node {\n'
    ieee4FeederStr +='\tname node3;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tnominal_voltage 2400;\n'
    ieee4FeederStr +='\tobject meter {\n'
    ieee4FeederStr +='\t\tname node3Meter;\n'
    ieee4FeederStr +='\t\tphases ABC;\n'
    ieee4FeederStr +='\t\tnominal_voltage 2400;\n'
    ieee4FeederStr +='\t};\n'

    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object overhead_line {\n'
    ieee4FeederStr +='\tname ohl34;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tfrom node3;\n'
    ieee4FeederStr +='\tto node4;\n'
    ieee4FeederStr +='\tlength 2500;\n'
    ieee4FeederStr +='\tconfiguration lc300;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object node {\n'
    ieee4FeederStr +='\tname node4;\n'
    ieee4FeederStr +='\tphases "ABCN";\n'
    ieee4FeederStr +='\tnominal_voltage 2400;\n'
    ieee4FeederStr +='}\n\n'


    #triplex portions
    ieee4FeederStr +='//////////////////////////////////////////////\n'
    ieee4FeederStr +='// BEGIN :Transformer and triplex_nodes\n'
    ieee4FeederStr +='//////////////////////////////////////////////\n\n'
    ieee4FeederStr +='//Triplex Transformers\n\n'
    ieee4FeederStr +='object transformer {\n'
    ieee4FeederStr +='\tname center_tap_AS;\n'
    ieee4FeederStr +='\tphases AS;\n'
    ieee4FeederStr +='\tfrom node4;\n'
    ieee4FeederStr +='\tto trip_node_AS;\n'
    ieee4FeederStr +='\tconfiguration AS_config;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object transformer {\n'
    ieee4FeederStr +='\tname center_tap_BS;\n'
    ieee4FeederStr +='\tphases BS;\n'
    ieee4FeederStr +='\tfrom node4;\n'
    ieee4FeederStr +='\tto trip_node_BS;\n'
    ieee4FeederStr +='\tconfiguration BS_config;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object transformer {\n'
    ieee4FeederStr +='\tname center_tap_CS;\n'
    ieee4FeederStr +='\tphases CS;\n'
    ieee4FeederStr +='\tfrom node4;\n'
    ieee4FeederStr +='\tto trip_node_CS;\n'
    ieee4FeederStr +='\tconfiguration CS_config;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='//Triplex nodes\n\n'
    ieee4FeederStr +='object triplex_node {\n'
    ieee4FeederStr +='\tname trip_node_AS;\n'
    ieee4FeederStr +='\tphases AS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_node {\n'
    ieee4FeederStr +='\tname trip_node_BS;\n'
    ieee4FeederStr +='\tphases BS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_node {\n'
    ieee4FeederStr +='\tname trip_node_CS;\n'
    ieee4FeederStr +='\tphases CS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='//Triplex meters\n\n'
    ieee4FeederStr +='object triplex_meter {\n'
    ieee4FeederStr +='\tname trip_meter_AS;\n'
    ieee4FeederStr +='\tphases AS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_meter {\n'
    ieee4FeederStr +='\tname trip_meter_BS;\n'
    ieee4FeederStr +='\tphases BS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_meter {\n'
    ieee4FeederStr +='\tname trip_meter_CS;\n'
    ieee4FeederStr +='\tphases CS;\n'
    ieee4FeederStr +='\tnominal_voltage 120;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='//Triplex lines\n\n'
    ieee4FeederStr +='object triplex_line {\n'
    ieee4FeederStr +='\tname trip_line_AS;\n'
    ieee4FeederStr +='\tphases AS;\n'
    ieee4FeederStr +='\tfrom trip_node_AS;\n'
    ieee4FeederStr +='\tto trip_meter_AS;\n'
    ieee4FeederStr +='\tlength 10;\n'
    ieee4FeederStr +='\tconfiguration triplex_line_configuration_1;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_line {\n'
    ieee4FeederStr +='\tname trip_line_BS;\n'
    ieee4FeederStr +='\tphases BS;\n'
    ieee4FeederStr +='\tfrom trip_node_BS;\n'
    ieee4FeederStr +='\tto trip_meter_BS;\n'
    ieee4FeederStr +='\tlength 10;\n'
    ieee4FeederStr +='\tconfiguration triplex_line_configuration_1;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='object triplex_line {\n'
    ieee4FeederStr +='\tname trip_line_CS;\n'
    ieee4FeederStr +='\tphases CS;\n'
    ieee4FeederStr +='\tfrom trip_node_CS;\n'
    ieee4FeederStr +='\tto trip_meter_CS;\n'
    ieee4FeederStr +='\tlength 10;\n'
    ieee4FeederStr +='\tconfiguration triplex_line_configuration_1;\n'
    ieee4FeederStr +='}\n\n'
    ieee4FeederStr +='//////////////////////////////////////////////\n'
    ieee4FeederStr +='// END: Pure Powerflow Portions\n'
    ieee4FeederStr +='//////////////////////////////////////////////\n\n'
    return ieee4FeederStr

def createRecorders(BaseRecorderName, RecorderInterval):
    recordersStr = 'object multi_recorder {\n'
    recordersStr +='\tfile %main_transformer_power.csv;\n'
    recordersStr +='\tparent controller_9999;\n'
    recordersStr +='\tinterval %d;\n' % RecorderInterval
    recordersStr +='\tproperty power_out_A.real,power_out_B.real,power_out_C.real,power_out.real,center_tap_AS:power_out.real,center_tap_BS:power_out.real,center_tap_CS:power_out.real;\n'
    recordersStr +='}\n'
    recordersStr +='\n'
    return recordersStr

def assign_load_profile():
    comfortable = []
    affluent = []
    adversity = []

    input_folder_name = "D:\Temp\Load_profiles"
    files = [f for f in os.listdir(input_folder_name) if os.path.isfile(os.path.join(input_folder_name, f))]
    demographicGroups = demographicGroupDistribution.keys()
    load_profiles = []
    numFiles = len(files)
    for i in range(0, 100):
        added = False
        while added == False:
            rand = random.randint(0, numFiles-1)
            filetoAdd = files[rand]
            for group in demographicGroups:
                if filetoAdd.endswith(".csv") and filetoAdd.find(group) != -1:
                    if demographicGroupDistributionActual[group] < demographicGroupDistribution[group]:
                        load_profiles.append(filetoAdd)
                        demographicGroupDistributionActual[group] += 1
                        added = True
                        break

    return load_profiles, demographicGroupDistributionActual

def copy_load_profile_file(filename, destination_folder):
    output_fullpath = destination_folder + "\\" + filename
    if os.path.exists(filename) == True:
        return
    input_fullpath = 'd:\\Temp\\Load_profiles\\'+filename
    if os.path.exists(input_fullpath) == True:
        shutil.copyfile(input_fullpath, output_fullpath)
    return


def CreateNetMeteringRecorder(netMeteringGroup):
    file.write('object collector {\n')
    file.write('\tfile global_%s.csv;\n' % netMeteringGroup.lower())
    file.write('\tgroup "class=triplex_meter AND groupid=%s";\n' % netMeteringGroup)
    file.write('\tproperty "sum(measured_real_power),sum(measured_real_energy),avg(measured_real_power),avg(measured_real_energy)";\n')
    file.write('\tinterval %d;\n' % RecorderInterval)
    file.write('}\n\n')
    return


#remove folder if already exists
if os.path.exists(destination_folder_name):
    shutil.rmtree(destination_folder_name)
#create folder
os.mkdir(destination_folder_name) 

file = open(filename, 'w+')
file.write("//IEEE 4-node file - generated\n")
file.write('//Generated with prefix ''%s''\n' % BaseRecorderName)
file.write('//Contained %d houses\n' % NumHouses)
file.write('//Run with mininum_timestep=%d and recorders set at %d\n' %
        (MinTimeStep, RecorderInterval))

if PowerflowSolver == 0:
    file.write('//FBS Powerflow solver\n\n')
else:
    file.write('//NR Powerflow solver\n\n')

#Definitions
file.write('#set suppress_repeat_messages=0\n')
file.write('#set minimum_timestep=%d\n' % MinTimeStep)
file.write('#set profiler=1\n')
file.write('#set randomseed=10\n')
if PauseAtExit == 1:
    file.write('#set pauseatexit=1\n')
file.write('//End header\n')

file.write('clock {\n')
file.write('\ttimezone %s;\n' % TimeZone)
file.write("\tstarttime '%s';\n" % StartTime)
file.write("\tstoptime '%s';\n" % EndTime)
file.write('}\n\n')
file.write('module tape;\n')
file.write('module climate;\n')
if Use_Controllers == True:
    file.write('module market;\n')
file.write('module residential {\n')
file.write('\timplicit_enduses NONE;\n')
file.write('}\n')
file.write('module generators;\n')

#module powerflow
file.write('module powerflow {\n')
if PowerflowSolver == 0:
    file.write('\tsolver_method FBS;\n')
else:
    file.write('\tsolver_method NR;\n')
    file.write('\tNR_iteration_limit 50;\n')
file.write('}\n\n')

#object climate
# file.write('object climate {\n')
# file.write('\tname "WeatherData";\n')
# file.write('\ttmyfile "%s";\n' % WeatherFile)
# file.write('\tinterpolate QUADRATIC;\n')
# file.write('\tobject recorder {\n')
# file.write('\t\tfile climate_out.csv;\n')
# file.write('\t\tinterval 600;\n')
# file.write('\t\tproperty temperature,humidity,solar_flux,solar_direct,solar_diff,pressure,wind_speed,rainfall;\n')
# file.write('\t};\n\n')
# file.write('}\n\n')

#csv_reader: custom weather
file.write('object csv_reader{\n')
file.write('\tname CsvReader;\n')
file.write('\tfilename %s;\n' % weather_csv_filename)
file.write('}\n')

file.write('object climate {\n')
file.write('\tname MyClimate;\n')
file.write('\ttmyfile %s;\n' % weather_csv_filename)
file.write('\treader CsvReader;\n')
file.write('\tobject recorder {\n')
file.write('\t\tfile climate_out.csv;\n')
file.write('\t\tinterval %i;\n' % RecorderInterval)
file.write('\t\tproperty temperature,humidity,solar_flux,solar_direct,pressure,wind_speed;\n')
file.write('\t};\n')
file.write('}\n\n')

file.write('#include "%s";\n\n' % feeder_line_configuration)


#IEEE-4
file.write(createIEEE4NodeFeeder())

#residential houses 

load_profiles = []
if usePlayer:
    load_profiles, populationDistribution = assign_load_profile()

for houseID in range(1, NumHouses + 1):
    phase = houseID % 3
    if phase == 1:
        phaseStr = "AS"
    elif phase == 2:
        phaseStr = "BS"
    else:
        phaseStr = "CS"

    netMeteringGroupId = 'NETMETERING'
    if usePlayer == True:
        lprofile = load_profiles[houseID-1]
        if lprofile.find('Comfortable') != -1:
            netMeteringGroupId += "_COMFORTABLE"
        elif lprofile.find('Affluent') != -1:
            netMeteringGroupId += "_AFFLUENT"
        elif lprofile.find('Adversity') != -1:
            netMeteringGroupId += "_ADVERSITY"


    houseName = 'house_%d' % houseID
    tripleMeterName = "trip_meter_"+phaseStr
    houseMeterName = "house%i_%s" % (houseID, tripleMeterName)
    solarInverterMeterName = houseMeterName + '_solar'
    batteryInverterMeterName = houseMeterName + '_battery'
    houseNodeName = "house_%d_node" % houseID
    houseBatteryInverterName = 'house%i_battery_inv' % houseID
    houseSolarInverterName = 'house%i_solar_inv' % houseID
    batteryName = 'house%i_battery' % houseID

    file.write('/////////////////////////////////////////////\n')
    file.write('//Configuration to include PV for %s\n' % houseName)
    file.write('/////////////////////////////////////////////\n')

    file.write('object triplex_line {\n')
    file.write('\tname house_%d_triple_line_%s;\n' % (houseID, phaseStr))
    file.write('\tfrom trip_node_%s;\n' % phaseStr)
    file.write('\tto %s;\n' % houseNodeName)
    file.write('\tphases %s;\n' % phaseStr)
    file.write('\tlength 10;\n')
    file.write('\tconfiguration triplex_line_configuration_1;\n')
    file.write('}\n\n')

    file.write('object triplex_meter {\n')
    file.write('\tname %s;\n' % houseNodeName)
    file.write('\tphases %s;\n' % phaseStr)
    file.write('\tnominal_voltage 120;\n')
    file.write('\tbill_day 1;\n')
    file.write('\tprice 1 $/kWh;\n')
    file.write('\tgroupid %s;\n' % netMeteringGroupId)
    file.write('}\n\n')

    file.write('/////////////////////////////////////////////\n')
    file.write('//PV entry point\n')
    file.write('//HouseId,%d,;\n' % houseID)
    file.write('//HouseNode,%s,;\n' % houseNodeName)
    file.write('//Phase,%s,;\n' % phaseStr)
    file.write('//END entry point: HouseId:%d\n' % houseID)
    file.write('/////////////////////////////////////////////\n\n')

    file.write('/////////////////////////////////////////////\n')
    file.write('//Storage entry point\n')
    file.write('//HouseId,%d,\n' % houseID)
    file.write('//HouseNode,%s,\n' % houseNodeName)
    file.write('//Phase,%s,\n' % phaseStr)
    file.write('//END entry point: HouseId:%d\n' % houseID)
    file.write('/////////////////////////////////////////////\n\n')

    #house branch
    file.write('object triplex_line {\n')
    file.write('\tname house_%d_triple_line_B;\n' % houseID)
    file.write('\tfrom %s;\n' % houseNodeName)
    file.write('\tto %s;\n' % houseMeterName)
    file.write('\tphases %s;\n' % phaseStr)
    file.write('\tlength 10;\n')
    file.write('\tconfiguration triplex_line_configuration_1;\n')
    file.write('}\n\n')

    file.write('object triplex_meter {\n')
    file.write('\tname %s;\n' % houseMeterName)
    file.write('\tphases %s;\n' % phaseStr)
    file.write('\tnominal_voltage 120;\n')
    file.write('\tbill_day 1;\n')
    file.write('\tprice 1 $/kWh;\n')
    file.write('\tgroupid HOUSEMETERING;\n')
    file.write('}\n\n')

    file.write('/////////////////////////////////////////////\n')
    file.write('//Houses\n')
    file.write('/////////////////////////////////////////////\n')

    file.write('object house {\n')
    file.write('\tname %s;\n' % houseName)

    file.write('\tparent %s;\n' % houseMeterName)

    file.write('\tgroupid Residential;\n')
    schedule_skew = random.normalvariate(0, residential_skew_std)
    #file.write('\tschedule_skew %.0f;\n' % schedule_skew)

    floor_area = random.normalvariate(floor_area_mean, 200)
    file.write('\tfloor_area %.0f;\n' % floor_area)
    file.write('\tnumber_of_stories %.0f;\n' % 2)
    ceiling_height = 8 + random.randint(1, 2)
    file.write('\tceiling_height %.0f;\n' % ceiling_height)
    file.write('\tthermal_integrity_level NORMAL;\n')
    file.write('\tglazing_layers TWO;\n')
    file.write('\tglass_type GLASS;\n')
    file.write('\twindow_frame WOOD;\n')
    # set init_temp
    init_temp = 69 + 4 * random.uniform(0, 1)
    file.write('\tair_temperature %.2f;\n' % init_temp)
    file.write('\tmass_temperature %.2f;\n' % init_temp)
    #Heating type information
    file.write('\theating_system_type GAS;\n')
    #file.write('\theating_system_type RESISTANCE;\n')
    file.write('\tcooling_system_type NONE;\n')

    #Zip load
    file.write('\tobject ZIPload {\n')
    file.write('\t\t// Unresponsive load\n')
    file.write('\t\tname house_%d_load;\n' % houseID)
    
    if usePlayer == False:
        #Auxilliary load pieces
        # scale all of the end-use loads
        scalar1 = 324.9 / 8907 * floor_area**0.442
        scalar2 = 0.8 + 0.4 * random.uniform(0, 1)
        scalar3 = 0.8 + 0.4 * random.uniform(0, 1)
        resp_scalar = scalar1 * scalar2
        unresp_scalar = scalar1 * scalar3
        file.write('\t\tschedule_skew %.0f;\n' % schedule_skew)
        file.write('\t\tbase_power unresponsive_loads_average*%.2f;\n' % unresp_scalar)
    else:
        lprofile = load_profiles[houseID-1]
        file.write('\t\tobject player {\n')
        file.write('\t\t\tproperty base_power;\n')
        #file.write('\t\t\tfile "power_player.csv";\n')
        file.write('\t\t\tfile "%s";\n' % lprofile)
        copy_load_profile_file(lprofile, destination_folder_name)
        file.write('\t\t};\n')
    file.write('\t};\n')
 
    #House Multi Recorder
    #createHouseMultiRecorder(houseName, houseNodeName, solarInverterMeterName, houseMeterName, houseBatteryInverterName, batteryName, batteryInverterMeterName)

    #End house
    file.write('}\n\n')


#recorders
file.write(createRecorders(BaseRecorderName, RecorderInterval))

CreateNetMeteringRecorder('HOUSEMETERING')

if usePlayer == False:
    CreateNetMeteringRecorder(netMeteringGroupId)
else:
    CreateNetMeteringRecorder('NETMETERING_COMFORTABLE')
    CreateNetMeteringRecorder('NETMETERING_AFFLUENT')
    CreateNetMeteringRecorder('NETMETERING_ADVERSITY')
  

#close the file handle
file.close()

#additional information
detailsFile = open("%s\\Details.out" % destination_folder_name, 'w')
detailsFile.write('Number of houses %d:\n' % NumHouses)
for group in populationDistribution:
    detailsFile.write('Number of houses (%s) :%d:\n' % (group, populationDistribution[group]))  

detailsFile.close()

#copy input files if they don't exist
if os.path.exists(destination_folder_name + waterheater_schedule_filename) == False:
    shutil.copy(waterheater_schedule_filename, destination_folder_name)
if os.path.exists(destination_folder_name + appliances_schedule_filename) == False:
    shutil.copy(appliances_schedule_filename, destination_folder_name)
if os.path.exists(destination_folder_name + battery_schedule_filename) == False:
    shutil.copy(battery_schedule_filename, destination_folder_name)
if os.path.exists(destination_folder_name + feeder_line_configuration) == False:
    shutil.copy(feeder_line_configuration, destination_folder_name)
if os.path.exists(destination_folder_name + Price_Player_Filename) == False:
    shutil.copy(Price_Player_Filename, destination_folder_name)
if os.path.exists(destination_folder_name + weather_csv_filename) == False:
    shutil.copy(weather_csv_filename, destination_folder_name)
if os.path.exists(destination_folder_name + power_player_file) == False:
    shutil.copy(power_player_file, destination_folder_name)
