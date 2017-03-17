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
#population distribution
nbComfortable = 0
nbAffluent = 0
nbAdverse = 0
nbHousesWithSolar = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "h:o:p:n:", ['solar', 'storage','player', 'help','useBatteryLoadFollowing','useCES'])
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
    elif opt == '--solar':
        useSolar = True
    elif opt == '--player':
        usePlayer = True
    elif opt in ("-p", "--solarPercentage"):
        solarPercentage = float(arg)/100
    elif opt == '--storage':
        useStorage = True
    elif opt == 'useBatteryLoadFollowing':
        useBatteryLoadFollowing = True
    elif opt == '--useCES':
        useCES = True


#file names
filename = destination_folder_name + '\\Model.glm'
waterheater_schedule_filename = "waterheater_schedule.glm"
appliances_schedule_filename = "appliances_schedule.glm"
battery_schedule_filename = "battery_schedule.glm"
feeder_line_configuration = "Test_Feeder_Line_Configurations.glm"
Price_Player_Filename = 'Price.player'
weather_Filename = 'WA-Seattle.tmy2'
weather_csv_filename = 'weather_uk_2013.csv'
power_player_file = 'power_player.csv'
BaseRecorderName = 'MarketTest'
#base recorder name
BaseRecorderName = 'MarketTest'


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



def createHVACController(houseNum,schedule_skew):
    controllerStr = '\tobject controller {\n'
    controllerStr += '\t\tname controller_%d;\n' % houseNum
    controllerStr += '\t\tschedule_skew %.0f;\n' % schedule_skew
    controllerStr += '\t\tmarket Market_1;\n'
    controllerStr += '\t\tcooling_setpoint cooling_setpoint;\n'
    controllerStr += '\t\theating_setpoint heating_setpoint;\n'
    controllerStr += '\t\tcontrol_mode DOUBLE_RAMP;\n'
    controllerStr += '\t\tresolve_mode DEADBAND;\n'
    controllerStr += '\t\tslider_setting_heat %.2f;\n' % slider_values[houseNum-1]
    controllerStr += '\t\tslider_setting_cool %.2f;\n' % slider_values[houseNum-1]
    #controllerStr += '\t\tcooling_base_setpoint cooling%d*%.2f+%.2f;\n' % (cooling_set,cool_night_diff,cool_night))
    #controllerStr += '\t\theating_base_setpoint heating%d*%.2f+%.2f;\n' % (heating_set,heat_night_diff,heat_night))
    controllerStr += '\t\tperiod %d;\n' % MarketPeriod
    controllerStr += '\t\tcooling_demand last_cooling_load;\n'
    controllerStr += '\t\theating_demand last_heating_load;\n'
    controllerStr += '\t\taverage_target my_avg_price;\n'
    controllerStr += '\t\tstandard_deviation_target my_std_price;\n'
    controllerStr += '\t\ttarget air_temperature;\n'
    controllerStr += '\t\tdeadband thermostat_deadband;\n'
    controllerStr += '\t\ttotal hvac_load;\n'
    controllerStr += '\t\tload hvac_load;\n'
    controllerStr += '\t\tstate power_state;\n'
    controllerStr += '\t};\n'
    return controllerStr

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
    recordersStr +='\tfile %s_transformer_power.csv;\n' % BaseRecorderName
    recordersStr +='\tparent controller_9999;\n'
    recordersStr +='\tinterval %d;\n' % RecorderInterval
    recordersStr +='\tproperty power_out_A.real,power_out_B.real,power_out_C.real,power_out.real,node3Meter:measured_real_energy,center_tap_AS:power_out.real,center_tap_BS:power_out.real,center_tap_CS:power_out.real;\n'
    recordersStr +='}\n'
    recordersStr +='\n'
    return recordersStr

