# Model for BEAMS application

import os
import pandas as pd 
import numpy as np
from scipy.interpolate import spline
import time

class BEAMSModel():
    def __init__(self):
        super(BEAMSModel,self).__init__()  
        self.filenames = set()
        self.failed_files = set()
        self.run_list = []
        self.current_read_files = set()
        self.color_options = ["blue", "orange", "green", "red", "purple", \
            "brown", "pink", "gray", "olive", "cyan","custom"]
        self.used_colors = []
        
    def read_files(self, filenames):
        # Remove old runs that are no longer checked
        remove_files = self.current_read_files.difference(filenames)
        self.remove_runs(remove_files)

        # Add runs that are newly checked by user
        new_files = filenames.difference(self.current_read_files)
        self.add_runs(new_files)

    def check_files(self, filenames):
        # Check files for:
        # 1) '.dat' extension
        # 2) BEAMS format (otherwise the user will need to specify the format for now)
        # Return both the BEAMS and non-BEAMS formatted dat files.
        beams_files = set()
        non_beams_files = []
        for filename in filenames:
            file_ext = os.path.splitext(os.path.basename(filename))[1]
            if(file_ext == ".dat"):
                full_file = self.find_full_file(filename)
                if self.is_BEAMS(full_file):
                    beams_files.add(full_file)
                else:
                    non_beams_files.append(full_file)
        return [beams_files,non_beams_files]

    def remove_runs(self,remove_files):
        # Goes through the array of runs and removes the ones whose filename is no longer checked.
        for filename in remove_files:
            for data in self.run_list:
                if(data.filename == filename):
                    self.used_colors.remove(data.color)
                    self.color_options.append(data.color)
                    self.current_read_files.remove(filename)
                    self.run_list.remove(data)

    def add_runs(self,run_files):
        # Adds any newly user-specified runs to the array of runs by filename
        for filename in run_files:
            self.run_list.append(RunData(filename=filename,color=self.color_options[0]))
            self.used_colors.append(self.color_options[0])
            self.color_options.remove(self.color_options[0])
            self.current_read_files.add(filename)
            print(self.used_colors,"\n",self.color_options)

    def find_full_file(self,file_root):
        # Only the root of the filepath is given from the file manager, here we find the full file
        # path from the stored array of full file paths (stored when the user imports a file)
        for full_file in self.filenames:
            if(os.path.split(full_file)[1] == file_root):
                return full_file

    def is_BEAMS(self,filename):
        # Checks if dat file is in BEAMS format (basically whether we converted it with BEAMS)
        with open(filename) as file:
            first_line = file.readline()
        if first_line.split(None, 1)[0] == "BEAMS":
            return True
        return False

    def check_unrecognized_format(self,sections=None):
        '''Checks user specified format to ensure it can be properly handled'''
        if sections:
            if 'Front' in sections and 'Back' in sections:
                if 'Time' in sections:
                    if (sections['Front'] == sections['Back']) or (sections['Front'] == sections['Time']) \
                        or (sections['Back'] == sections['Time']):
                        return False
                    return "fbt"
                else:
                    if (sections['Front'] == sections['Back']):
                        return False
                    return "fb"
            elif 'Left' in sections and 'Right' in sections:
                if 'Time' in sections:
                    if (sections['Left'] == sections['Right']) or (sections['Left'] == sections['Time']) \
                        or (sections['Right'] == sections['Time']):
                        return False
                    return "lrt"
                else:
                    if (sections['Left'] == sections['Right']):
                        return False
                    return "lr"
            elif 'Asymmetry' in sections:
                if 'Time' in sections:
                    if 'Uncertainty' in sections:
                        if (sections['Asymmetry'] == sections['Time']) or (sections['Asymmetry'] == sections['Uncertainty']) \
                            or (sections['Uncertainty'] == sections['Time']):
                            return False    
                        return 'atu'
                    else:
                        if (sections['Asymmetry'] == sections['Time']):
                            return False
                        return 'at'
                else:
                    return False
            else:
                return False
        else:
            print("Processing Error :: m.beams_model.py -> c.BEAMSModel -> f.check_unrecognized_format")
            return False
        return False

    def read_unrecognized_format(self,sections=None,filenames=None,header_rows=None,fformat=None):
        for filename in filenames:
            self.run_list.append(RunData(filename=filename,header_rows=header_rows,isBEAMS=False,sections=sections,fformat=fformat))

    def inspect_unrecognized_column(self,filename=None,column=None,header_rows=None):
        print(filename,"\n",column,"\n",header_rows)
        self.column_data = pd.read_csv(filename,skiprows=header_rows,usecols=[column])
        print(self.column_data)

    def index_from_filename(self,filename=None):
        for index in range(len(self.run_list)):
            if self.run_list[index].filename == filename:
                return index
        return -1


