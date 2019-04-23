# Model for BEAMS application

import os
import pandas as pd 
import numpy as np
import time

class RunDataBase():
    def __init__(self):
        super(RunDataBase,self).__init__()
        self.filenames = set()
        self.run_list = []
        self.current_read_files = set()

    def read_all_files(self, filenames):
        remove_files = self.current_read_files.difference(filenames)
        new_files = filenames.difference(self.current_read_files)
        self.remove_runs(remove_files)
        corrupt_dat_files = self.add_runs(new_files)
        return corrupt_dat_files

    def remove_runs(self,remove_files):
        for filename in remove_files:
            for data in self.run_list:
                if(os.path.split(data.filename)[1] == filename):
                    print("Removing",filename,"...")
                    self.current_read_files.remove(filename)
                    self.run_list.remove(data)

    def add_runs(self,new_files):
        non_beams_files = []
        for filename in new_files:
            file_ext = os.path.splitext(os.path.basename(filename))[1]
            if(file_ext == ".dat"):
                full_file = self.find_full_file(filename)
                if self.is_BEAMS(full_file):
                    print("Reading",filename,"...")
                    self.current_read_files.add(filename)
                    self.run_list.append(RunData(filename=full_file))
                else:
                    non_beams_files.append(full_file)
            else:
                print(filename,"::",file_ext," is unsupported file type")
        return non_beams_files

    def find_full_file(self,file_root):
        for full_file in self.filenames:
            if(os.path.split(full_file)[1] == file_root):
                return full_file

    def is_BEAMS(self,filename):
        with open(filename) as file:
            first_line = file.readline()
        if first_line.split(None, 1)[0] == "BEAMS":
            return True
        return False

    def read_unrecognized_files(self,sections=None,filename=None):
        print(sections)
        print(filename)


class RunData():
    def __init__(self,filename=None,header_rows=1,hist_file=True):
        super(RunData,self).__init__()
        self.asymmetry = np.array([])
        self.time = np.array([])
        self.uncertainty = np.array([])
        self.header_data = {}
        self.filename = filename

        if filename:
            self.read_dat_file(filename=self.filename)

    def read_dat_file(self,filename=None):
        print("   Retrieving header data ...")
        self.retrieve_header_data()
        print("   Retrieving histogram data ...")
        self.retrieve_histogram_data()
        print("   Calculating Uncertainty ...")
        self.calculate_uncertainty()
        print("   Calculating Background Radiation ...")
        self.calculate_background_radiation()
        print("   Calculating Asymmetry ...")
        self.calculate_asymmetry()
        print("   Clearing Memory")
        del self.histogram_data
        print("Sucessfully read",filename)
     
    def retrieve_header_data(self):
        header = pd.read_csv(self.filename,nrows=1,skiprows=1)
        for title in header.columns:
            self.header_data[title] = header.iloc[0][title]
    
    def retrieve_histogram_data(self,hist=None):
        index = 1
        while(pd.read_csv(self.filename,nrows=1,skiprows=index).size > 4): # Determines what line histogram data starts.
            index += 1
        if not hist: # If no specific histogram is specified
            self.histogram_data = pd.read_csv(self.filename,skiprows=index)
            self.histogram_data.columns = ['Back','Front','Right','Left']
        else:
            self.histogram_data = pd.read_csv(self.filename,skiprows=index,usecols=hist)
          
    def calculate_uncertainty(self):
        d_front = np.sqrt(self.histogram_data['Front'])
        d_back = np.sqrt(self.histogram_data['Back'])
        self.uncertainty = np.sqrt(np.power((2*self.histogram_data['Back']/np.power(self.histogram_data['Front'] \
             + self.histogram_data['Back'],2)*d_front),2) + np.power((2*self.histogram_data['Front'] \
                 /np.power(self.histogram_data['Front'] + self.histogram_data['Back'],2)*d_back),2))
        del d_front
        del d_back

    def calculate_background_radiation(self):
        self.bkg_back = np.mean(self.histogram_data.iloc[70:800,0].values)
        self.bkg_front = np.mean(self.histogram_data.iloc[70:800,1].values)

    def calculate_asymmetry(self):
        self.asymmetry = ((self.histogram_data['Back'] - self.bkg_back) - (self.histogram_data['Front'] - self.bkg_front))\
            /((self.histogram_data['Front'] - self.bkg_front) + (self.histogram_data['Back'] - self.bkg_back))

    def bin_data(self):
        return