def assign_load_profile():
    comfortable = []
    affluent = []
    adversity = []
    nbAffluent = 0
    nbComfortable = 0
    nbAdverse = 0

    input_folder_name = "D:\Temp\Load_profiles"
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
        rand = random.uniform(0, 1)
        if rand < 0.2:
            load_profiles.append(adversity[i%len(adversity)])
            nbAdverse += 1
        elif rand < 0.4:
            load_profiles.append(affluent[i%len(affluent)])
            nbAffluent += 1
        else:
            load_profiles.append(comfortable[i%len(comfortable)])
            nbComfortable += 1
    return load_profiles, nbAdverse, nbComfortable, nbAdverse

def copy_load_profile_file(filename, destination_folder):
    output_fullpath = destination_folder + "\\" + filename
    if os.path.exists(filename) == True:
        return
    input_fullpath = 'd:\\Temp\\Load_profiles\\'+filename
    if os.path.exists(input_fullpath) == True:
        shutil.copyfile(input_fullpath, output_fullpath)
    return

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

def createHouseMultiRecorder(houseName, houseNodeName, solarInverterMeterName, houseMeterName, houseBatteryInverterName, batteryName, batteryInverterMeterName):
    file.write('\tobject multi_recorder {\n')
    file.write('\t\tname %s_data;\n' % houseName)
    file.write('\t\tfile %s_data.csv;\n' % houseName)
    file.write('\t\tinterval %d;\n' % RecorderInterval)
    file.write('\t\tproperty %s:air_temperature, %s:outdoor_temperature, %s:measured_real_power, %s:measured_real_energy, %s:monthly_energy' %(houseName, houseName, houseNodeName, houseNodeName, houseMeterName))
    if houseUsingSolar == True:
        file.write(',%s:measured_real_power, %s:measured_real_energy\n' %(solarInverterMeterName, solarInverterMeterName))
        
    if houseUsingStorage == True:
        file.write(',%s:VA_Out.real, %s:state_of_charge, %s:measured_real_energy, %s:VA_Out.real, %s:measured_real_energy;\n' %(houseBatteryInverterName, batteryName,batteryInverterMeterName, houseSolarInverterName, solarInverterMeterName))
    file.write(';\n')
    file.write('\t};\n')

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
#schedule include files
file.write('#include "%s"\n' % waterheater_schedule_filename)
file.write('#include "%s"\n\n' % appliances_schedule_filename)
file.write('#include "%s"\n\n' % battery_schedule_filename)

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

#auction object
if Use_Controllers == True:
    if Use_Singlemarket == False:
        file.write('class auction {\n')
        file.write('\tdouble current_price_mean_24h;\n')
        file.write('\tdouble current_price_stdev_24h;\n')
        file.write('}\n\n')

        file.write('object auction {\n')
        file.write('\tname Market_1;\n')
        file.write('\tperiod %d;\n' % MarketPeriod)
        file.write('\tunit kW;\n')
        if MarketVerbose == True:
            file.write('\tverbose TRUE;\n')
        file.write('\tspecial_mode NONE;\n')
        file.write('\tprice_cap %f;\n' % MarketPriceCap)
        file.write('\tinit_price %f;\n' % MarketInitialPrice)
        file.write('\tinit_stdev %f;\n' % MarketInitialStdDev)
        file.write('\twarmup 0;\n')
        file.write('\tcapacity_reference_object controller_9999;\n')
        file.write('\tcapacity_reference_property power_out_real;\n')
        file.write('\tcapacity_reference_bid_price %f;\n' %
                MarketCapacityReferenceBid)
        file.write('\tmax_capacity_reference_bid_quantity %f;\n' %
                MarketMaxCapacityReferenceQuantity)
        file.write('\tcurve_log_file "%s_market_bids.csv";\n' %
                BaseRecorderName)
        file.write('\tcurve_log_info EXTRA;\n')
        file.write('\tobject recorder {\n')
        file.write(
            '\t\tproperty "current_market.clearing_price,current_market.clearing_quantity,fixed_price,fixed_quantity";\n')
        file.write('\t\tinterval %d;\n' % RecorderInterval)
        file.write('\t\tfile "%s_marketvalues.csv";\n' % BaseRecorderName)
        file.write('\t};\n')
        file.write('}\n\n')
    else:
        file.write('class auction {\n')
        file.write('     double current_price_mean_24h;\n')
        file.write('     double current_price_stdev_24h;\n')
        # create some new variables in stub auction that I can use to put
        # my values of std and mean, instead of rolling 24 hour
        file.write('     double my_avg_price;\n')
        file.write('     double my_std_price;\n')
        file.write('};\n\n')

        # auction
        file.write('object auction {\n')
        file.write('\tname Market_1;\n')
        file.write('\tperiod %d;\n' % MarketPeriod)
        if MarketVerbose == 1:
            file.write('\tverbose TRUE;\n')
        file.write('\tspecial_mode BUYERS_ONLY;\n')
        file.write('\tunit kW;\n')
        file.write('\tmy_avg_price %f;\n' % MarketInitialPrice)
        file.write('\tmy_std_price %f;\n' % MarketInitialStdDev)
        file.write('\tinit_price %f;\n' % MarketInitialPrice)
        file.write('\tinit_stdev %f;\n' % MarketInitialStdDev)
        file.write('\tcurve_log_file "%s_market_bids.csv";\n' %
                BaseRecorderName)
        file.write('\tcurve_log_info EXTRA;\n')
        file.write('\tobject player {\n')
        file.write('          property fixed_price;\n')
        file.write('          file %s;\n' % Price_Player_Filename)
        file.write('          loop 24;\n')
        file.write('     };\n')
        file.write('}\n\n')