class RunData():
    def __init__(self,filename=None,header_rows=1,isBEAMS=True,sections=None,color="blue",fformat='fb',t0=800,binsize=0.396025):
        super(RunData,self).__init__()
        self.asymmetry = np.array([])
        self.uncertainty = np.array([])
        self.header_data = {}
        self.filename = filename
        self.color = color
        self.header_rows = header_rows

        if isBEAMS:
            self.read_dat_file(filename=self.filename)
        else:
            self.sections = sections
            self.fformat= fformat
            self.read_formatted_file()

    def read_dat_file(self,filename=None):
        self.retrieve_header_data()
        self.retrieve_histogram_data()
        self.calculate_uncertainty()
        self.calculate_background_radiation()
        self.calculate_asymmetry()
        self.time = np.arange(0,self.header_data['numBins']*self.header_data['binsize']/1000,self.header_data['binsize']/1000)
        del self.histogram_data

    def read_formatted_file(self):
        def invert_dict():
            self.sections = {v: k for k, v in self.sections.items()}

        def read_fb_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Front'],self.sections['Back']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1]]

        def read_fbt_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Front'],self.sections['Back'],self.sections['Time']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1],self.sections[2]]

        def read_lr_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Left'],self.sections['Right']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1]]

        def read_lrt_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Left'],self.sections['Right'],self.sections['Time']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1],self.sections[2]]

        def read_at_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Asymmetry'],self.sections['Time']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1]]

        def read_atu_format():
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=[self.sections['Asymmetry'],self.sections['Time'],self.sections['Uncertainty']])
            invert_dict()
            self.histogram_data.columns = [self.sections[0],self.sections[1],self.sections[2]]

        if self.fformat == "fb":
            read_fb_format()
        elif self.fformat == "fbt":
            read_fbt_format()
        elif self.fformat == "lr":
            read_lr_format()
        elif self.fformat == "lrt":
            read_lrt_format()
        elif self.fformat == "at":
            read_at_format()
        elif self.fformat == "atu":
            read_atu_format()
        else:
            print("Unrecognized format:")

        del self.histogram_data

    def retrieve_header_data(self): 
        header = pd.read_csv(self.filename,nrows=self.header_rows,skiprows=1)
        for title in header.columns:
            self.header_data[title] = header.iloc[0][title]
    
    def retrieve_histogram_data(self):
        index = 1
        while(pd.read_csv(self.filename,nrows=1,skiprows=index).size > 4): # Determines what line histogram data starts.
            index += 1
       
        self.histogram_data = pd.read_csv(self.filename,skiprows=index)
        self.histogram_data.columns = ['Back','Front','Right','Left']
        
    def calculate_uncertainty(self):
        d_front = np.sqrt(self.histogram_data['Front'])
        d_back = np.sqrt(self.histogram_data['Back'])
        self.uncertainty = np.sqrt(np.power((2*self.histogram_data['Back']/np.power(self.histogram_data['Front'] \
             + self.histogram_data['Back'],2)*d_front),2) + np.power((2*self.histogram_data['Front'] \
                 /np.power(self.histogram_data['Front'] + self.histogram_data['Back'],2)*d_back),2))
        del d_front
        del d_back

    def calculate_background_radiation(self,front=0,back=1):
        self.bkg_back = np.mean(self.histogram_data.iloc[70:800,front].values)
        self.bkg_front = np.mean(self.histogram_data.iloc[70:800,back].values)

    def calculate_asymmetry(self):
        self.asymmetry = ((self.histogram_data['Back'] - self.bkg_back) - (self.histogram_data['Front'] - self.bkg_front))\
            /((self.histogram_data['Front'] - self.bkg_front) + (self.histogram_data['Back'] - self.bkg_back))
        self.asymmetry.fillna(0.0,inplace=True)

    def calculate_fft(self,bin_size):
        period_s = bin_size
        frequency_s = 1.0 / period_s
        n = len(self.new_asymmetry)
        k = np.arange(n)
        period = n / frequency_s
        frequencies = k / period
        frequencies = frequencies[range(int(n/2))]
        yValues = np.fft.fft([self.new_asymmetry,self.new_times]) / n
        yValues = abs(yValues[0, range(int(n/2))])

        # Calculate the spline for the graph
        self.x_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)
        np.insert(self.x_smooth,0,0)
        self.y_smooth = spline(frequencies, yValues, self.x_smooth)
        np.insert(self.y_smooth,0,0)

    def bin_data(self,bin_size=150,xmin=0,xmax=10,slider_moving=False):
        # start = time.time()

        time_sep = float(self.header_data['binsize'])/1000
        bin_size = float(bin_size)/1000
        indices_per_bin = int(np.floor(bin_size/time_sep))
        indices_total = int(np.floor((float(xmax)-float(xmin))/time_sep))
        indices_new_total = int(np.floor(indices_total / indices_per_bin))
        indices_counted = int(np.floor(float(xmin)/time_sep))

        self.new_asymmetry = np.empty(indices_new_total)
        self.new_uncertainty = np.zeros(indices_new_total)
        self.new_times = np.arange(float(xmin),float(xmax)+bin_size,bin_size)

        mean = np.mean
        if slider_moving:
            for new_index in range(indices_new_total):
                self.new_asymmetry[new_index] = mean(self.asymmetry[indices_counted:(indices_counted+indices_per_bin)])
                indices_counted += indices_per_bin
            self.match_arrays()
        else:
            uncertainty_sum = 0
            for new_index in range(indices_new_total):
                self.new_asymmetry[new_index] = mean(self.asymmetry[indices_counted:(indices_counted+indices_per_bin)])
                indices_counted += indices_per_bin
                for unc in self.uncertainty[indices_counted:indices_counted+indices_per_bin]:
                    uncertainty_sum += unc**2
                self.new_uncertainty[new_index] = np.sqrt(uncertainty_sum) / (indices_per_bin)
                uncertainty_sum = 0
            self.match_arrays()
            self.calculate_fft(bin_size=bin_size)

    def match_arrays(self):
        if len(self.new_times) != len(self.new_asymmetry):
            if len(self.new_asymmetry) > len(self.new_times):
                self.new_asymmetry = self.new_asymmetry[0:len(self.new_times)]
                self.new_uncertainty = self.new_uncertainty[0:len(self.new_times)]
            else:
                self.new_times = self.new_times[0:len(self.new_asymmetry)]

