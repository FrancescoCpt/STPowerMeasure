'''
Created on 2 ago 2023

@author: caputofr
'''

from NucleoPowerMonitorV3 import NucleoPowerMonitor, TEMP_CELSIUS,\
    ACQMODE_STATIC, TRIGGER_SOURCE_HW, POWER_TARGET_ON, TRIGGER_SOURCE_SW,\
    ACQMODE_DYNAMIC, OUTPUT_FORMAT_ASCII
import time
from matplotlib import pyplot as plt

pm = NucleoPowerMonitor("COM29", baudrate=115200)
pm.openConnectionToDevice()

res = pm.getInfo()
print(res)

res = pm.getVersion()
print(res)

res = pm.getAPIVersion()
print(res)

res = pm.gerRange()
print(res)

res = pm.getStatus()
print(res)

#pm.setUserControlledMode(True)


#pm.setAcquisitionMode(ACQMODE_DYNAMIC)
pm.setAcquisitionTime(5)
pm.setVoltage(3300)
pm.setOutputFormat(output_format=OUTPUT_FORMAT_ASCII)
pm.setTriggerSource(TRIGGER_SOURCE_HW)
pm.setFrequency(10000) # UPPER BOUND!!!

res = pm.getTemperature(TEMP_CELSIUS, False)
print(res)

time.sleep(2)

samples = []

pm.startAcquisition()
print("start")

while(not pm.isAcquisitionEnded()):
    #pm.startAcquisition()
    samp = pm.readSampleFromDevice()
    if(samp != None):
        samples.append(samp)

#pm.setUserControlledMode(False)

pm.closeConnectionToDevice()

# Find end of inference ==============
upper_sample = 0
upper_sample_idx = 0
lower_sample_idx = 0
treshold_val = (max(samples) - min(samples)) * 0.5
for sample_idx in range(len(samples)):
    if (samples[sample_idx] > upper_sample):
        upper_sample = samples[sample_idx]
        upper_sample_idx = sample_idx
    else:
        dif_samp = upper_sample - samples[sample_idx]
        if(dif_samp > treshold_val):
            lower_sample_idx = sample_idx
            break

# Cut the edge
while(samples[lower_sample_idx] < samples[lower_sample_idx-1]):
    lower_sample_idx -= 1
samples = samples[:lower_sample_idx]
# =====================================

plt.plot(range(len(samples)), samples)
plt.show()