#IEEE-4
file.write(createIEEE4NodeFeeder())

#residential houses
#Slider settings
# limit slider randomization to Olypen style
slider_values = []
use_solar_array = []

for i in range(1, NumHouses + 1):
    slider_value = 0.45 + 0.2 * random.normalvariate(0, 1)
    if slider_value < 0:
        slider_value = 0
    if slider_value > 1:
        slider_value = 1
    slider_values.append(slider_value)

if useSolar == True:
    for i in range(1, NumHouses + 1):
        perc = random.uniform(0, 1)
        if perc < solarPercentage:
            use_solar_array.append(True)
        else:
            use_solar_array.append(False)

for houseID in range(1, NumHouses + 1):
    load_profiles = []
    if usePlayer:
        load_profiles, nbAffluent, nbComfortable, nbAdverse = assign_load_profile()

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

    # file.write('object transformer {\n')
    # file.write('\tname house_%d_transformer;\n' % houseID)
    # file.write('\tphases %s;\n' % phaseStr)
    # file.write('\tfrom trip_node_%s;\n' % phaseStr)
    # file.write('\tto %s;\n' % houseNodeName)
    # file.write('\tconfiguration house_transformer;')
    # file.write('}\n\n')

    file.write('object triplex_meter {\n')
    file.write('\tname %s;\n' % houseNodeName)
    file.write('\tphases %s;\n' % phaseStr)
    file.write('\tnominal_voltage 120;\n')
    file.write('\tbill_day 1;\n')
    file.write('\tprice 1 $/kWh;\n')
    file.write('\tgroupid %s;\n' % netMeteringGroupId)
    file.write('}\n\n')

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

    #solar branch
    houseUsingSolar = useSolar == True and use_solar_array[houseID - 1]
    houseUsingStorage = houseUsingSolar and useStorage

    if  houseUsingSolar == True:
        nbHousesWithSolar += 1
        file.write('/////////////////////////////////////////////\n')
        file.write('//START: Solar Configuration for House%d\n' % houseID)
        file.write('/////////////////////////////////////////////\n')
        file.write('object triplex_line {\n')
        file.write('\tname house_%d_triple_line_solar;\n' % houseID)
        file.write('\tfrom %s;\n' % houseNodeName)
        file.write('\tto %s;\n' % solarInverterMeterName)
        file.write('\tphases %s;\n' % phaseStr)
        file.write('\tlength 10;\n')
        file.write('\tconfiguration triplex_line_configuration_1;\n')
        file.write('}\n\n')

        file.write('object triplex_meter {\n')
        file.write('\tname %s;\n' % solarInverterMeterName)
        file.write('\tphases %s;\n' % phaseStr)
        file.write('\tgroupid SOLARMETERING;\n')
        file.write('\tnominal_voltage 120;\n')
        file.write('}\n\n')

        file.write('object inverter {\n')
        file.write('\tname %s;\n' % houseSolarInverterName)
        file.write('\tphases %s;\n' % phaseStr)
        file.write('\tparent %s;\n' % solarInverterMeterName)
        file.write('\tgenerator_status ONLINE;\n')
        file.write('\tinverter_type FOUR_QUADRANT;\n')
        file.write('\tfour_quadrant_control_mode CONSTANT_PF;\n')
        file.write('\tgenerator_mode SUPPLY_DRIVEN;\n')
        file.write('\tinverter_efficiency .95;\n')
        file.write('\trated_power 3000;\n')
        file.write('}\n\n')

        file.write('object solar {\n')
        file.write('\tname house%i_solar;\n' % houseID)
        file.write('\tphases %s;\n' % phaseStr)
        file.write('\tparent %s;\n' % houseSolarInverterName)
        file.write('\tgenerator_status ONLINE;\n')
        file.write('\tgenerator_mode SUPPLY_DRIVEN;\n')
        file.write('\tpanel_type SINGLE_CRYSTAL_SILICON;\n')
        file.write('\tarea 150 ft^2;\n')
        file.write('\ttilt_angle 40.0;\n')
        file.write('\tefficiency 0.135;\n')
        file.write('\torientation_azimuth 270; //equator-facing (South)\n')
        file.write('\torientation FIXED_AXIS;\n')
        file.write('\tSOLAR_TILT_MODEL SOLPOS;\n')
        file.write('\tSOLAR_POWER_MODEL FLATPLATE;\n')
        file.write('}\n\n')

        file.write('/////////////////////////////////////////////\n')
        file.write('//END: Solar Configuration for House%d\n' % houseID)
        file.write('/////////////////////////////////////////////\n')

        
        #add storage
        if useStorage == True:
            file.write('/////////////////////////////////////////////\n')
            file.write('//START: Storage Configuration for House%d\n' % houseID)
            file.write('/////////////////////////////////////////////\n')
            file.write('object triplex_line {\n')
            file.write('\tname house_%d_triple_line_battery;\n' % houseID)
            file.write('\tfrom %s;\n' % houseNodeName)
            file.write('\tto %s;\n' % batteryInverterMeterName)
            file.write('\tphases %s;\n' % phaseStr)
            file.write('\tlength 10;\n')
            file.write('\tconfiguration triplex_line_configuration_1;\n')
            file.write('}\n\n')

            file.write('object triplex_meter {\n')
            file.write('\tname %s;\n' % batteryInverterMeterName)
            file.write('\tphases %s;\n' % phaseStr)
            file.write('\tgroupid BATTERYMETERING;\n')
            file.write('\tnominal_voltage 120;\n')
            file.write('}\n\n')

            file.write('object inverter {\n')
            file.write('\tname %s;\n' % houseBatteryInverterName)
            file.write('\tgenerator_status ONLINE;\n')
            file.write('\tparent %s;\n' % batteryInverterMeterName)
            file.write('\tinverter_efficiency .95;\n')
            file.write('\tinverter_type FOUR_QUADRANT;\n')
            file.write('\trated_power 3000;\t\t//Per phase rating\n') 

            if useBatteryLoadFollowing == True:
                file.write('\tfour_quadrant_control_mode LOAD_FOLLOWING;\n')
                file.write('\tsense_object %s;\n' % houseNodeName)
                file.write('\tcharge_on_threshold 0 kW;\n')
                file.write('\tcharge_off_threshold 0.1 kW;\n')
                file.write('\tdischarge_off_threshold 0.2 kW;\n')
                file.write('\tdischarge_on_threshold 0.7 kW;\n')
                file.write('\tmax_discharge_rate 3 kW;\n')
                file.write('\tmax_charge_rate 3 kW;\n')
                file.write('\tcharge_lockout_time 1;\n')
                file.write('\tdischarge_lockout_time 1;\n')
            else:
                file.write('\tgenerator_mode CONSTANT_PQ;\n')
                file.write('\tfour_quadrant_control_mode CONSTANT_PQ;\n')
                file.write('\tP_Out battery_schedule*3000;\n')
                file.write('\tQ_Out 0;\n')

            file.write('}\n\n')
 
            file.write('object battery {\n')
            file.write('\tname %s;\n' % batteryName)
            file.write('\tparent %s;\n' % houseBatteryInverterName)
            file.write('\tbattery_type LI_ION;\n')
            file.write('\tuse_internal_battery_model TRUE;\n')
            file.write('\tpower_factor 1.0;\n')
            file.write('\tgenerator_mode SUPPLY_DRIVEN;\n')

            if useBatteryLoadFollowing == True:
                file.write('\tuse_internal_battery_model TRUE;\n')
                file.write('\trated_power 3 kW;\n')
                file.write('\tbattery_capacity 7 kWh;\n')
                file.write('\tround_trip_efficiency 0.81;\n')
                file.write('\tstate_of_charge 0.5;\n')
            else:
                #file.write('\tscheduled_power battery_schedule*3000;\n')
                file.write('\tV_Max 260;\n')
                file.write('\tI_Max 15;\n')
                #file.write('\tP_Max 3000;\n')
                file.write('\tE_Max 7000;\n')
                #file.write('\tEnergy 7000;\n')
                file.write('\tbattery_capacity 7000;\n')
                file.write('\tbase_efficiency 1;\n')
                file.write('\tpower_type DC;\n')
                file.write('\tgenerator_status ONLINE;\n')
                file.write('\tstate_of_charge 0.5;\n')

            file.write('}\n\n')
            file.write('/////////////////////////////////////////////\n')
            file.write('//END: Storage Configuration for House%d\n' % houseID)
            file.write('/////////////////////////////////////////////\n')


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

    # #Breaker values
    # file.write('\tbreaker_amps 1000;\n')
    # file.write('\thvac_breaker_rating 1000;\n')
    # #Choose the heating and cooling schedule
    # file.write('\thvac_power_factor 0.97;\n')
    # file.write('\tfan_type ONE_SPEED;\n')
    # file.write('\tnumber_of_doors 2;\n')
    cooling_sp = random.normalvariate(cooling_setpoint_std, setpoint_deviation)
    heating_sp = random.normalvariate(heating_setpoint_std, setpoint_deviation)
    # file.write('\tcooling_setpoint %.2f;\n' % cooling_sp)
    # file.write('\theating_setpoint %.2f;\n' % heating_sp)

    #controllers code
    if Use_Controllers == True:
        file.write(createHVACController(houseID, schedule_skew))

    #Auxilliary load pieces
    # scale all of the end-use loads
    scalar1 = 324.9 / 8907 * floor_area**0.442
    scalar2 = 0.8 + 0.4 * random.uniform(0, 1)
    scalar3 = 0.8 + 0.4 * random.uniform(0, 1)
    resp_scalar = scalar1 * scalar2
    unresp_scalar = scalar1 * scalar3

    file.write('\tobject ZIPload {\n')
    file.write('\t\t// Unresponsive load\n')
    file.write('\t\tname house_%d_unresp_load;\n' % houseID)
    
    # file.write('\t\theatgain_fraction %.3f;\n' % 0.9)
    # file.write('\t\tpower_pf %.3f;\n' % 1)
    # file.write('\t\tcurrent_pf %.3f;\n' % 1)
    # file.write('\t\timpedance_pf %.3f;\n' % 1)
    #file.write('\t\timpedance_fraction %f;\n' % 0.2)
    #file.write('\t\tcurrent_fraction %f;\n' % 0.4)
    #file.write('\t\tpower_fraction %f;\n' % 0.4)
    if usePlayer == False:
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
 
        
    #water heaters
    # heat_element = 3.0 + 0.5 * random.randint(0, 5)
    # tank_set = 120 + 16 * random.uniform(0, 1)
    # therm_dead = 4 + 4 * random.uniform(0, 1)
    # tank_UA = 2 + 2 * random.uniform(0, 1)
    # water_sch = math.ceil(6 * random.uniform(0, 1))
    # water_var = 0.95 + random.uniform(0, 1) * 0.1  # +/-5% variability
    # wh_size_test = random.uniform(0, 1)
    # wh_size_rand = random.uniform(1, 3)
    # #TODO: derefine water heater sizing
    # file.write('\tobject waterheater {\n')
    # file.write('\t\tschedule_skew %.0f;\n' % schedule_skew)
    # file.write('\t\tconfiguration IS220;\n')
    # file.write('\t\theating_element_capacity %.1f kW;\n' % heat_element)
    # file.write('\t\ttank_setpoint %.1f;\n' % tank_set)
    # file.write('\t\ttemperature 132;\n')
    # file.write('\t\tthermostat_deadband %.1f;\n' % therm_dead)
    # file.write('\t\tlocation INSIDE;\n')
    # file.write('\t\ttank_UA %.1f;\n' % tank_UA)
    # if floor_area_mean < 1000:
    #     file.write('\t\tdemand small*%.02f;\n' % water_var)
    #     whsize = 20 + (wh_size_rand - 1) * 5
    #     file.write('\t\ttank_volume %.0f;\n' % whsize)
    # else:
    #     file.write('\t\tdemand large_%.0f*%.02f;\n' % water_var)
    #     whsize = 30 + (wh_size_rand - 1) * 10
    #     file.write('\t\ttank_volume %.0f;\n' % whsize)
    # file.write('\t};\n')

    #House Multi Recorder
    #createHouseMultiRecorder(houseName, houseNodeName, solarInverterMeterName, houseMeterName, houseBatteryInverterName, batteryName, batteryInverterMeterName)

    #End house
    file.write('}\n\n')

