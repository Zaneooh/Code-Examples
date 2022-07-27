"""
Rev 1 S-QMS-SPEC-33756
heater_temp_measurement.py  

This script runs the heater at the user specified temperature and duration, collects heater debug data, and
generates data plots and .csv output files.

@copyright LumiraDx, 2021. All rights reserved. This code is provided on an
           "AS IS" basis. LumiraDx DISCLAIMS ALL WARRANTIES, TERMS AND
           CONDITIONS WITH RESPECT TO THE CODE, EXPRESS, IMPLIED, STATUTORY
           OR OTHERWISE, INCLUDING WARRANTIES, TERMS OR CONDITIONS OF
           MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT
           AND SATISFACTORY QUALITY. TO THE FULL EXTENT ALLOWED BY LAW,
           LUMIRADX ALSO EXCLUDES ANY LIABILITY, WHETHER BASED IN CONTRACT
           OR TORT (INCLUDING NEGLIGENCE), FOR INCIDENTAL, CONSEQUENTIAL,
           INDIRECT, SPECIAL OR PUNITIVE DAMAGES OF ANY KIND, OR FOR LOSS
           OF REVENUE OR PROFITS, LOSS OF BUSINESS, LOSS OF INFORMATION OR
           DATA, OR OTHER FINANCIAL LOSS ARISING OUT OF OR IN CONNECTION
           WITH THE USE OR PERFORMANCE OF THE CODE.

Modification History

AUTHOR    DATE        REASON FOR CHANGE
--------  --------    ----------------------------------
ZOO       28-03-2022    Initial code.
ZOO       20-04-2022   DCR-29217
"""

import csv
import logging
from amira_parser import AmiraErrorCodes, AmiraEventCodes
from amira_test_state_machine import AmiraTestEventParserReturnValues, AmiraTestOperations
from datetime import datetime
from typing import List
from twisted.python import log


import serial
import sys
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ***************************************************
# constant values to control the test flow execution
# ***************************************************

# default temperature setpoint in degrees C - this value will be used unless the user enters a valid setpoint
# when prompted




