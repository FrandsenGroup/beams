# Model for BEAMS application

import os
import pandas as pd 
import numpy as np
import csv
from scipy.interpolate import spline
import time

class BEAMSModel():
    '''Manages the data, logic and rules of the application.'''
    def __init__(self):
        '''Initializes the empty model'''
        super(BEAMSModel,self).__init__()  
        self.filenames = set()
        self.failed_files = set()
        self.run_list = []
        self.current_read_files = set()

        self.color_options = ["blue", "red", "green", "orange", "purple", \
            "brown", "yellow", "gray", "olive", "cyan","pink"]
        self.used_colors = []
        
    def read_files(self, filenames):
        '''Separates user specified files into files to remove (files no longer checked) and files to add (files newly checked)'''
        # Remove old runs that are no longer checked
        remove_files = self.current_read_files.difference(filenames)
        self.remove_runs(remove_files)

        # Add runs that are newly checked by user
        new_files = filenames.difference(self.current_read_files)
        self.add_runs(new_files)

    def check_files(self, filenames):
        ''' Checks files for BEAMS format and dat extension
         
            Check files for:
            1) '.dat' extension
            2) BEAMS format (otherwise the user will need to specify the format for now)
            Return both the BEAMS and non-BEAMS formatted dat files.'''
        beams_files = set()
        non_beams_files = []
        for filename in filenames:
            file_ext = os.path.splitext(os.path.basename(filename))[1]
            if(file_ext == ".dat"):
                full_file = self.find_full_file(filename)
                if (self.is_BEAMS(full_file)) or (full_file in self.current_read_files):
                    beams_files.add(full_file)
                else:
                    non_beams_files.append(full_file)
        return [beams_files,non_beams_files]

    def remove_runs(self,remove_files):
        '''Goes through the array of runs and removes the ones whose filename is no longer checked.'''
        for filename in remove_files:
            for data in self.run_list:
                if(data.filename == filename):
                    self.update_colors(color=data.color,used=False)
                    self.current_read_files.remove(filename)
                    self.run_list.remove(data)
                    del data
        return True

    def add_runs(self,run_files):
        '''Adds any newly user-specified runs to the array of runs by filename'''
        for filename in run_files:
            self.run_list.append(RunData(filename=filename,color=self.color_options[0]))
            self.update_colors(color=self.color_options[0],used=True)
            self.current_read_files.add(filename)
        return True
                
    def find_full_file(self,file_root):
        '''Finds full file path from a file root (i.e. 006515.dat)'''
        for full_file in self.filenames:
            if(os.path.split(full_file)[1] == file_root):
                return full_file

    def is_BEAMS(self,filename):
        '''Checks if dat file is in BEAMS format (basically whether we converted it with BEAMS)'''
        with open(filename) as file:
            first_line = file.readline()
        if (first_line.split(None, 1)[0] == "BEAMS"):
            return True
        return False

    def check_unrecognized_format(self,sections=None,t0=None,header_rows=None,filenames=None):
        '''Checks user specified format to ensure it can be properly handled, gives appropriate error if not properly formatted'''
        def check_filenames():
            try:
                for filename in filenames:
                    with open(filename) as fp:
                        continue
            except IOError:
                return False
            return True

        def check_header():
            '''Checks to ensure header rows was given correctly'''
            for filename in filenames:
                with open(filename) as fp:
                    for i,line in enumerate(fp):
                        if i == int(header_rows):
                            line = line.rstrip()
                            first_values = line.split(',')
                            try:
                                for value in first_values:
                                    if value != 'nan':
                                        float(value)
                            except ValueError:
                                return False
                            break
            return True

        def check_binning():
            '''Ensures the initial bin is not larger then the number of lines or less then zero'''
            try:
                int(t0)
            except ValueError:
                return False
            for filename in filenames:
                n = sum(1 for i in open(filename, 'rb'))
                if int(t0) > n or int(t0) < 0:
                    return False    
            return True        

        def check_column_values():
            for k1, v1 in sections.items():
                for k2, v2 in sections.items():
                    if v1 == v2 and k1 != k2:
                        return False
            return True

        def check_columns_setup():
            '''Checks specified sections to ensure needed attributes can be calculated and none have the same column'''
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
        
        if not check_filenames():
            return 'EF'
        if not check_header():
            return 'EH'
        if not check_column_values():
            return 'EC'

        fformat = check_columns_setup()
        if not fformat:
            return 'EC'
        elif fformat == 'fbt' or fformat == 'fb' or fformat == 'lrt' or fformat == 'lr':
            if not check_binning():
                return 'EB'

        return fformat

    def read_unrecognized_format(self,sections=None,filenames=None,header_rows=None,fformat=None,binsize=0.390625,start_bins=None):
        '''Creates RunData objects from files with unrecognized but user specified formats (checked beforehand)'''
        for filename in filenames:
            self.run_list.append(RunData(filename=filename,header_rows=header_rows,isBEAMS=False,sections=sections,fformat=fformat,\
                binsize=binsize,color=self.color_options[0]))
            self.update_colors(color=self.color_options[0],used=True)
        return True
                  
    def inspect_unrecognized_column(self,in_runs=False,column=None,run_index=None,filename=None,header_rows=None):
        '''Reads in the data from a column from a file with an unrecognized format'''
        if in_runs:
            self.run_list[run_index].read_formatted_file(recalc=True)
            self.column_data = self.run_list[run_index].histogram_data[column]
            del self.run_list[run_index].histogram_data
        else:
            if filename:
                self.column_data = pd.read_csv(filename,usecols=[column],skiprows=header_rows)
        

    def index_from_filename(self,filename=None):
        '''Retrieves a run's index in the model based on filename'''
        for index in range(len(self.run_list)):
            if self.run_list[index].filename == filename:
                return index
        return -1

    def update_colors(self,color=None,used=False,custom=False):
        if not custom:
            if used:
                if color in self.color_options:
                    self.color_options.remove(color)
                if color not in self.used_colors:
                    self.used_colors.append(color)
            else:
                if color in self.used_colors:
                    self.used_colors.remove(color)
                if color not in self.color_options:
                    self.color_options.append(color)
        return True

    def write_file(self,old_filename=None,new_filename=None,checked_items=None):
        if old_filename:
            index = self.index_from_filename(filename=old_filename)
            if index != -1:
                self.run_list[index].match_arrays(new=False)
                if checked_items[0] and checked_items[1] and checked_items[2]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].asymmetry,self.run_list[index].time,self.run_list[index].uncertainty],\
                        fmt='%2.4f,%2.9f,%2.4f',header='Asymmetry, Time, Uncertainty')
                elif checked_items[0] and checked_items[1]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].asymmetry,self.run_list[index].time],\
                        fmt='%2.4f,%2.9f',header='Asymmetry, Time')
                elif checked_items[0] and checked_items[2]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].asymmetry,self.run_list[index].uncertainty],\
                        fmt='%2.4f,%2.4f',header='Asymmetry, Uncertainty')
                elif checked_items[0]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].asymmetry],fmt='%2.4f',header='Asymmetry')
                elif checked_items[1] and checked_items[2]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].time,self.run_list[index].uncertainty],\
                        fmt='%2.9f,%2.4f',header='Time, Uncertainty')
                elif checked_items[1]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].time],fmt='%2.9f',header='Time')
                elif checked_items[2]:
                    np.savetxt(new_filename, np.c_[self.run_list[index].uncertainty],fmt='%2.4f',header='Uncertainty')
                return True
        return False