if useCES == True:
    createCES('trip_node_AS','AS')
    createCES('trip_node_BS','BS')
    createCES('trip_node_CS','CS')

#recorders
file.write(createRecorders(BaseRecorderName, RecorderInterval))

CreateNetMeteringRecorder('HOUSEMETERING')

if usePlayer == False:
    CreateNetMeteringRecorder(netMeteringGroupId)
else:
    CreateNetMeteringRecorder('NETMETERING_COMFORTABLE')
    CreateNetMeteringRecorder('NETMETERING_AFFLUENT')
    CreateNetMeteringRecorder('NETMETERING_ADVERSITY')

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
detailsFile.write('Number of houses (Comfortable) :%d:\n' % nbComfortable)
detailsFile.write('Number of houses (Affluent) :%d\n' % nbAffluent)
detailsFile.write('Number of houses (Adversity) :%d\n' % nbAdverse)
if useSolar == True:
    detailsFile.write('Number of solar panels: %d\n' % nbHousesWithSolar)
detailsFile.write('Using load player: %s\n' % usePlayer)
detailsFile.write('Using CES: %s\n' % useCES)
detailsFile.write('Using distributed storage: %s\n' % useStorage)
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
# if os.path.exists(destination_folder_name + weather_Filename) == False:
#     shutil.copy(weather_Filename, destination_folder_name)


#custom weather
# module climate;
# object csv_reader{
#        name CsvReader;
#        filename weather.csv;
# };
# object climate{
#        name MyClimate;
#        tmyfile weather.csv;
#        reader CsvReader;
# };
# // Weather changes state every 15-minutes and is only specifying temperature and humidity
# #sample weather CSV file
# $state_name=California
# $city_name=Berkeley
# temperature,humidity
# #month:day:hour:minute:second
# 1:01:00:00:00,50,0.05
# 1:01:00:15:00,62,0.16
# 1:01:00:30:00,78,0.15
# 1:01:00:45:00,74,0.14
# 1:01:02:00:00,72,0.12