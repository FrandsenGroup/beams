# Model for BEAMS application

import os
import pandas as pd #Going to do tests to see if numpy or pandas is faster.
import numpy as np

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
        self.add_runs(new_files)

    def remove_runs(self,remove_files):
        for filename in remove_files:
            for data in self.run_list:
                if(os.path.split(data.filename)[1] == filename):
                    print("Removing",filename,"...")
                    self.current_read_files.remove(filename)
                    self.run_list.remove(data)

    def add_runs(self,new_files):
        for filename in new_files:
            file_ext = os.path.splitext(os.path.basename(filename))[1]
            if(file_ext == ".dat"):
                print("Reading",filename,"...")
                self.current_read_files.add(filename)
                self.run_list.append(RunData(filename=self.find_full_file(filename)))
            else:
                print(filename,"::",file_ext," is unsupported file type")

    def find_full_file(self,file_root):
        for full_file in self.filenames:
            if(os.path.split(full_file)[1] == file_root):
                return full_file

class RunData():
    def __init__(self,filename=None):
        super(RunData,self).__init__()
        self.asymmetry = np.array([])
        self.time = np.array([])
        self.uncertainty = np.array([])
        self.filename = filename

        self.read_dat_file(filename)

    def read_dat_file(self,filename=None):
        data = pd.read_csv(filename)
        print(data)

    def update_asymmetry(self):
        return
