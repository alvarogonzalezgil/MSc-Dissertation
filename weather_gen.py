import os


def parse_line(line):
    values = []
    is_date = True
    for value_str in line.split(','):
        if is_date == True:
            is_date = False
            continue
        value = float(value_str)
        values.append(value)
    return values


def interpolate(value1, value2, interval, step):
    return value1 + step * (value2 - value1) / interval

def convertDegCtoFahrenheit(fromValue):
    return fromValue*1.8 + 32

#converting from Wm2 into Wft2
def convertSolarRadiation(fromValue):
    return fromValue*0.09290304

#converting from knots to miles/hr
def convertWindSpeed(fromValue):
    return fromValue*1.15078

days_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

out_file = open('weather_uk_2013.csv', 'w+')
# this file contains hourly weather data (temperature, humidity)
in_weather_file = open('Hourly_weather.csv', 'r')
# reading header
weather_header_line = in_weather_file.readline()
# this file contains minute radiation data (direct, diffuse, global)
in_radiation_file = open('Radiation.csv', 'r')
# reading header
radiatin_header_line = in_radiation_file.readline()

# reading first line of values
weather_previous_line = in_weather_file.readline()
prevous_weather_values = parse_line(weather_previous_line)

# write header
#month:day:hour:minute:second
out_file.write('$state_name=Cornwall\n')
out_file.write('$city_name=Camborne\n')
out_file.write('$lat_deg=50\n')
out_file.write('$lat_min=13\n')
out_file.write('$long_deg=-5\n')
out_file.write('$long_min=19\n')
out_file.write('$timezone_offset=0\n')
out_file.write('temperature,humidity,solar_global,solar_diff,solar_dir,wind_speed\n')
out_file.write('#month:day:hour:minute:second\n')

for month in range(1, 13):
    for day in range(1, days_month[month-1] + 1):
        for hour in range(0, 24):
            weather_next_line = in_weather_file.readline()
            next_weather_values = parse_line(weather_next_line)

            for minutes in range(0, 60):
                radiation_line = in_radiation_file.readline()
                radiation_values = parse_line(radiation_line)
                timestamp = str.split(radiation_line,",")[0]
                expected_timpestamp = "2013-%.2d-%.2dT%.2d:%.2d" % (month,day,hour,minutes)
                if timestamp != expected_timpestamp:
                    print "Missing timestamp: expected %s vs %s" % (expected_timpestamp, timestamp)
                interpolated_weather_values = []
                for i in range(0, len(next_weather_values)):
                    interpolated_weather_values.append(interpolate(
                        prevous_weather_values[i], next_weather_values[i], 60, minutes))
                
                air_temperature = convertDegCtoFahrenheit(interpolated_weather_values[1])
                relative_humidity = interpolated_weather_values[2]/100
                global_radiation = convertSolarRadiation(radiation_values[0])
                diffuse_radiation = convertSolarRadiation(radiation_values[2])
                direct_radiation = convertSolarRadiation(radiation_values[1])
                wind_speed = convertWindSpeed(interpolated_weather_values[0])
                #correction in case global and direct are 0; diffuse should be 0 as well
                if global_radiation == 0 and direct_radiation == 0 and diffuse_radiation > 0:
                    diffuse_radiation = 0
                out_file.write('%.2d:%.2d:%.2d:%.2d:00,%f,%f,%f,%f,%f,%f\n' % (
                    month, 
                    day, 
                    hour, 
                    minutes,
                    air_temperature,
                    relative_humidity,
                    global_radiation,
                    diffuse_radiation,
                    direct_radiation,
                    wind_speed
                    ))
            
            prevous_weather_values = next_weather_values
# close all open files
out_file.close()
in_weather_file.close()
in_radiation_file.close()
