import os
import datetime
import math
import re

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks

class ParState:
    OK = 0
    NOPAR = 1
    DATAEMPTY = 2
    FAIL = 3

class ParFileNameType:
    NONE = 0
    PBS = 1
    GLUCOSE = 2
    VOLTAGE = 3
    

# TODO:
class ParMode:
    CV = 0
    # ..
#

class ParReader:
    def __init__(self, filepath):
        if os.path.basename(filepath)[-3:].lower() != "par":
            self.status = ParState.NOPAR
            return    
        
        self.filepath = filepath
        self.filename = os.path.basename(filepath)[:-4]
        if "PBS" in self.filename:
            self.filetype = ParFileNameType.PBS
        elif "V" in self.filename:
            self.filetype = ParFileNameType.VOLTAGE
        else:
            try:
                int(self.filename)
                self.filetype = ParFileNameType.GLUCOSE
            except:
                self.filetype = ParFileNameType.NONE
        
        self.read_data(filepath)
        if self.status == ParState.OK:
            self.analysis_all()
        self.select_segment = 2
        
    def read_data(self, filepath):

        with open(filepath, 'r', encoding='utf-8') as f:
            data = f.read()
        if data is None:
            self.status = ParState.FAIL
            return
        
        pattern = r"<(\w+)>\s*(.*?)\s*</\1>"
        matches = re.findall(pattern, data, re.DOTALL)
        self.content = {match[0]: match[1].strip() for match in matches}
        if len(self.content) == 0:
            self.status = ParState.FAIL
            return
        
        segmentData = self.content.get("Segment1").split("\n")
        
        if segmentData is None or len(segmentData) < 4:
            self.status = ParState.DATAEMPTY
            return
                    
        segments = []
        voltages = []
        currents = []
        
        for data in segmentData[4:]:
            splitdata = data.split(",")
            status = int(splitdata[7])
            skip = self.check_status(status)
            if skip: continue
            
            segment = int(splitdata[0])
            voltage = float(splitdata[2])
            current = float(splitdata[3])
            
            segments.append(segment)
            voltages.append(voltage)
            currents.append(current)
        
        self.max_segment = max(segments) + 1

        counts = []
        for s in range(self.max_segment):
            counts.append(segments.count(s))
        
        self.voltages = [[] for _ in range(self.max_segment)]
        self.currents = [[] for _ in range(self.max_segment)]
    
        i = 0
        for s in range(self.max_segment):
            self.voltages[s] = voltages[i:counts[s] + i]
            self.currents[s] = currents[i:counts[s] + i]
            i += counts[s]
            
        self.status = ParState.OK
    
    def analysis_all(self):
        
        self.firstHalfVoltagesAll = [[] for _ in range(self.max_segment)]
        self.firstHalfCurrentsAll = [[] for _ in range(self.max_segment)]
        self.secondHalfVoltagesAll = [[] for _ in range(self.max_segment)]
        self.secondHalfCurrentsAll = [[] for _ in range(self.max_segment)]
        self.logScaleCurrentsAll = [[] for _ in range(self.max_segment)]
        self.cathodicVoltagesAll = [[] for _ in range(self.max_segment)]
        self.cathodicCurrentsAll = [[] for _ in range(self.max_segment)]
        self.anodicVoltagesAll = [[] for _ in range(self.max_segment)]
        self.anodicCurrentsAll = [[] for _ in range(self.max_segment)]
        self.peaksAll = [[] for _ in range(self.max_segment)]
        
        for segment in range(self.max_segment):
            self.analysis(segment)
        
    def analysis(self, segment):
        
        voltages = self.voltages[segment]
        currents = self.currents[segment]
        
        ## Get voltage min max
        voltageMaxIdx = voltages.index(max(voltages))
        voltageMinIdx = voltages.index(min(voltages))
        
        ## Split half
        firstHalfVoltages = self.firstHalfVoltagesAll[segment]
        firstHalfCurrents = self.firstHalfCurrentsAll[segment]
        secondHalfVoltages = self.secondHalfVoltagesAll[segment]
        secondHalfCurrents = self.secondHalfCurrentsAll[segment]

        if voltageMaxIdx < voltageMinIdx:
            firstHalfVoltages.extend(voltages[voltageMaxIdx:voltageMinIdx])
            firstHalfCurrents.extend(currents[voltageMaxIdx:voltageMinIdx])
            secondHalfVoltages.extend(voltages[voltageMinIdx:])
            secondHalfCurrents.extend(currents[voltageMinIdx:])
        else:
            firstHalfVoltages.extend(voltages[:voltageMinIdx])
            firstHalfCurrents.extend(currents[:voltageMinIdx])
            secondHalfVoltages.extend(voltages[voltageMinIdx:voltageMaxIdx])
            secondHalfCurrents.extend(currents[voltageMinIdx:voltageMaxIdx])
        
        
        ## Get peaks
        peaks = self.peaksAll[segment]
        
        if len(firstHalfCurrents) == 0:
            peaks.append((-1, -1, -1))
        else:
            firstpeaks, _ = find_peaks(-np.float32(firstHalfCurrents), width=10)
            if len(firstpeaks) == 0:
                peaks.append((-1, -1, -1))
            else:
                peaks.append((firstpeaks[0], firstHalfVoltages[firstpeaks[0]], firstHalfCurrents[firstpeaks[0]]))
            
        if len(secondHalfCurrents) == 0:
            peaks.append((-1, -1, -1))
        else:
            secondpeaks, _ = find_peaks(np.float32(secondHalfCurrents), width=10)
            if len(secondpeaks) == 0:
                peaks.append((-1, -1, -1))
            else:
                peaks.append((secondpeaks[0], secondHalfVoltages[secondpeaks[0]], secondHalfCurrents[secondpeaks[0]]))
                
        ## Logscale (only second half)
        logScaleCurrent = self.logScaleCurrentsAll[segment]
        if len(secondHalfCurrents) == 0:
            return
        
        logScaleCurrent.extend(list(map(lambda x : math.log10(abs(x * (10**3))), secondHalfCurrents)))
        
        ## Split cathodic anodic
        # get min max idx
        tafelMinCurrentIdx = logScaleCurrent.index(min(logScaleCurrent))
        tafelMaxCurrentIdx = logScaleCurrent.index(max(logScaleCurrent))
        
        # cathodic
        cathodicVoltages = self.cathodicVoltagesAll[segment]
        cathodicCurrents = self.cathodicCurrentsAll[segment]
        # anodic
        anodicVoltages = self.anodicVoltagesAll[segment]
        anodicCurrents = self.anodicCurrentsAll[segment]
        
        cathodicVoltages.extend(secondHalfVoltages[:tafelMinCurrentIdx])
        cathodicCurrents.extend(logScaleCurrent[:tafelMinCurrentIdx])
        anodicVoltages.extend(secondHalfVoltages[tafelMinCurrentIdx:tafelMaxCurrentIdx])
        anodicCurrents.extend(logScaleCurrent[tafelMinCurrentIdx:tafelMaxCurrentIdx])
    
    def save(self, savepath):
        dirpath = os.path.join(savepath, self.filename)
        os.makedirs(dirpath, exist_ok=True)
        
        for segment in range(self.max_segment):
            segmentpath = os.path.join(dirpath, f"segement_{segment}")
            os.makedirs(segmentpath, exist_ok=True)
            
            plt.figure()
            plt.title(f"{self.filename}, Segment # {segment}", fontsize=10, fontweight='bold')
            plt.plot(self.voltages[segment], self.currents[segment])
            plt.savefig(os.path.join(segmentpath, f"Segement_{segment}.png"))
            plt.close()
            
            plt.figure()
            plt.title(f"{self.filename}, Segment # {segment}, Split Half", fontsize=10, fontweight='bold')
            plt.plot(self.firstHalfVoltagesAll[segment], self.firstHalfCurrentsAll[segment], color='b')
            plt.plot(self.secondHalfVoltagesAll[segment], self.secondHalfCurrentsAll[segment], color='r')
            plt.savefig(os.path.join(segmentpath, f"Segment_{segment}_splithalf.png"))
            plt.close()
            
            plt.figure()
            plt.title(f"{self.filename}, Segment # {segment}, Peaks", fontsize=10, fontweight='bold')
            if self.peaksAll[segment][0][0] != -1:
                plt.scatter(self.peaksAll[segment][0][1], self.peaksAll[segment][0][2], s=40, color='b', label=f"V : {self.peaksAll[segment][0][1]}, I : {self.peaksAll[segment][0][2]}")
            if self.peaksAll[segment][1][0] != -1:
                plt.scatter(self.peaksAll[segment][1][1], self.peaksAll[segment][1][2], s=40, color='r', label=f"V : {self.peaksAll[segment][1][1]}, I : {self.peaksAll[segment][1][2]}")
            plt.plot(self.firstHalfVoltagesAll[segment], self.firstHalfCurrentsAll[segment], color='b')
            plt.plot(self.secondHalfVoltagesAll[segment], self.secondHalfCurrentsAll[segment], color='r')
            if self.peaksAll[segment][0][0] != -1 or self.peaksAll[segment][1][0] != -1:
                plt.legend()
            plt.savefig(os.path.join(segmentpath, f"Segment_{segment}_peaks.png"))
            plt.close()
        
            plt.figure()
            plt.title(f"{self.filename}, Segment # {segment}, log scale current", fontsize=10, fontweight='bold')
            plt.scatter(self.secondHalfVoltagesAll[segment], self.logScaleCurrentsAll[segment], marker='s', s=5, color='b')
            plt.savefig(os.path.join(segmentpath, f"Segement_{segment}_log.png"))
            plt.close()
        
            plt.figure()
            plt.title(f"{self.filename}, Segment # {segment}, Tafel", fontsize=10, fontweight='bold')
            plt.scatter(self.cathodicVoltagesAll[segment], self.cathodicCurrentsAll[segment], s=5, color='b')
            plt.scatter(self.anodicVoltagesAll[segment], self.anodicCurrentsAll[segment], s=5, color='r')
            plt.savefig(os.path.join(segmentpath, f"Segment_{segment}_tafel.png"))
            plt.close()
    
    def check_status(self, status):
        
        if (status >> 8) & 1: return True
        if (status >> 9) & 1: return True
        if (status >> 10) & 1: return True
        if (status >> 16) & 1: return True
        if (status >> 17) & 1: return True
        if (status >> 18) & 1: return True
        if (status & 0b1111) == 0b1111: return True
        
        return False
        
            
            
            
                
        
    
    