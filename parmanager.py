import os
from collections import OrderedDict

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from parreader import ParReader, ParState, ParFileNameType

class ParMergeType:
    Default = 0
    PBS = 1
    Voltage = 2

class ParManager:
    def __init__(self):
        self.files = OrderedDict()
        self.type = ParMergeType.Default
        
    def add(self, par : ParReader):
        if par.status == ParState.OK:
            self.files[par.filepath] = par
            if par.filetype == ParFileNameType.PBS:
                self.type = ParMergeType.PBS if self.type == ParMergeType.Default else ParMergeType.Default
            elif par.filetype == ParFileNameType.VOLTAGE:
                self.type = ParMergeType.Voltage if self.type == ParMergeType.Default else ParMergeType.Default            
    
    def sort(self):
        
        def filesort(items):
            par = items[1]
            if par.filetype == ParFileNameType.PBS:
                value = int(par.filename[3:])
                return value - 200000
            if par.filetype == ParFileNameType.GLUCOSE:
                return int(par.filename)
            if par.filetype == ParFileNameType.VOLTAGE:
                return int(par.filename[:-1])
    
        self.files = OrderedDict(sorted(self.files.items(), key=filesort))

    
    def remove(self, filepath):
        self.files.pop(filepath)
    
    def get_min_segment(self):
        min_segment = None
        for file in self.files.values():
            if min_segment is None:
                min_segment = file.max_segment
            elif min_segment > file.max_segment:
                min_segment = file.max_segment
        return min_segment
    
    def save_user_figure(self, savepath):
        plt.figure(figsize=(15, 10))
        data = {}
        for file in self.files.values():
            data[file.filename] = pd.Series(file.voltages[file.select_segment])        
            data[f"{file.filename}_segment#{file.select_segment}"] = pd.Series(file.currents[file.select_segment])
            plt.plot(file.voltages[file.select_segment], file.currents[file.select_segment], label=f"{file.filename}")
        plt.legend()
        plt.savefig(os.path.join(savepath, f"Segment_User_Option.png"))
        plt.close()
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(savepath, F"Segment_User_Option_data.csv"), index=False)
    
    def save_user_csv(self, savepath):
        filename = []
        segment_num = []
        minpeak_voltage = []
        minpeak_current = []
        maxpeak_voltage = []
        maxpeak_current = []
        for file in self.files.values():
            filename.append(file.filename)
            segment_num.append(file.select_segment)
            minpeak_voltage.append(None if file.peaksAll[file.select_segment][0][0] == -1 else file.peaksAll[file.select_segment][0][1])
            minpeak_current.append(None if file.peaksAll[file.select_segment][0][0] == -1 else file.peaksAll[file.select_segment][0][2])
            maxpeak_voltage.append(None if file.peaksAll[file.select_segment][1][0] == -1 else file.peaksAll[file.select_segment][1][1])
            maxpeak_current.append(None if file.peaksAll[file.select_segment][1][0] == -1 else file.peaksAll[file.select_segment][1][2])
        data = {
            "Filename" : pd.Series(filename),
            "Segment#" : pd.Series(segment_num),
            "cathodicpeak_voltage" : pd.Series(minpeak_voltage),
            "cathodicpeak_current" : pd.Series(minpeak_current),
            "anodicpeak_voltage" : pd.Series(maxpeak_voltage),
            "anodicpeak_current" : pd.Series(maxpeak_current)
        }
        
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(savepath, F"Segment_User_Option_Peak.csv"), index=False)
    
    def save_segment_figure(self, savepath, segment):
        plt.figure()
        data = {}
        for file in self.files.values():
            data[file.filename] = pd.Series(file.voltages[segment])
            data[f"{file.filename}_segment#{segment}"] = pd.Series(file.currents[segment])
            plt.plot(file.voltages[segment], file.currents[segment], label=f"{file.filename}")
        plt.legend()
        plt.savefig(os.path.join(savepath, f"Segment{segment}.png"))
        plt.close()
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(savepath, F"Segment{segment}_data.csv"), index=False)
    
    def save_segment_csv(self, savepath, segment):
        filename = []
        segment_num = []
        minpeak_voltage = []
        minpeak_current = []
        maxpeak_voltage = []
        maxpeak_current = []
        for file in self.files.values():
            filename.append(file.filename)
            segment_num.append(segment)
            minpeak_voltage.append(None if file.peaksAll[segment][0][0] == -1 else file.peaksAll[segment][0][1])
            minpeak_current.append(None if file.peaksAll[segment][0][0] == -1 else file.peaksAll[segment][0][2])
            maxpeak_voltage.append(None if file.peaksAll[segment][1][0] == -1 else file.peaksAll[segment][1][1])
            maxpeak_current.append(None if file.peaksAll[segment][1][0] == -1 else file.peaksAll[segment][1][2])
        data = {
            "Filename" : pd.Series(filename),
            "Segment#" : pd.Series(segment_num),
            "cathodic_peak_voltage" : pd.Series(minpeak_voltage),
            "cathodic_current" : pd.Series(minpeak_current),
            "anodic_voltage" : pd.Series(maxpeak_voltage),
            "anodic_current" : pd.Series(maxpeak_current)
        }
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(savepath, F"Segment{segment}_Peak.csv"), index=False)
    
    
    def save(self, savepath, check, mode):
        if len(self.files) == 0:
            print("No files")
            return

        mode = mode.get()

        saveDetail = check[0].get()
        
        min_segment = self.get_min_segment()
            
        ### User options
        self.save_user_figure(savepath)
        self.save_user_csv(savepath)

        if saveDetail:
            for segment in range(min_segment):
                self.save_segment_figure(savepath, segment)
                self.save_segment_csv(savepath, segment)
                
            for file in self.files.values():
                file.save(savepath)
        
        if mode == ParMergeType.PBS:
            self.save_pbs_type(savepath)
        if mode == ParMergeType.Voltage:
            self.save_voltage_type(savepath)
    
    # TODO:
    def save_pbs_type(self, savepath):
        pass
    
    # TODO:
    def save_voltage_type(self, savepath):
        pass
        
            