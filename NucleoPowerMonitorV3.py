'''
Created on 15 set 2023

@author: caputofr
'''

import serial
import time
import re
import math

TEMP_CELSIUS = "degc"
TEMP_FARENIGHT = "degf"

ACQMODE_DYNAMIC = "dyn"
ACQMODE_STATIC = "stat"

FUNCMODE_OPTIMIZED = "optim"
FUNCMODE_HIGH_CURRENT = "high"

OUTPUT_TYPE_ENERGY = "energy"
OUTPUT_TYPE_CURRENT = "current"

OUTPUT_FORMAT_ASCII = "ascii_dec"
OUTPUT_FORMAT_HEX = "bin_hexa"

OUTPUT_SIGNAL_VOUT = "vout"
OUTPUT_SIGNAL_VAUX = "vaux"

OUTPUT_PWR_MODE_AUTO = "auto"
OUTPUT_PWR_MODE_ON = "on"
OUTPUT_PWR_MODE_OFF = "off"
OUTPUT_PWR_MODE_NOSTATUS = "nostatus"
OUTPUT_PWR_MODE_STATUS = "status"

POWER_TARGET_ON = "on"
POWER_TARGET_OFF = "off"

TRIGGER_SOURCE_HW = "hw"
TRIGGER_SOURCE_SW = "sw"