class RunData():
    '''Stores all data relevant to a run, both calculated quantities and graphing variables'''
    def __init__(self,filename=None,header_rows=1,isBEAMS=True,sections=None,color="blue",fformat='fb',t0=0,t1=800,binsize=0.390625):
        '''Initialize a RunData object based on filename and format'''
        super(RunData,self).__init__()
        self.asymmetry = np.array([])
        self.uncertainty = np.array([])
        self.header_data = {}
        self.filename = filename
        self.color = color
        self.header_rows = header_rows
        self.isBEAMS = isBEAMS
        self.t0 = t0
        self.t1 = t1
        self.columns = []

        if isBEAMS:
            self.read_dat_file(filename=self.filename)
            self.columns = ['Front','Back','Right','Left']
        else:
            for key,value in sections.items():
                self.columns.append(key)
            self.sections = sections
            self.fformat= fformat
            self.binsize = float(binsize)
            self.read_formatted_file()
            del self.histogram_data

    def read_dat_file(self,filename=None):
        '''Reads in data from a BEAMS formatted file'''
        self.retrieve_header_data()
        self.retrieve_histogram_data()
        self.calculate_uncertainty()
        self.calculate_background_radiation()
        self.calculate_asymmetry()
        self.calculate_time(num_bins=self.header_data['numBins'])
        del self.histogram_data

    def check_formatted_input(self):
        '''Checks data we read in from the file'''
        return

    def read_formatted_file(self,recalc=False):
        '''Reads in non-BEAMS formatted files based on user input'''
        def invert_dict():
            '''Inverts section dictionary so column values are keys and column names are values'''
            self.sections = {v: k for k, v in self.sections.items()}

        def read_fb_format():
            '''Reads in file where Front and Back Histograms are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.calculate_uncertainty(hist_one='Back',hist_two='Front')
            self.calculate_background_radiation(hist_one='Back',hist_two='Front')
            self.calculate_asymmetry(hist_one='Back',hist_two='Front')
            self.calculate_time(num_bins=len(self.asymmetry),binsize=self.binsize)

        def read_fbt_format():
            '''Reads in file where Front and Back Histograms and Time are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.calculate_uncertainty(hist_one='Back',hist_two='Front')
            self.calculate_background_radiation(hist_one='Back',hist_two='Front')
            self.calculate_asymmetry(hist_one='Back',hist_two='Front')
            self.time = self.histogram_data['Time'].values

        def read_lr_format():
            '''Reads in file where Left and Right Histograms are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.calculate_uncertainty(hist_one='Left',hist_two='Right')
            self.calculate_background_radiation(hist_one='Left',hist_two='Right')
            self.calculate_asymmetry(hist_one='Left',hist_two='Right')
            self.calculate_time(num_bins=len(self.asymmetry),binsize=self.binsize)

        def read_lrt_format():
            '''Reads in file where Left and Right Histograms and Time are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.calculate_uncertainty(hist_one='Left',hist_two='Right')
            self.calculate_background_radiation(hist_one='Left',hist_two='Right')
            self.calculate_asymmetry(hist_one='Left',hist_two='Right')
            self.time = self.histogram_data['Time'].values

        def read_at_format():
            '''Reads in file where Asymmetry and Time are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.asymmetry = self.histogram_data['Asymmetry'].values
            self.time = self.histogram_data['Time'].values
            self.uncertainty = np.zeros(len(self.asymmetry))

        def read_atu_format():
            '''Reads in file where Asymmetry, Time and Uncertainty are given'''
            self.histogram_data = pd.read_csv(self.filename,skiprows=self.header_rows,usecols=list(self.sections.values()))
            invert_dict()
            column_names = list(self.sections.values())
            for key,value in self.sections.items():
                column_names[key] = value
            self.histogram_data.columns = column_names
            self.asymmetry = self.histogram_data['Asymmetry'].values
            self.time = self.histogram_data['Time'].values
            self.uncertainty = np.array(self.histogram_data['Uncertainty'])

        if recalc:
            invert_dict()

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

    def retrieve_header_data(self): 
        '''Retrieves header data from a BEAMS formatted file'''
        header = pd.read_csv(self.filename,nrows=self.header_rows,skiprows=1)
        for title in header.columns:
            self.header_data[title] = header.iloc[0][title]
    
    def retrieve_histogram_data(self):
        '''Retrieves histogram data from a BEAMS formatted file'''
        index = 1
        while(pd.read_csv(self.filename,nrows=1,skiprows=index).size > 4): # Determines what line histogram data starts.
            index += 1
       
        self.histogram_data = pd.read_csv(self.filename,skiprows=index)
        self.histogram_data.columns = ['Back','Front','Right','Left']
    
    def calculate_time(self,num_bins=None,binsize=0.390625):
        '''Calculates the time array based on bin size and number of bins'''
        # FIXME I'm just realizing we don't really need this array. Try working to delete it.
        self.time = np.arange(0,(num_bins-1)*binsize/1000,binsize/1000)

    def calculate_uncertainty(self,hist_one='Back',hist_two='Front'):
        '''Calculates the uncertainty based on histograms'''
        d_front = np.sqrt(self.histogram_data[hist_two])
        d_back = np.sqrt(self.histogram_data[hist_one])
        self.uncertainty = np.array(np.sqrt(np.power((2*self.histogram_data[hist_one]/np.power(self.histogram_data[hist_two] \
             + self.histogram_data[hist_one],2)*d_front),2) + np.power((2*self.histogram_data[hist_two] \
                 /np.power(self.histogram_data[hist_two] + self.histogram_data[hist_one],2)*d_back),2)))
        np.nan_to_num(self.uncertainty,copy=False)

        del d_front
        del d_back
    
    def re_calculate_uncertainty(self):
        if self.isBEAMS:
            self.retrieve_histogram_data()
            self.calculate_uncertainty()
        else:
            self.read_formatted_file(recalc=True)

    def calculate_background_radiation(self,hist_one='Back',hist_two='Front'):
        '''Calculates the background radiation based on histogram data before positrons are being detected'''
        background = self.histogram_data.loc[int(self.t0):int(self.t1),hist_one].values
        mean_b = np.mean(background) # Find mean based on histogram area
        background = np.clip(background,0,mean_b*4) # Clips outlier values
        self.bkg_back = np.mean(background) # Find mean on new array

        background = self.histogram_data.loc[int(self.t0):int(self.t1),hist_two].values
        mean_b = np.mean(background)
        background = np.clip(background,0,mean_b*4)
        self.bkg_front = np.mean(background)

        del background

    def calculate_asymmetry(self,hist_one='Back',hist_two='Front'):
        '''Calculate asymmetry based on histograms'''
        self.asymmetry = ((self.histogram_data[hist_one] - self.bkg_back) - (self.histogram_data[hist_two] - self.bkg_front))\
            /((self.histogram_data[hist_two] - self.bkg_front) + (self.histogram_data[hist_one] - self.bkg_back))
        self.asymmetry.fillna(0.0,inplace=True)

    def calculate_fft(self,bin_size):
        '''Calculates fast fourier transform on asymmetry'''
        n = len(self.new_asymmetry)
        k = np.arange(n)
        frequencies = k / (n * bin_size)
        frequencies = frequencies[range(int(n/2))]
        yValues = np.fft.fft([self.new_asymmetry,self.new_times]) / n
        yValues = abs(yValues[0, range(int(n/2))])
        yValues[0] = 0

        # Calculate the spline for the graph
        self.x_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)
        np.insert(self.x_smooth,0,0)
        self.y_smooth = spline(frequencies, yValues, self.x_smooth)
        np.insert(self.y_smooth,0,0)

    def bin_data(self,bin_size=150,xmin=0,xmax=10,slider_moving=False,initial_binsize=0.390625):
        '''Re-bins the asymmetry based on user specified bin size'''
        # start = time.time()

        time_sep = float(initial_binsize)/1000
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

    def match_arrays(self,new=True):
        '''Ensures the time array doesn't become larger or smaller by one value based on errors in calculation'''
        if new:
            if len(self.new_times) != len(self.new_asymmetry):
                if len(self.new_asymmetry) > len(self.new_times):
                    self.new_asymmetry = self.new_asymmetry[0:len(self.new_times)]
                    self.new_uncertainty = self.new_uncertainty[0:len(self.new_times)]
                else:
                    self.new_times = self.new_times[0:len(self.new_asymmetry)]
        else:
            if len(self.time) != len(self.asymmetry):
                if len(self.asymmetry) > len(self.time):
                    self.asymmetry = self.asymmetry[0:len(self.time)]
                    self.uncertainty = self.uncertainty[0:len(self.time)]
                else:
                    self.time = self.time[0:len(self.asymmetry)]