class TestHandler(object):
    """
    This class is used in combination with a test sequence list to test the heater in the Amira instrument.
    """
    # class attribute type hints
    adc_counts_data: List[int]
    temperature_data: List[float]
    temperature_setpoint: int

    def __init__(self):
        """
        Class initializer.
        """
        self.allow_heater_data_collection = True
        self.adc_counts_data = []
        self.duty_cycle_data = []
        self.temperature_data = []
        self.temperature_setpoint = [30,50,40]#the three test values
        self.temperature_setpoint_index=0#keeps track of which value we are on

    def heater_debug_capture_event_parser(self, _test_step_index: int, event_code: AmiraEventCodes,
                                          _time_of_day: int, _time_str: str, _rtc_ticks: int,
                                          event_payload: dict) -> AmiraTestEventParserReturnValues:
        """
        This function is used to customize the parsing of heater debug data events.

        :param _test_step_index: Index of the currently executing test step.  Not used by this routine.
        :param event_code: Code of the event that has been received (i.e. AmiraEventCodes.app_fsm_door_open)
        :param _time_of_day: Unix timestamp of the event (i.e. 205296989).  Not used by this routine.
        :param _time_str: Time of day string (i.e. '07/04/76 02:56:29 AM').  Not used by this routine.
        :param _rtc_ticks: Running RTC tick count of the instrument with a 30.5 uS resolution (i.e. 347004915).
                           Not used by this routine,
        :param event_payload: JSON formatted payload (if any) of the event that has been received.  For the heater
                              debug event, there is additional data available to be used by this rouine.

        :return: Always AmiraTestEventParserReturnValues.ignore to instruct the scripting engine to continue to run.
        """
        global timer_done
        global timer_value
        global timer_start
        global t_high
        global t_low
        global t_stable
        temperature_reading=0
        
        ser=serial.Serial()
        ser.timeout = 0
        ser.port = "COM4" #Change to match the COM per computer
        ser.baudrate = '115200'
        ser.open()

        encoding = sys.getdefaultencoding()

        while True:
            if ser.inWaiting() >7:
                temp=ser.readline()
                temp = temp.decode(encoding)
                temp = temp.strip("b'\r\n'")
                temp=float(temp)
                temperature_reading=temp
                print(temperature_reading)
                if self.temperature_setpoint_index==0:#If the setpoint is 30
                    t_low=temperature_reading
                if self.temperature_setpoint_index==1:#If the setpoint is 50
                    t_high=temperature_reading
                if self.temperature_setpoint_index==2:#If the setpoint is 40
                    t_stable=temperature_reading    
                if timer_done == False and temperature_reading>39:#Time is only false when setpoint is 40 
                    timer_value=time.perf_counter()-timer_start#Record timer value when temperature hits 39 degrees
                    timer_done=True
                break

        if event_code == AmiraEventCodes.heater_debug_log and self.allow_heater_data_collection:
            
            # append the data sent in this event message
            if all([key in event_payload.keys() for key in ['adc-counts', 'duty-cycle-percent', 'temperature-c']]):
                self.adc_counts_data.append(event_payload['adc-counts'])
                self.duty_cycle_data.append(event_payload['duty-cycle-percent'])
                self.temperature_data.append(temperature_reading)

                log.msg('heater debug capture: ADC count: {0}, duty cycle: {1}, temperature: {2}'.format(
                        event_payload['adc-counts'], event_payload['duty-cycle-percent'],
                        temperature_reading), logLevel=logging.INFO)

        # return .ignore to instruct the test sequence state machine to proceed with the sequence
        return AmiraTestEventParserReturnValues.ignore

    def motor_movement_complete_event_parser(
            self, _test_step_index: int,
            event_code: AmiraEventCodes,
            _time_of_day: int, _time_str: str, _rtc_ticks: int,
            _event_payload: dict) -> AmiraTestEventParserReturnValues:
        """
        This function is used to customize the parsing of motor movement complete events.

        :param _test_step_index: Index of the currently executing test step. Not used by this routine.
        :param event_code: Code of the event that has been received.
        :param _time_of_day: Unix timestamp of the event (i.e. 205296989). Not used by this routine.
        :param _time_str: Time of day string (i.e. '07/04/76 02:56:29 AM'). Not used by this routine.
        :param _rtc_ticks: Running RTC tick count of the instrument with a 30.5 uS resolution (i.e. 347004915).
                          Not used by this routine.
        :param _event_payload: JSON formatted payload (if any) of the event that has been received.
                              Not used by this routine.
        :return: AmiraTestEventParserReturnValues.success if this routine has successfully parsed the event and the
                 test sequence should proceed to the next test step, AmiraTestEventParserReturnValues.failure if the
                 test sequence should be aborted, otherwise AmiraTestEventParserReturnValues.ignore.
        """
        if event_code == AmiraEventCodes.motor_fsm_move_complete:
            result = AmiraTestEventParserReturnValues.success
        elif event_code == AmiraEventCodes.motor_fsm_error:
            result = AmiraTestEventParserReturnValues.failure
        else:
            result = AmiraTestEventParserReturnValues.ignore
        return result

    def heater_run_test_step_on_exit(self, _test_step_index: int) -> bool:
        """
        This routine is called on the exit of a test step in which the heater has been running and debug data has
        been collected.

        :param _test_step_index: Current test step index of the test sequence.  Not used by this routine.
        :return: True if this routine has executed properly or False if there was an error.  If False is returned,
                 the entire script will fail with an AmiraTestInternalErrors.test_step_custom_on_exit_failure
                 event code.
        """
        self.allow_heater_data_collection = False
        global timer_value
        global error_string

        if self.temperature_setpoint_index==2 and self.temperature_data[len(self.temperature_data)-1]<30:#If no temperature is detected above 30 strip isnt inserted when setpoint is 40
            error_string=error_string+" CRITICAL ERROR STRIP NEVER INSERTED"
            print(error_string)

        if len(self.adc_counts_data):
            if self.temperature_setpoint_index==2:
                    passed=True
                    for i in range(len(self.temperature_data)-60+int(timer_value),len(self.temperature_data)-1):
                        if self.temperature_data[i]>41 or self.temperature_data[i]<39:#Confirms that the temperature stays withing 1 degrees of 40 degrees
                            error_string=error_string+'{0} FAILURE TO STABILIZE, '.format(self.temperature_setpoint[self.temperature_setpoint_index])
                            passed=False#Marked that it failed to stabilize
                            break
                    if passed:
                        error_string=error_string+'{0} Stabilized Correctly, '.format(self.temperature_setpoint[self.temperature_setpoint_index])
            elif self.temperature_setpoint_index==0 or self.temperature_setpoint_index==1: 
                    passed=True
                    for i in range(len(self.temperature_data)-20,len(self.temperature_data)-1):#Confirms temperature hasn't changed more than 2 degrees in 30 seconds
                        if abs(self.temperature_data[len(self.temperature_data)-1]-self.temperature_data[i])>2:
                            error_string=error_string+'{0} FAILURE TO STABILIZE, '.format(self.temperature_setpoint[self.temperature_setpoint_index])
                            passed=False#Marked that it failed to stabilize
                            break
                    if passed:
                        error_string=error_string+'{0} Stabilized Correctly, '.format(self.temperature_setpoint[self.temperature_setpoint_index])
      
            else:
                error_string=error_string+'{0} FAILURE TO STABILIZE, '.format(self.temperature_setpoint[self.temperature_setpoint_index])
            heater_csv_filename = '{0}  {1}.csv'.format(UUT,datetime.today().strftime('%Y-%m-%d_%H-%M-%S'))
            heater_plot_filename = '{0}  {1}.png'.format(UUT,datetime.today().strftime('%Y-%m-%d_%H-%M-%S'))

            # write all the data to a CSV file
            self.print_to_stdout('Saving data to .csv file ...')

            with open("heaterdata/"+heater_csv_filename, mode='w') as heater_data_file:
                heater_data_writer = csv.writer(heater_data_file, delimiter=',', quotechar='"',
                                                quoting=csv.QUOTE_MINIMAL)

                # write the fields header line
                heater_data_writer.writerow(['ADC Counts', 'Temperature (Deg.C)', 'Duty Cycle (Percent)'])

                num_data_points = len(self.adc_counts_data)
                index = 0
                while index < num_data_points:
                    # write the row of data
                    heater_data_writer.writerow([self.adc_counts_data[index], self.temperature_data[index],
                                                 self.duty_cycle_data[index]])
                    # increment the index
                    index += 1
                if self.temperature_setpoint_index == 2 and timer_done:
                    heater_data_writer.writerow(["Timer Value","Seconds",str(timer_value)])
            # create and save a plot of the data
            self.print_to_stdout('Plotting data ...')
            self.plot_heater_data("heaterdata/"+heater_plot_filename, self.adc_counts_data, self.temperature_data,
                                  self.duty_cycle_data)
            

        # return True to indicate that the routine executed properly with no errors
        return True

    def error_test_step_on_exit(self, _test_step_index: int) -> bool:
        """
        This routine is called on the exit of a test step in which the heater has been running and debug data has
        been collected.

        :param _test_step_index: Current test step index of the test sequence.  Not used by this routine.
        :return: True if this routine has executed properly or False if there was an error.  If False is returned,
                 the entire script will fail with an AmiraTestInternalErrors.test_step_custom_on_exit_failure
                 event code.
        """
        global timer_value
        global error_string
        print("\n" * 50)#Clears the screen
        if timer_value>20:#If it took longer than 20 seconds
            error_string=error_string+"{0} TIMER VALUE FAILED".format(timer_value)
        else:
            error_string=error_string+"{0} Timer Value Correct".format(timer_value)
        print(error_string)
        print("\n" * 5)
        # return True to indicate that the routine executed properly with no errors
        return True

    def ignore_already_initialized_response_parser(self, _test_step_index: int, _response_success: bool,
                                                   error_code: AmiraErrorCodes,
                                                   _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to the parsing of responses received for commands that might generate an already
        initialized error response which is ok to ignore.

        :param _test_step_index: Index of the currently executing test step (not used by this routine).
        :param _response_success: Success of the response parsing (not used by this routine).
        :param error_code: Error code of the response (AmiraErrorCodes.NRF_SUCCESS or AmiraErrorCodes.NRFX_SUCCESS if
                           the command was successful, otherwise another error code).
        :param _command_str: Sub-command portion of the command string (i.e. "app-info" for the full command
                            "mfg app-info").  Not used by this routine.
        :param _response_payload: JSON formatted response payload (i.e "{'productName': 'Amira', 'versionString':
                                 '0.16.1_d', 'appCodeSize': 1944122628, 'datastoreSize': 4194509569, 'gitTag':
                                 '0.16.1.b1f9665', 'gitData': '2021-05-24 14:47:51 -0400', 'gitSHA':
                                 '768c7705d0d4c5bcc4869a87f8075fca5486c06c'}" for the "mfg app-info" command.
                                 Not used by this routine.

        :return: True if the command was successfully parsed/approved by this routine, otherwise False.
                 If False is returned, the entire script will fail with an
                 AmiraTestInternalErrors.test_step_custom_response_parser_failure event code.
        """
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the optics has
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            self.allow_heater_data_collection = True
            return True
        else:
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            return False

    def plot_heater_data(self, plot_filename: str, adc_counts_data: List[int], temperature_data:List[float],
                         duty_cycle_data:List[int]) -> None:
        """
        This routine creates a plot with heater ADC counts and temperature data.  The temperature is plotted
        twice - an overall plot with all the data points and a second plot of the temperature after it's reached
        one percent of the setpoint.

        :param plot_filename: Name of plot file to save.
        :param adc_counts_data:  List with ADC data to plot.
        :param temperature_data: List with temperature data in degrees C to plot.
        :param duty_cycle_data: List with duty cycle data in percent plot.
        :return: None.
        """
        # determine the temperature data index value if any at which the temperature has stabilized
        stabilized_data_index_value = 0
        index = 0
        while index < len(temperature_data):
            # find the first data point that's within 3 percent of the setpoint
            if abs(temperature_data[index] - self.temperature_setpoint[self.temperature_setpoint_index]) <= self.temperature_setpoint[self.temperature_setpoint_index] * 0.03:
                stabilized_data_index_value = index
                break
            else:
                index += 1

        # create a plot with the heater ADC and temperature data all on individual subplots
        fig1, (ax1, ax2, ax3, ax4) = plt.subplots(figsize=(8, 11), nrows=4, sharex=True)
        x_axis_values = list(range(1, len(adc_counts_data) + 1))
        ax1.plot(x_axis_values, adc_counts_data)
        ax2.plot(x_axis_values, temperature_data)
        ax3.plot(x_axis_values[stabilized_data_index_value:], temperature_data[stabilized_data_index_value:])
        ax4.plot(x_axis_values, duty_cycle_data)
        ax1.set(ylabel='ADC Counts')
        ax2.set(ylabel='Temperature (Deg. C)')
        ax3.set(ylabel='Temperature - Stabilized (Deg. C)')
        ax4.set(xlabel='Sample Number', ylabel='Duty Cycle (Percent)')
        plot_title = 'Heater Data (Setpoint: {0} Deg C)'.format(self.temperature_setpoint[self.temperature_setpoint_index])
        fig1.suptitle(plot_title)
        fig1.savefig(plot_filename)

        self.adc_counts_data = []
        self.duty_cycle_data = []
        self.temperature_data = []
        self.temperature_setpoint_index+=1

    def print_to_stdout(self, output_message: str) -> None:
        """
        This routine outputs a message to the console/standard output if logging in the application is NOT enabled.
        This routine should be used for output that needs to occur when console logging is not enabled the application.

        :param output_message: Message to output.
        :return: None
        """
        # output the message in the format "AmiraTest: <time> <message>
        print('AmiraTest: {0} {1}'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], output_message))



    

    def start_heater_command_generator(self, _test_step_index: int) -> str:
        """
        This routine is the routine that is called to generate the command to start the heater.

        :param _test_step_index: Current test step index.  Not used by this routine.
        :return: String with command to send during the test step.
        """
        global timer_start
        global timer_done
        if self.temperature_setpoint_index == 2:#if the setpoint is 40 start the timer when the heater starts
            timer_start=time.perf_counter()
            timer_done=False
        
        return 'ins heater start {0}'.format(self.temperature_setpoint[self.temperature_setpoint_index])

    def set_heater_command_generator(self, _test_step_index: int) -> str:
        """
        This routine is the routine that is called to generate the command to start the heater.

        :param _test_step_index: Current test step index.  Not used by this routine.
        :return: String with command to send during the test step.
        """
        global timer_start
        global timer_done
        global t_low
        global t_high
        
        if self.temperature_setpoint_index==2:#This only entered if each of the two temperature values are alread recorded
            print('CALIBRATING HEATER')
            print('t_low')#Print out the values of the two recorded values
            print(t_low)
            print('t_high')
            print(t_high)
            #t_low+=0.5#Rounds each temperature to the nearest degree
            #t_high+=0.5
            return 'mfg htr-cal set {0} 1800 {1} 2800'.format(t_high,t_low)
        else:
            return 'mfg getwid'

    def start_heater_message_generator(self, _test_step_index: int) -> str:
        """
        This routine is the routine that is called to generate the message when the heater is started.

        :param _test_step_index: Current test step index.  Not used by this routine.
        :return: String with message to be logged/outputted when the heater is started.
        """
        return 'Starting heater (setpoint: {0} degrees C) ...'.format(self.temperature_setpoint[self.temperature_setpoint_index])#Start the heater to the correct setpoint

    

    def serial_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to customize the parsing of command responses received for the "ins optics init" message.

        :param _test_step_index: Index of the currently executing test step (not used by this routine).
        :param _response_success: Success of the response parsing (not used by this routine).
        :param error_code: Error code of the response (AmiraErrorCodes.NRF_SUCCESS or AmiraErrorCodes.NRFX_SUCCESS if
                           the command was successful, otherwise another error code).
        :param _command_str: Sub-command portion of the command string (i.e. "app-info" for the full command
                            "mfg app-info").  Not used by this routine.
        :param _response_payload: JSON formatted response payload (i.e "{'productName': 'Amira', 'versionString':
                                 '0.16.1_d', 'appCodeSize': 1944122628, 'datastoreSize': 4194509569, 'gitTag':
                                 '0.16.1.b1f9665', 'gitData': '2021-05-24 14:47:51 -0400', 'gitSHA':
                                 '768c7705d0d4c5bcc4869a87f8075fca5486c06c'}" for the "mfg app-info" command.
                                 Not used by this routine.

        :return: True if the command was successfully parsed/approved by this routine, otherwise False.  If False is
                 returned, the entire script will fail with an AmiraTestInternalErrors.test_step_custom_response_parser_failure
                 event code.
        """
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the optics has already been initialized
        
        # open the file in the write mode
        
        

        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            global UUT
            UUT=_response_payload['wirelessIdFull'] #capture the id of the amira
            return True
        else:
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            return False

    def version_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to customize the parsing of command responses received for the "ins optics init" message.

        :param _test_step_index: Index of the currently executing test step (not used by this routine).
        :param _response_success: Success of the response parsing (not used by this routine).
        :param error_code: Error code of the response (AmiraErrorCodes.NRF_SUCCESS or AmiraErrorCodes.NRFX_SUCCESS if
                           the command was successful, otherwise another error code).
        :param _command_str: Sub-command portion of the command string (i.e. "app-info" for the full command
                            "mfg app-info").  Not used by this routine.
        :param _response_payload: JSON formatted response payload (i.e "{'productName': 'Amira', 'versionString':
                                 '0.16.1_d', 'appCodeSize': 1944122628, 'datastoreSize': 4194509569, 'gitTag':
                                 '0.16.1.b1f9665', 'gitData': '2021-05-24 14:47:51 -0400', 'gitSHA':
                                 '768c7705d0d4c5bcc4869a87f8075fca5486c06c'}" for the "mfg app-info" command.
                                 Not used by this routine.

        :return: True if the command was successfully parsed/approved by this routine, otherwise False.  If False is
                 returned, the entire script will fail with an AmiraTestInternalErrors.test_step_custom_response_parser_failure
                 event code.
        """
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the optics has already been initialized
        
        # open the file in the write mode
        
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            global version
            version=_response_payload['versionString']#capture the version of the amira
            return True
        else:
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            return False

    def htrcal_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to customize the parsing of command responses received for the "ins optics init" message.

        :param _test_step_index: Index of the currently executing test step (not used by this routine).
        :param _response_success: Success of the response parsing (not used by this routine).
        :param error_code: Error code of the response (AmiraErrorCodes.NRF_SUCCESS or AmiraErrorCodes.NRFX_SUCCESS if
                           the command was successful, otherwise another error code).
        :param _command_str: Sub-command portion of the command string (i.e. "app-info" for the full command
                            "mfg app-info").  Not used by this routine.
        :param _response_payload: JSON formatted response payload (i.e "{'productName': 'Amira', 'versionString':
                                 '0.16.1_d', 'appCodeSize': 1944122628, 'datastoreSize': 4194509569, 'gitTag':
                                 '0.16.1.b1f9665', 'gitData': '2021-05-24 14:47:51 -0400', 'gitSHA':
                                 '768c7705d0d4c5bcc4869a87f8075fca5486c06c'}" for the "mfg app-info" command.
                                 Not used by this routine.

        :return: True if the command was successfully parsed/approved by this routine, otherwise False.  If False is
                 returned, the entire script will fail with an AmiraTestInternalErrors.test_step_custom_response_parser_failure
                 event code.
        """
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the optics has already been initialized
        
        # open the file in the write mode
        

        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            
            if round(t_high,2)==round(_response_payload['highTemp'],2) and round(t_low,2)==round(_response_payload['lowTemp'],2):#Compare our recorded values to the values the calibration returns
                print("Heater Calibration Values Set Correctly")
            else:
                print("high and low")#print out the values to help debug if set incorrectly
                print(float(t_high))
                print(float(t_low))
                print("Heater Calibration Values Set Incorrectly")
            print(_response_payload)
            f = open("heaterdata/calheater.csv", 'a', newline='')
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.now()
            myDict = {'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,"t-high":_response_payload['highTemp'],"c-high":_response_payload['adcHigh'],"t-low":_response_payload['lowTemp'],"c-low":_response_payload['adcLow'],"timer-value":timer_value,"stabilized":t_stable}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            return True
        else:
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            return False


# create an instance of the test handler
test_handler = TestHandler()
t_high=50#50 degree setpoint cal value
version=0#Holds the current firmware version of the device
UUT=0#Holds the device ID
t_low=30#30 degree setpoint cal calue
t_stable=0#Record the value that our setpoint of 40 stabilizes at
timer_start=0#Value of timer when it starts
timer_done=True#When false the program begins to track a timer
timer_value=80#Value of how long it takes to heat to 35 when calibrated to 40
error_string=""#This will contain all information generated and will be printed at the end of calibration

# create the csv writer
f = open("heaterdata/calheater.csv", 'a', newline='')
rowcount = 0
header=["UUT","FirmVersion","DateTimeStamp","t-high","c-high","t-low","c-low","timer-value","stabilized"]#csv header columns
#iterating through the whole file
for row in open("heaterdata/calheater.csv"):
    rowcount+= 1
if rowcount==0:#checks to see if this is the first test
    writer = csv.DictWriter(f, fieldnames = header)
    writer.writeheader()#if is first test write the header
writer = csv.DictWriter(f, fieldnames = header)
#writer.writerow({'UUT':' '})# This creates a space between the last test group and this test group
f.close()


"""
This is the list of test steps that the test tool will execute sequentially, one step at a time.

IMPORTANT: The name of this list must always be test_step_list and should never be changed!!!

Each test step is a Python dictionary with the type of action to be taken for the test step as well as some
additional information needed by the tool to execute the test step.

Potential dictionary keys for test steps in this list include:
    
'action': AmiraTestOperations: Test operation to execute. This is REQUIRED for every test step!
'command': str: Command to be sent in the test step.
'commandDelay': int: Time in seconds to wait after sending the raw command before proceeding to the next
                    test step.
'customCommandGenerator': Callable[[int], str]: Function to be called to generate the command to be sent
                          during the test step. The input to the routine is the integer test step index.  
                          The return value is the command string to be sent.  This dictionary entry can be 
                          used in place of defining 'command' if the value of 'command' needs to be determined 
                          dynamically during the user script execution. 
'customCommandDelayGenerator': Callable[[int], int]: Function to be called to generate the 'commandDelay' value
                               for the test step. The input to the routine is the integer test step index and the
                               return value is the integer 'commandDelay' value.  This dictionary entry can be
                               used in place of defining 'commandDelay' if the value of 'commandDelay' needs to
                               be determined dynamically during the user script execution. 
'customDiagnosticParser': Callable[[int, dict], None]: Routine to be called to parse JSON formatted diagnostic 
                          messages received from the instrument.  These messages are typically used to handle 
                          outputting of large amount of data such as test results or audit log messages or for 
                          certain types of informational log messages that needed for CI or other types of automated
                          testing. The input to the routine is the integer test step index and a dictionary with 
                          the JSON data received in the message.                              
'customEventParser': Callable[[int, AmiraEventCodes, int, str, int, dict], AmiraTestEventParserReturnValues]: 
                     Routine to be called to parse JSON events when an event is received during the test step.
'customLogParser': Callable[[int, AmiraLogEventTypes, str], bool]: Routine to be called to parse log messages
                   received during the test step.
'customMessageGenerator': Callable[[int], str]: Function to be called to generate the message to be outputted
                          to the log and standard output upon entry to the test step. The input to the routine 
                          is the integer test step index and the return value is a string of the generated 
                          message. This dictionary entry can be used in place of defining 'customStepDisplayMessage' 
                          if the value of 'customStepDisplayMessage' needs to be determined dynamically
                          during the user script execution.     
'customNumLoopsGenerator': Callable[[int], int]: Function to be called to generate the 'numLoops' value for the
                           test step.  The input to the routine is the integer test step index and the return 
                           value is an integer 'numLoops' value.  This dictionary entry can be used in place
                           of defining 'numLoops' if the value of 'numLoops' needs to be determined dynamically
                           during the user script execution.     
'customOnEntryHandler': Callable[[int], bool]: Routine to be called on initial entry into a test step before
                        the test step action occurs.  The input to the routine is the integer test step index. 
'customOnExitHandler': Callable[[int], bool]: Routine to be called on exit from a test step after all the
                       actions in the test step have occurred.
'customRegexMatchHandler': Callable[[int, re.Match, str], None]: Routine to be called when there is a regex match 
                           of a received line when using the 'regexPattern' pattern specified for the test step.
                           The input to the routine is the integer test step index, the generated regular expression 
                           match object, and the line of data (string) checked for a pattern match.
'customRepeatsGenerator': Callable[[int], int]: Function to be called to generate the 'repeats' value for the
                          test step. The input to the routine is the integer test step index and the return value
                          is the integer 'repeats' value.  This dictionary entry can be used in place of defining 
                          'repeats' if the value of 'repeats' needs to be determined dynamically during the user
                          script execution. 
'customResponseParser': Callable[[int, bool, AmiraErrorCodes, str, dict], bool]: Function to be called to
                        parse any command responses received while in the test step.
'customStepDisplayMessage': str: Message to be outputted to the log and the standard output upon entry to the
                            test step.
'customTimeoutGenerator': Callable[[int], int]: Function to be called to generate the timeout value for the
                          test step. The input to the routine is the integer test step index. The return value
                          is an integer 'timeout' value.
'customUserInputParser': Callable[[int, str], None]: Routine to call to parse input received during a
                         AmiraTestOperations.wait_for_user_input test step action.  
'numLoops': int: Number of loops to execute for a sequence of test steps enclosed within the 
            AmiraTestOperations.start_loop and AmiraTestOperations.end_loop actions. 
'regexPattern': str: Regular expression pattern to use to test lines of received data for a match.
'repeats': int: Number of times to send a command if the test step action is 
           AmiraTestOperations.send_repeat_command.
'testStepName': str: Name of the test step.  Can be used internally by user test scripts to help identify
                which test step is executing or just as the equivalent of a comment to help make the script
                more clear.  There is no requirement to have test steps named and the name is not otherwise 
                used in the test state machine as of present.    
'timeout': int: Timeout in seconds to wait for the test step action to completed.  Unless the test step action is
           AmiraTestOperations.delay, a timeout will result in the failure of the entire test sequence with
           a AmiraTestInternalErrors.timeout error code.  
"""
test_step_list = \
    [
        # ***************************************************************************
        # do some initial setup to allow the scripting tool to work more efficiently
        # ***************************************************************************

        # send the "cli echo off" command to disable the instrument from echoing back each command - this
        # command does not generate a JSON formatted response so use the .send_raw_command action instead
        # of .send_command - NOTE: if the instrument has been idle for a long time, it's possible that
        # it's gone into low power mode and disabled the serial interface so to be safe, send this message
        # twice - if the instrument has disabled the interface, the first message will be partially lost but
        # it will wake up the interface - sending the message twice is harmless and won't cause any problems
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo off', 'commandDelay': 1},
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo off', 'commandDelay': 1},

        # erase the current heater calibration to prepare the test
        {'action': AmiraTestOperations.send_command, 'command': 'mfg props-erase 3', 'timeout': 2},


         # wait 1 second
        {'action': AmiraTestOperations.delay, 'timeout': 1},

        # send the "mfg reset" command to reset the device - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_raw_command, 'command': 'mfg reset', 'commandDelay': 1,
 'customStepDisplayMessage': 'Resetting the device ...'},

        # wait up to 15 seconds for the instrument to reset and complete booting up
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_general_startup_complete,
         'timeout': 15, 'customStepDisplayMessage': 'Waiting for the device to restart ...'},
         
         # wait 5 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 5},

        # disable the application FSM to avoid any conflicts
        {'action': AmiraTestOperations.send_command, 'command': 'ins state event set-bypass-fsm', 'timeout': 50},

        #Get the serial number of the device
        {'action': AmiraTestOperations.send_command, 'command': 'mfg getwid', 'timeout': 20,
         'customResponseParser': test_handler.serial_response_parser},

         #Get the version of firmware on the device
        {'action': AmiraTestOperations.send_command, 'command': 'mfg app-info', 'timeout': 20,
         'customResponseParser': test_handler.version_response_parser},

         

        # **************************************
        # turn on the internal instrument power
        # **************************************

        # turn on the power to both rails
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 0 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 1 1', 'timeout': 2},

        {'action': AmiraTestOperations.send_command, 'command': 'ins motor move home', 'timeout': 2},#Make sure motor is in compressed position

        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.motor_fsm_move_complete,
         'customEventParser': test_handler.motor_movement_complete_event_parser,
         'customStepDisplayMessage': 'Waiting for motor home movement to complete ...', 'timeout': 30},

        # wait for user input
        {'action': AmiraTestOperations.wait_for_user_input,
         'customStepDisplayMessage': 'Insert the strip and hit enter ...'},

        {'action': AmiraTestOperations.start_loop, 'numLoops': 2}, #Loops to calculate t_low and t_high

        # enable heater debug output
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater debug enable', 'timeout': 2},

        # initialize the heater - ignore any already initialized errors
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater init', 'timeout': 2,
         'customResponseParser': test_handler.ignore_already_initialized_response_parser},

        # start the heater - the default setpoint value will be used unless the user entered a valid setpoint
        # value in the previous step
        {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': test_handler.start_heater_command_generator,
         'customMessageGenerator': test_handler.start_heater_message_generator,
         'testStepName': 'startHeater'},

        # run the heater for the time returned by calling test_handler.run_heater_timeout_generator,
        # collecting debug data
        {'action': AmiraTestOperations.delay,
         'customOnExitHandler': test_handler.heater_run_test_step_on_exit,
         'customEventParser': test_handler.heater_debug_capture_event_parser,
         'timeout': 60,
         'testStepName': 'runHeater'},

        # ***********************************
        # clean-up and shut everything down
        # ***********************************

        # stop data collection
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater debug disable', 'timeout': 2},

        # turn off the heater
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater stop', 'timeout': 2,
         'customStepDisplayMessage': 'Test complete - turning heater off ...'},

         # wait 2 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 2},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': test_handler.set_heater_command_generator},

         #Wait 30 seconds to cool heater
        {'action': AmiraTestOperations.delay, 'timeout': 30,
         'customStepDisplayMessage': 'Letting heater cool for 30 seconds...'},

        {'action': AmiraTestOperations.end_loop},

        # send the "mfg reset" command to reset the device - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_raw_command, 'command': 'mfg reset', 'commandDelay': 1,
 'customStepDisplayMessage': 'Resetting the device ...'},

        # wait up to 15 seconds for the instrument to reset and complete booting up
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_general_startup_complete,
         'timeout': 15, 'customStepDisplayMessage': 'Waiting for the device to restart ...'},
         
         # wait 5 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 5},


        # disable the application FSM to avoid any conflicts
        {'action': AmiraTestOperations.send_command, 'command': 'ins state event set-bypass-fsm', 'timeout': 5},

        # **************************************
        # turn on the internal instrument power
        # **************************************

        # turn on the power to both rails
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 0 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 1 1', 'timeout': 2},


        # enable heater debug output
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater debug enable', 'timeout': 2},

        # initialize the heater - ignore any already initialized errors
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater init', 'timeout': 2,
         'customResponseParser': test_handler.ignore_already_initialized_response_parser},

        # start the heater - the default setpoint value will be used unless the user entered a valid setpoint
        # value in the previous step
        {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': test_handler.start_heater_command_generator,
         'customMessageGenerator': test_handler.start_heater_message_generator,
         'testStepName': 'startHeater'},

        # run the heater for the time returned by calling test_handler.run_heater_timeout_generator,
        # collecting debug data
        {'action': AmiraTestOperations.delay,
         'customOnExitHandler': test_handler.heater_run_test_step_on_exit,
         'customEventParser': test_handler.heater_debug_capture_event_parser,
         'timeout': 80,
         'testStepName': 'runHeater'},

        # ***********************************
        # clean-up and shut everything down
        # ***********************************

        # stop data collection
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater debug disable', 'timeout': 2},

        # turn off the heater
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater stop', 'timeout': 2,
         'customStepDisplayMessage': 'Test complete - turning heater off ...'},

         # wait 2 seconds
        {'action': AmiraTestOperations.delay, 'customOnExitHandler': test_handler.error_test_step_on_exit, 'timeout': 1},

        # wait 2 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 2},

        {'action': AmiraTestOperations.send_command, 'command': 'mfg htr-cal get', 'timeout': 2,
         'customResponseParser': test_handler.htrcal_response_parser},

        # turn off the power to both rails
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 1 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 0 0', 'timeout': 2},

        # re-enable the application FSM so it will work normally again
        {'action': AmiraTestOperations.send_command, 'command': 'ins state event clear-bypass-fsm', 'timeout': 2},

        # send the "cli echo on" command - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo on'}
    ]