class NucleoPowerMonitor():
    ser = None
    ser_port = None
    ser_port_baudrate = None
    on_meas = False
    
    def __init__(self, serial_port=None, baudrate=3686400):
        
        if(serial_port == None):
            print("Error in serial port configuration")
            return
        
        self.ser_port = serial_port
        self.ser_port_baudrate = baudrate
        
    def openConnectionToDevice(self):
        if(self.ser != None or self.ser_port == None):
            print("ERROR: Something Wrong")
            return
        
        self.ser = serial.Serial(
            port        = self.ser_port,
            baudrate    = self.ser_port_baudrate,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS
        )
        
        self.ser.isOpen()
        
    def closeConnectionToDevice(self):
        self.ser.close()
        self.ser = None
    
    def __writeOnDevice(self, command):
        send_str = command + '\r\n'
        self.ser.write(send_str.encode())
        
    def __readFromDevice(self):
        res_str = ""
        while(res_str == ""):
            if(self.ser.inWaiting() > 0):
                line = self.ser.readline()
                if("ack" in line.decode()):
                    res_str += line.decode()
            time.sleep(0.1)
            
        res_str = res_str.replace("ack ", "")
        res_str = res_str.replace("stlp >","")
        res_str = res_str.strip()
        return res_str
    
    def readSampleFromDevice(self):
        rex = re.compile("^[0-9]{4}-[0-9]{2}") # find string of type "NNNN-NN", where N is a number
        res_str = ""
        while(res_str == ""):
            if(self.ser.inWaiting() > 0):
                line = self.ser.readline()
                line_str = line.decode()
                if("end" in line_str):
                    self.on_meas = False
                    return None
                
                line_str = line_str.strip()
                line_str = line_str.strip("\x00")
                if rex.match(line_str.strip()):
                    res_str += line_str
        
        values = res_str.split("-")
        sample = 0
        if(int(values[0]) > 0):
            sample = int(values[0]) * math.pow(10, (-1*int(values[1])))
            
        return sample
    
    def isAcquisitionEnded(self):
        return (not self.on_meas)
    
    def setUserControlledMode(self, value=True):
        if(value):
            self.__writeOnDevice("htc")
        else:
            self.__writeOnDevice("hrc")
        self.__readFromDevice()
            
    def getHelp(self):
        self.__writeOnDevice("help")
        return self.__readFromDevice()
    
    def getInfo(self):
        self.__writeOnDevice("powershield")
        return self.__readFromDevice()
    
    def getVersion(self):
        self.__writeOnDevice("version")
        version_str = self.__readFromDevice()
        return version_str.replace("version: ","")

    def getAPIVersion(self):
        self.__writeOnDevice("apiver")
        api_ver_res = self.__readFromDevice()
        api_ver_res = api_ver_res.replace("apiver: ", "")
        return api_ver_res
    
    # Get measure range [A]
    def gerRange(self):
        self.__writeOnDevice("range")
        ranges_res = self.__readFromDevice()
        ranges_res =ranges_res.replace("range ","")
        return [float(range_val.replace("-","E-")) for range_val in ranges_res.split(" ")]
    
    def getStatus(self):
        self.__writeOnDevice("status")
        status_res = self.__readFromDevice()
        return status_res.replace("status ", "")
                
    def hardwareReset(self):
        self.__writeOnDevice("psrst")
        self.__readFromDevice()
        
    def targetReset(self, time_s=1):
        self.__writeOnDevice(f"targrst {time_s}")
        self.__readFromDevice()
        
    def performAutoTest(self):
        self.__writeOnDevice(f"autotest")
        self.__readFromDevice()
        
    def performAutoCalibration(self):
        self.__writeOnDevice(f"calib")
        self.__readFromDevice()
        
    def getTemperature(self, t_type=TEMP_CELSIUS, refresh=False):
        if(refresh):
            self.__writeOnDevice(f"temp {t_type} refresh")
        else:
            self.__writeOnDevice(f"temp {t_type}")
        
        temp_res = self.__readFromDevice()
        temp_res = temp_res.replace("temp degc ","")
        
        if(refresh):
            temp_res = temp_res.replace("refresh ","")
            
        return float(temp_res)
    
    def startAcquisition(self):
        self.__writeOnDevice(f"start")
        self.__readFromDevice()
        self.on_meas = True
        
    def stopAcquisition(self):
        self.__writeOnDevice(f"stop")
        self.__readFromDevice()
        self.on_meas = False
        
    def setVoltage(self, voltage=0, output=None):
        if(output==None or not(output in [OUTPUT_SIGNAL_VOUT, OUTPUT_SIGNAL_VAUX])):
            self.__writeOnDevice(f"volt {voltage}m")
        else:
            self.__writeOnDevice(f"volt {output} {voltage}m")
        self.__readFromDevice()
        
    def getVoltage(self):
        self.__writeOnDevice(f"volt get")
        return self.__readFromDevice()
    
    def setFrequency(self, freq=0):
        self.__writeOnDevice(f"freq {freq}")
        self.__readFromDevice()
    
    def setAcquisitionTime(self, acqtime=0):
        self.__writeOnDevice(f"acqtime {acqtime}")
        self.__readFromDevice()
        
    def setFunctionMode(self, funcmode=FUNCMODE_OPTIMIZED):
        self.__writeOnDevice(f"funcmode {funcmode}")
        self.__readFromDevice()
        
    def setOutputType(self, output_type=OUTPUT_TYPE_CURRENT):
        self.__writeOnDevice(f"output {output_type}")
        self.__readFromDevice()
    
    def setOutputFormat(self, output_format=OUTPUT_FORMAT_ASCII):
        self.__writeOnDevice(f"format {output_format}")
        self.__readFromDevice()
        
    def setTriggerSource(self, trigsrc=TRIGGER_SOURCE_SW):
        self.__writeOnDevice(f"trigsrc {trigsrc}")
        self.__readFromDevice()
    
    def setTriggerDelay(self, trigdelay=0):
        self.__writeOnDevice(f"trigdelay {trigdelay}")
        self.__readFromDevice()
        
    def setCurrentThreshold(self, currthres=0):
        self.__writeOnDevice(f"currthres {currthres}")
        self.__readFromDevice()
        
    def setPowerTargetMode(self, pwr=OUTPUT_PWR_MODE_AUTO, pwr_signal=None, pwr_status=None):
        if(pwr_signal==None and pwr_status==None):
            self.__writeOnDevice(f"pwr {pwr}")
        else:
            pwr_signal_str = (f"{pwr_signal} ") if (pwr_signal != None) else ""
            pwr_status_str = (f"{pwr_status} ") if (pwr_status != None) else ""
            self.__writeOnDevice(f"pwr {pwr_signal_str}{pwr}{pwr_status_str}")
            
        self.__readFromDevice()
        
    def setPowerTargetEnd(self, pwrend=POWER_TARGET_OFF):
        self.__writeOnDevice(f"pwrend {pwrend}")
        self.__readFromDevice()   