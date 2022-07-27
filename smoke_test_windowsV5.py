"""
Smoketest.py Rev 2 S-QMS-SPEC-33754
Bleak installed
This script runs both door init and fluidics init to prep instruments START WITH DOOR CLOSED

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

Version   AUTHOR    DATE        REASON FOR CHANGE
--------  --------    ----------------------------------
1            ZOO      09-22-21     Initial code.
2            ZOO      07/Apr/22    Sent to gas
3            ZOO      20/Apr/22    Sent to gas DCR-29217
4            ZOO      13/Apr/22    Add bluetooth functionality test
5            ZOO      13/May/22    Added scanning in the RFID and RFID tests
"""

import logging
from amira_parser import AmiraErrorCodes, AmiraEventCodes
from amira_test_state_machine import AmiraTestEventParserReturnValues, AmiraTestOperations
from twisted.python import log
from typing import List
import asyncio
from bleak import BleakScanner


import datetime
import csv


class InitDebugCapture(object):
    """
    This class is used in combination with a test sequence list to test the commands of fluidics init and door init
    """
    
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

    def motor_away_movement_complete_event_parser(
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
        global away_test
        global rowcount
        global test_result
        if event_code == AmiraEventCodes.motor_fsm_move_complete:
            result = AmiraTestEventParserReturnValues.success
            test_result='Fail'
            if away_test>1700 and away_test<2000: #Check to make sure motor is in right position This catches errors where motor doesn't move
                test_result='Pass'
            else:
                print('FAILURE: MOTOR POSITION ERROR')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Motor Away Movement', 'Units':'Position', 'LowerRangeValue':1700,'HigherRangeValue':2000,'MeasuredValue':away_test,'Result':test_result}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)  
            rowcount+=1
        elif event_code == AmiraEventCodes.motor_fsm_error:
            test_result='Fail'
            result = AmiraTestEventParserReturnValues.failure
            away_test=99999
            print('FAILURE: MOTOR POSITION ERROR')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Motor Away Movement', 'Units':'Position', 'LowerRangeValue':1700,'HigherRangeValue':2000,'MeasuredValue':'Error','Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)  
            rowcount+=1
        else:
            result = AmiraTestEventParserReturnValues.ignore
            away_test=_event_payload['position']
                
        return result

    def motor_home_movement_complete_event_parser(
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
        global home_test
        global rowcount
        global test_result
        if event_code == AmiraEventCodes.motor_fsm_move_complete:
            result = AmiraTestEventParserReturnValues.success
            test_result='Fail'
            if home_test>-500 and home_test<600: #Check to make sure motor is in right position This catches errors where motor doesn't move
                test_result='Pass'
            else:
                print('FAILURE: MOTOR POSITION ERROR')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Motor Home Movement', 'Units':'Position', 'LowerRangeValue':-500,'HigherRangeValue':600,'MeasuredValue':home_test,'Result':test_result}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            
        elif event_code == AmiraEventCodes.motor_fsm_error:
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            test_result='Fail'
            home_test=99999
            print('FAILURE: MOTOR POSITION ERROR')
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Motor Home Movement', 'Units':'Position', 'LowerRangeValue':-500,'HigherRangeValue':6000,'MeasuredValue':'Error','Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            result = AmiraTestEventParserReturnValues.failure
        else:            
            result = AmiraTestEventParserReturnValues.ignore
            home_test=_event_payload['position']
                
        return result

    
    def print_to_stdout(self, output_message: str) -> None:
        """
        This routine outputs a message to the console/standard output if logging in the application is NOT enabled.
        This routine should be used for output that needs to occur when console logging is not enabled the application.

        :param output_message: Message to output.
        :return: None
        """
        # output the message in the format "AmiraTest: <time> <message>
        print('AmiraTest: {0} {1}'.format(datetime.today().isoformat(), output_message))


    def logging_data_test_step_on_entry(self, test_step_index: int) -> bool:
        """
        This routine is called on the entry into a test step before any other code executes.

        This customization routine must be included in the test step for which it should execute by
        including the 'customOnExitHandler' dictionary item in the test step.

        :param test_step_index:  Current test step index of the test sequence.

        :return: True if this routine has executed properly or False if there was an error.  If False is returned,
                 the entire script will fail with an AmiraTestInternalErrors.test_step_custom_on_entry_failure
                 event code.
        """

        # note: use the Twisted library's logging call "log" instead of the standard Python loggging library
        # for proper sequencing of events
        log.msg('custom_test_step_on_entry() has executed - test step index {0}'.format(test_step_index),
                logLevel=logging.INFO)

        # return True to indicate that the routine executed properly with no errors
        return True

    def heater_init_response_parser(self, _test_step_index: int, _response_success: bool,
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
        global rowcount
        global test_result
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Heater', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_SUCCESS','Result':'Pass'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return True
        else:
            test_result='Fail'
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            print('FAILURE: HEATER DID NOT INITIALIZE')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Heater', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_FAILURE','Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return False

    def fluidics_init_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
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
        global rowcount
        global test_result
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Fluidics', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_SUCCESS','Result':'Pass'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return True
        else:
            test_result='Fail'
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            print('FAILURE: FLUIDICS DID NOT INITIALIZE')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Fluidics', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_FAILURE','Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return False

    def serial_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        
        global rowcount
        global test_result
        global bluetoothID

        async def run():
            global bluetoothID
            devices = await BleakScanner.discover()
            for d in devices:
                if 'Amira' in str(d):
                    bluetoothID=str(d)
                    #print(d)
                    break

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())

        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors
            global UUT
            UUT=_response_payload['wirelessIdFull'] #capture the id of the amira
            if UUT!=serial_val:
                print("Serial Values Set Incorrectly, Reinstall the firmware and try again")
                print(UUT)
                print(serial_val)
                return False
            else:
                print("RFID Set Correctly")
                            
            if str(UUT)[-3:]==str(bluetoothID)[-3:]:
                print("Bluetooth is functional")
            else:
                print("FAILURE BAD BLUETOOTH VALUES")
                test_result='Fail'

            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Bluetooth Test', 'Units':'Pass/Fail', 'MeasuredValue':str(bluetoothID),'Result':test_result}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
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
        
        global rowcount
        
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

    def door_init_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to customize the parsing of command responses received for the "ins door init" message.

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
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the door has already been initialized
        global rowcount
        global test_result
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors

            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Door', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_SUCCESS','Result':'Pass'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return True
        else:
            test_result='Fail'
            # return False indicating that there was a problem - note: this will end the execution of the entire
            # test script
            print('FAILURE: DOOR DID NOT INITIALIZE')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Door', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_FAILURE','Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return False

    def door_uninit_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
                                    _command_str: str, _response_payload: dict) -> bool:
        """
        This function is used to customize the parsing of command responses received for the "ins door uninit" message.

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
        # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the door has already been initialized
        global rowcount
        global test_result
        if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
            # return True to indicate that the response was parsed properly with no errors

            f = open("test_scripts/test.csv", 'a', newline='')
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'UnInitializing the Door', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_SUCCESS','Result':'Pass'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return True
        else:
            test_result='Fail'
            # return False indicating that there was a problem - note: this will end the execution of the entire
            print('FAILURE: DOOR FAILED TO UNINITIALIZE')
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'UnInitializing the Door', 'Units':'Pass/Fail', 'MeasuredValue':error_code,'Result':'Fail'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            return False


    def optics_init_response_parser(self, _test_step_index: int, _response_success: bool, error_code: AmiraErrorCodes,
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
            # allow the NRFX_ERROR_ALREADY_INITIALIZED error to occur which just means that the optics has
            global rowcount
            global test_result
            if error_code == AmiraErrorCodes.NRF_SUCCESS or error_code == AmiraErrorCodes.NRFX_SUCCESS or \
                    error_code == AmiraErrorCodes.NRFX_ERROR_ALREADY_INITIALIZED or \
                    error_code == AmiraErrorCodes.NRF_ERROR_MODULE_ALREADY_INITIALIZED:
                # return True to indicate that the response was parsed properly with no errors

                f = open("test_scripts/test.csv", 'a', newline='')
                writer = csv.DictWriter(f, fieldnames = header)
                time = datetime.datetime.now()
                myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Optics', 'Units':'Pass/Fail', 'MeasuredValue':'NRF_SUCCESS','Result':'Pass'}
                #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
                writer.writerow(myDict)
                rowcount+=1
                return True
            else:
                test_result='Fail'
                # return False indicating that there was a problem - note: this will end the execution of the entire
                print('FAILURE: OPTICS FAILED TO INITIALIZE')
                f = open("test_scripts/test.csv", 'a', newline='')
                # create the csv writer
                writer = csv.DictWriter(f, fieldnames = header)
                time = datetime.datetime.now()
                myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Initializing the Optics', 'Units':'Pass/Fail', 'MeasuredValue':'Error','Result':'Fail'}
                #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
                writer.writerow(myDict)
                rowcount+=1
                return False


    def custom_diagnostic_json_message_parser(self, test_step_index: int, json_payload: dict) -> None:
        """
        This function is used to customize the parsing of door open events.

        This customization routine must be included in each test step in which the door events are expected by
        including the 'customEventParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param json_payload: Dictionary with payload from diagnostic JSON message.
        :return: None.
        """
        
        
        log.msg('custom_diagnostic_json_message_parser(): test_step: {0}, payload: {1}'.format(
            test_step_index, json_payload), logLevel=logging.INFO)

    def custom_door_open_event_parser(self, test_step_index: int, event_code: AmiraEventCodes,
                                      time_of_day: int, time_str: str, rtc_ticks: int,
                                      event_payload: dict) -> AmiraTestEventParserReturnValues:
        """
        This function is used to customize the parsing of door open events.

        This customization routine must be included in each test step in which the door events are expected by
        including the 'customEventParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param event_code: Code of the event that has been received (i.e. AmiraEventCodes.app_fsm_door_open)
        :param time_of_day: Unix timestamp of the event (i.e. 205296989).
        :param time_str: Time of day string (i.e. '07/04/76 02:56:29 AM')
        :param rtc_ticks: Running RTC tick count of the instrument with a 30.5 uS resolution (i.e. 347004915)
        :param event_payload: JSON formatted payload (if any) of the event that has been received.  For the door-open
                              event, there is no additional payload.
        :return: AmiraTestEventParserReturnValues.success if this routine has successfully parsed the event and the
                 test sequence should proceed to the next test step, otherwise AmiraTestEventParserReturnValues.ignore.
        """
        # note: use the Twisted library's logging call "log" instead of the standard Python logging library
        # for proper sequencing of events
        result = AmiraTestEventParserReturnValues.ignore

        global rowcount

        if event_code == AmiraEventCodes.app_fsm_door_open: #If door open as been detected
            log.msg('custom_door_open_event_parser: the door has been opened successfully!', logLevel=logging.INFO)

            log.msg('custom_door_open_event_parser: test_step: {0}, event_code: {0}, tod: {1}, time_str: {2}, '
                    'rtc_ticks: {3}, payload: {4}'.format(test_step_index, event_code, time_of_day, time_str,
                                                          rtc_ticks, event_payload), logLevel=logging.INFO)
            
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            myDict = {'TestId':rowcount, 'UUT':UUT,'FirmVersion':version, 'DateTimeStamp':time,'Description':'Opening the Door', 'Units':'Pass/Fail', 'MeasuredValue':'app_fsm_door_open','Result':'Pass'}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1
            # indicate that the event was successfully parsed and the test sequence should proceed to the next
            # test step
            result = AmiraTestEventParserReturnValues.success
        else:
            # ignore the event
            result = AmiraTestEventParserReturnValues.ignore

        return result

    def custom_measure_single_event_parser(self, test_step_index: int, event_code: AmiraEventCodes,
                                      time_of_day: int, time_str: str, rtc_ticks: int,
                                      event_payload: dict) -> AmiraTestEventParserReturnValues:
        """
        This function is used to customize the parsing of door open events.

        This customization routine must be included in each test step in which the door events are expected by
        including the 'customEventParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param event_code: Code of the event that has been received (i.e. AmiraEventCodes.app_fsm_door_open)
        :param time_of_day: Unix timestamp of the event (i.e. 205296989).
        :param time_str: Time of day string (i.e. '07/04/76 02:56:29 AM')
        :param rtc_ticks: Running RTC tick count of the instrument with a 30.5 uS resolution (i.e. 347004915)
        :param event_payload: JSON formatted payload (if any) of the event that has been received.  For the door-open
                              event, there is no additional payload.
        :return: AmiraTestEventParserReturnValues.success if this routine has successfully parsed the event and the
                 test sequence should proceed to the next test step, otherwise AmiraTestEventParserReturnValues.ignore.
        """
        # note: use the Twisted library's logging call "log" instead of the standard Python logging library
        # for proper sequencing of events
        result = AmiraTestEventParserReturnValues.ignore
        global test_result
        global rowcount
        global ref_optics_test
        global main_optics_test
        if event_code == AmiraEventCodes.optics_measurement_complete:
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            test_result='Fail'
            
            main_optics_test=event_payload['main-pd']#Set Values for measure_half tests
            if event_payload['main-pd']<50000 and event_payload['main-pd']>1000:#Checks to make sure the values is a passsing value
                test_result='Pass'
            if test_result=='Fail':
                print('FAILURE: BAD MAIN PD OPTICS TEST')
            myDict = {'TestId':rowcount, 'UUT':UUT,'FirmVersion':version, 'DateTimeStamp':time,'Description':'Main PD Optics Measurement', 'Units':'Saturation', 'MeasuredValue':event_payload['main-pd'],'LowerRangeValue':1000,'HigherRangeValue':50000,'Result':test_result}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1

            result = AmiraTestEventParserReturnValues.success
        else:
            # ignore the event
            result = AmiraTestEventParserReturnValues.ignore

        return result

    def custom_measure_half_event_parser(self, test_step_index: int, event_code: AmiraEventCodes,
                                      time_of_day: int, time_str: str, rtc_ticks: int,
                                      event_payload: dict) -> AmiraTestEventParserReturnValues:
        """
        This function is used to customize the parsing of door open events.

        This customization routine must be included in each test step in which the door events are expected by
        including the 'customEventParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param event_code: Code of the event that has been received (i.e. AmiraEventCodes.app_fsm_door_open)
        :param time_of_day: Unix timestamp of the event (i.e. 205296989).
        :param time_str: Time of day string (i.e. '07/04/76 02:56:29 AM')
        :param rtc_ticks: Running RTC tick count of the instrument with a 30.5 uS resolution (i.e. 347004915)
        :param event_payload: JSON formatted payload (if any) of the event that has been received.  For the door-open
                              event, there is no additional payload.
        :return: AmiraTestEventParserReturnValues.success if this routine has successfully parsed the event and the
                 test sequence should proceed to the next test step, otherwise AmiraTestEventParserReturnValues.ignore.
        """
        # note: use the Twisted library's logging call "log" instead of the standard Python logging library
        # for proper sequencing of events
        result = AmiraTestEventParserReturnValues.ignore
        global test_result
        global rowcount
        test1='Fail'
        test2='Fail'
        if event_code == AmiraEventCodes.optics_measurement_complete:
            f = open("test_scripts/test.csv", 'a', newline='')
            # create the csv writer
            writer = csv.DictWriter(f, fieldnames = header)
            time = datetime.datetime.now()
            

            test_result='Fail'
            ratio=main_optics_test/(event_payload['main-pd']+.0001)
            if ratio>1.8:#Checks to make sure the values is a passsing value
                test1='Pass'
            else:
                test_result='Fail'
            if event_payload['main-pd']<25000 and event_payload['main-pd']>500:
                if test1=='Pass':                    
                    test_result='Pass'
                test2='Pass'
            else:
                test2='Fail'
            if test2=='Fail':
                print('FAILURE: BAD MAIN PD HALF OPTICS TEST')
            if test1=='Fail':
                print('FAILURE: BAD MAIN PD Ratio OPTICS TEST')
            myDict = {'TestId':rowcount, 'UUT':UUT,'FirmVersion':version, 'DateTimeStamp':time,'Description':'Half Power Main PD Optics Measurement', 'Units':'Saturation'.format(ratio), 'MeasuredValue':event_payload['main-pd'],'LowerRangeValue':500,'HigherRangeValue':25000,'Result':test2}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1

            myDict = {'TestId':rowcount, 'UUT':UUT,'FirmVersion':version, 'DateTimeStamp':time,'Description':'Half Power Ratio Measurement', 'Units':'Ratio', 'MeasuredValue':ratio,'LowerRangeValue':1.8,'HigherRangeValue':5.0,'Result':test1}
            #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
            writer.writerow(myDict)
            rowcount+=1

            result = AmiraTestEventParserReturnValues.success
        else:
            # ignore the event
            result = AmiraTestEventParserReturnValues.ignore

        return result

    def custom_light_user_input_parser(self, test_step_index: int, user_input: str) -> None:
        """
        This routine is called after the user has entered a string when prompted at the command line.

        This customization routine must be included in the test step for which it should execute by
        including the 'customUserInputParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param user_input:  User entered string.
        :return: None.
        """
        global test_result
        global rowcount
        test_result='Fail'
        if user_input=='y' or user_input=='Y':#Checks to see if the user says test passed
            test_result='Pass'
        f = open("test_scripts/test.csv", 'a', newline='')
        writer = csv.DictWriter(f, fieldnames = header)
        time = datetime.datetime.now()
        myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Manual LED Test', 'Units':'Pass/Fail','Result':test_result}
        #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
        writer.writerow(myDict)
        rowcount+=1
            

    def custom_strip_user_input_parser(self, test_step_index: int, user_input: str) -> None:
        """
        This routine is called after the user has entered a string when prompted at the command line.

        This customization routine must be included in the test step for which it should execute by
        including the 'customUserInputParser' dictionary item in the test step.

        :param test_step_index: Index of the currently executing test step.
        :param user_input:  User entered string.
        :return: None.
        """
        global rowcount
        global test_result
        test_result='Fail'
        if user_input=='y' or user_input=='Y':#If the user entered that it passed change result value
            test_result='Pass'
        f = open("test_scripts/test.csv", 'a', newline='')
        writer = csv.DictWriter(f, fieldnames = header)
        time = datetime.datetime.now()
        myDict = {'TestId':rowcount, 'UUT':UUT, 'FirmVersion':version, 'DateTimeStamp':time,'Description':'Manual Strip Tension Test', 'Units':'Pass/Fail','Result':test_result}
        #"Test Id", "UUT","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"
        writer.writerow(myDict)
        rowcount+=1

    def failure_lights_command_generator(self, _test_step_index: int) -> str:
        """
        This routine is the routine that is called to generate the command to start the heater.

        :param _test_step_index: Current test step index.  Not used by this routine.
        :return: String with command to send during the test step.
        """
        global test_result
        global test_failed
        if test_result == 'Fail' or test_failed:#This only entered if each of the two temperature values are alread recorded
            test_failed=True
            return 'ins ui-led setstate-all 1'
        else:
            return 'mfg getwid'#If not setting heater send dummy command

    def set_serial_command_generator(self, _test_step_index: int) -> str:
        """
        This routine is the routine that is called to generate the command to start the heater.

        :param _test_step_index: Current test step index.  Not used by this routine.
        :return: String with command to send during the test step.
        """
        global serial_val
        #print("hi")
        formatted_serial=serial_val[5:10]+serial_val[11:]
        #print(formatted_serial)
        return 'mfg setwid {0}'.format(formatted_serial)
        


serial_val='error'
serial_val = input("Scan in the serial number on the bottom of the device")
input("Insert the Amira into the docking station and hit enter")
#print(serial_val)

# create an instance of inits debug capture
inits_debug = InitDebugCapture()


# create the csv writer
f = open("test_scripts/test.csv", 'a', newline='')
rowcount = 0
header=["TestId", "UUT","FirmVersion","DateTimeStamp","Description","Units","MeasuredValue","LowerRangeValue","HigherRangeValue","Result"]#csv header columns
#iterating through the whole file
for row in open("test_scripts/test.csv"):
    rowcount+= 1
if rowcount==0:#checks to see if this is the first test
    writer = csv.DictWriter(f, fieldnames = header)
    writer.writeheader()#if is first test write the header
writer = csv.DictWriter(f, fieldnames = header)
writer.writerow({'Units':' '})# This creates a space between the last test group and this test group
f.close()
 

#Finds the current TestId
rowcount=1 #A placeholder for the number of rows in the file
with open('test_scripts/test.csv', newline='') as csvfile: #This finds the most recent test and sets the rowcount rows so that tests are numbered correctly
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['TestId']!='':#Make sure row is populated
            if int(row['TestId'])>=rowcount:#If value is larger than current testid set as current testid
                rowcount=int(row['TestId'])+1 #increment row number


bluetoothID='IDs'
UUT=0 #Placeholder for the ID of the unit
version=0 #Placeholder for the unit version
home_test=0 #Place holder for the motor's location in the home movement
test_result='Pass'
test_failed=False
ref_optics_test=0 #Placeholeder for the value recorded by the optics ref PD reading
main_optics_test=0 #Placeholeder for the value recorded by the optics main PD reading
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
customEventParser': Callable[[int, AmiraEventCodes, int, str, int, dict], AmiraTestEventParserReturnValues]: 
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
        # send the "cli echo off" command to disable the instrument from echoing back each command - this
        # command does not generate a JSON formatted response so use the .send_raw_command action instead
        # of .send_command - NOTE: if the instrument has been idle for a long time, it's possible that
        # it's gone into low power mode and disabled the serial interface so to be safe, send this message
        # twice - if the instrument has disabled the interface, the first message will be partially lost but
        # it will wake up the interface - sending the message twice is harmless and won't cause any problems
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo off', 'commandDelay': 1},
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo off', 'commandDelay': 1},

        
        # send the "mfg reset" command to reset the device - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_raw_command, 'command': 'mfg reset', 'commandDelay': 1,
 'customStepDisplayMessage': 'Resetting the device ...'},


        # wait up to 15 seconds for the instrument to reset and complete booting up
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_general_startup_complete,
         'timeout': 15, 'customStepDisplayMessage': 'Waiting for the device to restart ...'},

         # wait 6 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 6},
         
        {'action': AmiraTestOperations.send_command, 'timeout': 20,
         'customCommandGenerator': inits_debug.set_serial_command_generator},

         # wait 3 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 3},


        # disable the application FSM
        {'action': AmiraTestOperations.send_command, 'command': 'ins state event set-bypass-fsm', 'timeout': 20},

        # send the "mfg reset" command to reset the device - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_command, 'command': 'mfg app-info', 'timeout': 2,
         'customResponseParser': inits_debug.version_response_parser},

        # disable the application FSM
        {'action': AmiraTestOperations.send_command, 'command': 'ble radio-on', 'timeout': 20},
        
        # send the "mfg reset" command to reset the device - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_command, 'command': 'mfg getwid', 'timeout': 20,
         'customResponseParser': inits_debug.serial_response_parser},

        

        # turn on the power rails - these commands generate a JSON formatted response
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 0 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 1 1', 'timeout': 2},


        # waiting 5 seconds
        {'action': AmiraTestOperations.delay, 'timeout': 5,
         'customStepDisplayMessage': 'Watch the UI LEDs Turn White then Pink then Red then off...'},
         #Turns all Led's white
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 0 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 2 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 4 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 6 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 8 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 10 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 12 1', 'timeout': 2},

        # Delay to see light white
        {'action': AmiraTestOperations.delay, 'timeout': 3},
        #Turns all Led's pink
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 1 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 3 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 5 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 7 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 9 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 11 1', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 13 1', 'timeout': 2},

         # Delay to see light pink
        {'action': AmiraTestOperations.delay, 'timeout': 3},

        #Turns all Led's red by turning off white light
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 0 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 2 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 4 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 6 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 8 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 10 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 12 0', 'timeout': 2},

        # Delay to see light red
        {'action': AmiraTestOperations.delay, 'timeout': 3},

        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 1 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 3 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 5 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 7 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 9 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 11 0', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins ui-led setstate 13 0', 'timeout': 2},

        # wait for user input
        {'action': AmiraTestOperations.wait_for_user_input,
         'customStepDisplayMessage': 'Did the LEDs turn on and off properly? y=yes n=no ...',
         'customUserInputParser': inits_debug.custom_light_user_input_parser},
         
         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

        # enable heater debug output
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater debug enable', 'timeout': 2},

        # initialize the heater - ignore any already initialized errors
        {'action': AmiraTestOperations.send_command, 'command': 'ins heater init', 'timeout': 2,
         'customResponseParser': inits_debug.heater_init_response_parser,
         'customStepDisplayMessage': 'Initializing heater ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

        # setup the optics to output ADC counts to the console in JSON formatted events
        {'action': AmiraTestOperations.send_command, 'command': 'ins fluidics init',
         'timeout': 20, 'customResponseParser': inits_debug.fluidics_init_response_parser,
         'customStepDisplayMessage': 'Initializing fluidics ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         # setup the door to begin sending state data
	    {'action': AmiraTestOperations.send_command, 'command': 'ins door init',
         'timeout': 20, 'customResponseParser': inits_debug.door_init_response_parser,
         'customStepDisplayMessage': 'Initializing door ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

        # report the state of the door
        {'action': AmiraTestOperations.send_command, 'command': 'ins door get-state', 'timeout': 2
         },

        # wait up to 20 seconds for the door to be opened
        # if a door event is received, call the custom event handler custom_door_open_event_parser()
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_fsm_door_open,
         'customEventParser': inits_debug.custom_door_open_event_parser, 'timeout': 200,
         'customStepDisplayMessage': 'Open the Door ...'},

         # report the state of the door
        {'action': AmiraTestOperations.send_command, 'command': 'ins door get-state', 'timeout': 2},

         # stop monitoring the state of the door
	    {'action': AmiraTestOperations.send_command, 'command': 'ins door uninit',
         'timeout': 2, 'customResponseParser': inits_debug.door_uninit_response_parser},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         #Move motor test
        #{'action': AmiraTestOperations.send_command, 'command': 'ins motor mode idle', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins motor moveto 1740', 
         'customStepDisplayMessage': 'Waiting for motor away movement to complete ...','timeout': 20},
        

         # wait for user input
        {'action': AmiraTestOperations.wait_for_user_input,
         'customStepDisplayMessage': 'Insert the Strip and Hit enter'},

        {'action': AmiraTestOperations.send_command, 'command': 'ins motor config home', 'timeout': 2},
        {'action': AmiraTestOperations.send_command, 'command': 'ins motor move', 'timeout': 2},
        # wait for the motor home movement to complete
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.motor_fsm_move_complete,
         'customEventParser': inits_debug.motor_home_movement_complete_event_parser,
         'customStepDisplayMessage': 'Waiting for motor home movement to complete ...', 'timeout': 30},

          {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         # wait for user input
        {'action': AmiraTestOperations.wait_for_user_input,
         'customStepDisplayMessage': 'Lightly pull the strip. Did the strip have tension when attempting to pull it? y=yes n=no ...',
         'customUserInputParser': inits_debug.custom_strip_user_input_parser},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         {'action': AmiraTestOperations.send_command, 'command': 'ins motor moveto 1740', 'customStepDisplayMessage': 'Waiting for motor away movement to complete ...', 'timeout': 20},
        #{'action': AmiraTestOperations.send_command, 'command': 'ins motor config decompress', 'timeout': 2},
        #{'action': AmiraTestOperations.send_command, 'command': 'ins motor move', 'timeout': 2},
        # wait for the motor away movement to complete
        #{'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.motor_fsm_move_complete,
         #'customEventParser': inits_debug.motor_away_movement_complete_event_parser,
         #'customStepDisplayMessage': 'Waiting for motor away movement to complete ...', 'timeout': 30},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         # wait for user input
        {'action': AmiraTestOperations.wait_for_user_input,
         'customStepDisplayMessage': 'Remove the Strip, Close the door, and Hit enter'},


         #Initilize optics
         {'action': AmiraTestOperations.send_command, 'command': 'ins optics init', 'timeout': 4, 
          'customResponseParser': inits_debug.optics_init_response_parser,
         'customStepDisplayMessage': 'Initializing optics ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         #Set optics full power
         #{'action': AmiraTestOperations.send_command, 'command': 'ins optics reg write 22 303F', 'timeout': 4},
         #{'action': AmiraTestOperations.send_command, 'command': 'ins optics reg write 25 F800', 'timeout': 4},

         {'action': AmiraTestOperations.send_command, 'command': 'ins optics led-current set 3 15 31', 'timeout': 4},

         #Take an optics measurement
         {'action': AmiraTestOperations.send_command, 'command': 'ins optics measure single', 'timeout': 4},

         # wait up to 20 seconds for the measurement
        # if a measurement is received, call the custom event handler 
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_fsm_measurement_complete,
         'customEventParser': inits_debug.custom_measure_single_event_parser, 'timeout': 20,
         'customStepDisplayMessage': 'Reading measurement ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

         #Set optics half power
         #{'action': AmiraTestOperations.send_command, 'command': 'ins optics reg write 22 3038', 'timeout': 4},
         #{'action': AmiraTestOperations.send_command, 'command': 'ins optics reg write 25 A000', 'timeout': 4},

         {'action': AmiraTestOperations.send_command, 'command': 'ins optics reg write 22 3034', 'timeout': 4},

         #Take an optics measurement at half power
         {'action': AmiraTestOperations.send_command, 'command': 'ins optics measure single', 'timeout': 4},

         # if a measurement is received, call the custom event handler 
        {'action': AmiraTestOperations.wait_for_event, 'event': AmiraEventCodes.app_fsm_measurement_complete,
         'customEventParser': inits_debug.custom_measure_half_event_parser, 'timeout': 20,
         'customStepDisplayMessage': 'Reading second measurement ...'},

         {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

        #UnInitilize optics
         {'action': AmiraTestOperations.send_command, 'command': 'ins optics uninit', 'timeout': 4},

         #UnInitilize optics
         {'action': AmiraTestOperations.send_command, 'command': 'ins fluidics uninit', 'timeout': 4},

         
         # re-enable the application FSM so it will work normally again
        {'action': AmiraTestOperations.send_command, 'command': 'ins state event clear-bypass-fsm', 'timeout': 2},

        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 0 1', 'timeout': 2},#Allow LED error lights to turn on
        {'action': AmiraTestOperations.send_command, 'command': 'ins pwr 1 1', 'timeout': 2},

        {'action': AmiraTestOperations.send_command, 'timeout': 2,
         'customCommandGenerator': inits_debug.failure_lights_command_generator},

        # send the "cli echo on" command - this command does not generate a JSON formatted response
        {'action': AmiraTestOperations.send_raw_command, 'command': 'cli echo on'}
    ]


