# Controller for BEAMS Application

import beams_view
import beams_model
from PyQt5 import QtWidgets, QtCore
import sys
import os

class BEAMSController():
    def __init__(self):
        super(BEAMSController,self).__init__()
    
    def start_program(self):
        app = QtWidgets.QApplication(sys.argv)
        self.BEAMS_view = beams_view.MainGUIWindow()
        self.BEAMS_database = beams_model.RunDataBase()
        self.set_events()
        self.BEAMS_view.show()
        sys.exit(app.exec_())

    def set_events(self):
        self.BEAMS_view.run_display.isolate_button.released.connect(lambda: self.isolate_click())
        self.BEAMS_view.run_display.inspect_button.released.connect(lambda: self.inspect_click())
        self.BEAMS_view.run_display.plot_all_button.released.connect(lambda: self.plot_all_click())

        self.BEAMS_view.file_manager.import_button.released.connect(lambda: self.import_click())
        self.BEAMS_view.file_manager.write_button.released.connect(lambda: self.write_click())
        self.BEAMS_view.file_manager.plot_button.released.connect(lambda: self.plot_click())

        self.BEAMS_view.plot_editor.input_xmax_one.returnPressed.connect(lambda: self.xvalue_change())
        self.BEAMS_view.plot_editor.input_xmax_two.returnPressed.connect(lambda: self.xvalue_change())
        self.BEAMS_view.plot_editor.input_xmin_one.returnPressed.connect(lambda: self.xvalue_change())
        self.BEAMS_view.plot_editor.input_xmin_two.returnPressed.connect(lambda: self.xvalue_change())
        self.BEAMS_view.plot_editor.input_slider_one.returnPressed.connect(lambda: self.bin_value_change())
        self.BEAMS_view.plot_editor.input_slider_two.returnPressed.connect(lambda: self.bin_value_change())
        self.BEAMS_view.plot_editor.slider_one.sliderMoved.connect(lambda: self.slider_moved())
        self.BEAMS_view.plot_editor.slider_two.sliderMoved.connect(lambda: self.slider_moved())

        self.BEAMS_view.exit_act.triggered.connect(QtWidgets.qApp.quit)
        self.BEAMS_view.add_data_act.triggered.connect(lambda: self.import_click())

    def isolate_click(self):
        return

    def inspect_click(self):
        return 

    def import_click(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.BEAMS_view,'Add file','/home')[0]
        self.BEAMS_database.filenames.update(filenames) 
        for filename in filenames:
            file_root = os.path.split(filename)[1]
            file_item = QtWidgets.QListWidgetItem(file_root,self.BEAMS_view.file_manager.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

    def write_click(self):
        print("Write button currently has no functionality ... ")

    def plot_click(self):
        checked_items = set()
        for index in range(self.BEAMS_view.file_manager.file_list.count()):
            if self.BEAMS_view.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                checked_items.add(self.BEAMS_view.file_manager.file_list.item(index).text())
        self.BEAMS_database.read_all_files(checked_items)

    def plot_all_click(self):
        return

    def xvalue_change(self):
        return

    def bin_value_change(self):
        return

    def slider_moved(self):
        return
