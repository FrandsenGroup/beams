# Controller for BEAMS Application

import beams_view
import beams_model

import numpy as np
from PyQt5 import QtWidgets, QtCore
import sys
import os

class BEAMSController():
    def __init__(self):
        super(BEAMSController,self).__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.BEAMS_view = beams_view.MainGUIWindow()
        self.BEAMS_database = beams_model.RunDataBase()
        self.set_main_events()
    
    def start_program(self):
        self.BEAMS_view.show()
        sys.exit(self.app.exec_())

    def set_main_events(self):
        self.BEAMS_view.run_display.isolate_button.released.connect(lambda: self.isolate_click())
        self.BEAMS_view.run_display.inspect_button.released.connect(lambda: self.inspect_click())
        self.BEAMS_view.run_display.plot_all_button.released.connect(lambda: self.plot_all_click())

        self.BEAMS_view.file_manager.import_button.released.connect(lambda: self.import_click())
        self.BEAMS_view.file_manager.write_button.released.connect(lambda: self.write_click())
        self.BEAMS_view.file_manager.plot_button.released.connect(lambda: self.plot_click())

        self.BEAMS_view.plot_editor.input_xmax_one.returnPressed.connect(lambda: self.xvalue_change(plot=1,xtype="MAX",\
            xvalue=float(self.BEAMS_view.plot_editor.input_xmax_one.text())))
        self.BEAMS_view.plot_editor.input_xmax_two.returnPressed.connect(lambda: self.xvalue_change(plot=2,xtype="MAX",\
            xvalue=float(self.BEAMS_view.plot_editor.input_xmax_two.text())))
        self.BEAMS_view.plot_editor.input_xmin_one.returnPressed.connect(lambda: self.xvalue_change(plot=1,xtype="MIN",\
            xvalue=float(self.BEAMS_view.plot_editor.input_xmin_one.text())))
        self.BEAMS_view.plot_editor.input_xmin_two.returnPressed.connect(lambda: self.xvalue_change(plot=2,xtype="MIN",\
            xvalue=float(self.BEAMS_view.plot_editor.input_xmin_two.text())))

        self.BEAMS_view.plot_editor.input_slider_one.returnPressed.connect(lambda: self.bin_value_change(plot=1,\
            bin_value=int(self.BEAMS_view.plot_editor.input_slider_one.text())))
        self.BEAMS_view.plot_editor.input_slider_two.returnPressed.connect(lambda: self.bin_value_change(plot=2,\
            bin_value=int(self.BEAMS_view.plot_editor.input_slider_two.text())))

        self.BEAMS_view.plot_editor.slider_one.sliderMoved.connect(lambda: self.slider_moved(plot=1,moving=True))
        self.BEAMS_view.plot_editor.slider_two.sliderMoved.connect(lambda: self.slider_moved(plot=2,moving=True))
        self.BEAMS_view.plot_editor.slider_one.sliderReleased.connect(lambda: self.slider_moved(plot=1,moving=False))
        self.BEAMS_view.plot_editor.slider_two.sliderReleased.connect(lambda: self.slider_moved(plot=2,moving=False))

        self.BEAMS_view.exit_act.triggered.connect(QtWidgets.qApp.quit)
        self.BEAMS_view.add_data_act.triggered.connect(lambda: self.import_click())
        self.BEAMS_view.format_act.triggered.connect(lambda: self.launch_formatter())

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
        beams_checked_items = set()
        for index in range(self.BEAMS_view.file_manager.file_list.count()):
            if self.BEAMS_view.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                beams_checked_items.add(self.BEAMS_view.file_manager.file_list.item(index).text())
        non_beams_files = self.BEAMS_database.read_all_files(beams_checked_items)
        if non_beams_files:
            self.invalid_file_format(filenames=non_beams_files)

    def plot_all_click(self):
        return

    def xvalue_change(self,plot=None,xtype=None,xvalue=None):
        return

    def bin_value_change(self,plot=None,bin_value=None):
        return

    def slider_moved(self,plot=None,moving=False):
        return

    def invalid_file_format(self,filenames=None):
        self.launch_formatter(filenames)

    def launch_formatter(self,filenames=None):
        self.file_formatter = beams_view.FileFormatterUI(filenames=filenames)
        self.set_formatter_events()
        self.file_formatter.file_display.setPlainText(open(filenames[0]).read())
        self.file_formatter.show()

    def set_formatter_events(self):
        self.file_formatter.check_asym.stateChanged.connect(lambda: self.formatter_checkbox(dtype="asym"))
        self.file_formatter.check_bhist.stateChanged.connect(lambda: self.formatter_checkbox(dtype="bhist"))
        self.file_formatter.check_error.stateChanged.connect(lambda: self.formatter_checkbox(dtype="error"))
        self.file_formatter.check_fhist.stateChanged.connect(lambda: self.formatter_checkbox(dtype="fhist"))
        self.file_formatter.check_lhist.stateChanged.connect(lambda: self.formatter_checkbox(dtype="lhist"))
        self.file_formatter.check_other.stateChanged.connect(lambda: self.formatter_checkbox(dtype="other"))
        self.file_formatter.check_rhist.stateChanged.connect(lambda: self.formatter_checkbox(dtype="rhist"))
        self.file_formatter.check_time.stateChanged.connect(lambda: self.formatter_checkbox(dtype="time"))
        self.file_formatter.check_uncertain.stateChanged.connect(lambda: self.formatter_checkbox(dtype="uncertain"))

        self.file_formatter.apply_button.released.connect(lambda: self.formatter_apply_click(apply_all=False))
        self.file_formatter.apply_all_button.released.connect(lambda: self.formatter_apply_click(apply_all=True))
        self.file_formatter.done_button.released.connect(lambda: self.formatter_done_click())
        self.file_formatter.file_list.currentIndexChanged.connect(lambda: self.formatter_file_changed())

    def formatter_checkbox(self,dtype=None):
        if dtype == "asym":
            self.file_formatter.spin_asym.setEnabled(False) if self.file_formatter.spin_asym.isEnabled() \
                else self.file_formatter.spin_asym.setEnabled(True)
        elif dtype == "bhist":
            self.file_formatter.spin_bhist.setEnabled(False) if self.file_formatter.spin_bhist.isEnabled() \
                else self.file_formatter.spin_bhist.setEnabled(True)
        elif dtype == "error":
            self.file_formatter.spin_error.setEnabled(False) if self.file_formatter.spin_error.isEnabled() \
                else self.file_formatter.spin_error.setEnabled(True)
        elif dtype == "fhist":
            self.file_formatter.spin_fhist.setEnabled(False) if self.file_formatter.spin_fhist.isEnabled() \
                else self.file_formatter.spin_fhist.setEnabled(True)
        elif dtype == "lhist":
            self.file_formatter.spin_lhist.setEnabled(False) if self.file_formatter.spin_lhist.isEnabled() \
                else self.file_formatter.spin_lhist.setEnabled(True)
        elif dtype == "other":
            self.file_formatter.spin_other.setEnabled(False) if self.file_formatter.spin_other.isEnabled() \
                else self.file_formatter.spin_other.setEnabled(True)
        elif dtype == "rhist":
            self.file_formatter.spin_rhist.setEnabled(False) if self.file_formatter.spin_rhist.isEnabled() \
                else self.file_formatter.spin_rhist.setEnabled(True)
        elif dtype == "time":
            self.file_formatter.spin_time.setEnabled(False) if self.file_formatter.spin_time.isEnabled() \
                else self.file_formatter.spin_time.setEnabled(True)
        else:
            self.file_formatter.spin_uncertain.setEnabled(False) if self.file_formatter.spin_uncertain.isEnabled() \
                else self.file_formatter.spin_uncertain.setEnabled(True)

    def formatter_apply_click(self,apply_all=False):
        data_sections = dict()
        if self.file_formatter.check_asym.isChecked():
            data_sections['asym'] = self.file_formatter.spin_asym.value() 
        if self.file_formatter.check_bhist.isChecked():
            data_sections['bhist'] = self.file_formatter.spin_bhist.value()
        if self.file_formatter.check_error.isChecked(): 
            data_sections['error'] = self.file_formatter.spin_error.value()
        if self.file_formatter.check_fhist.isChecked(): 
            data_sections['fhist'] = self.file_formatter.spin_fhist.value() 
        if self.file_formatter.check_lhist.isChecked():
            data_sections['lhist'] = self.file_formatter.spin_lhist.value() 
        if self.file_formatter.check_other.isChecked():
            data_sections['other'] = self.file_formatter.spin_other.value() 
        if self.file_formatter.check_rhist.isChecked():
            data_sections['rhist'] = self.file_formatter.spin_rhist.value() 
        if self.file_formatter.check_time.isChecked():
            data_sections['time'] = self.file_formatter.spin_time.value() 
        if self.file_formatter.check_uncertain.isChecked():
            data_sections['uncertain'] = self.file_formatter.spin_uncertain.value() 

        if not apply_all:
            self.BEAMS_database.read_unrecognized_format(sections=data_sections,\
                filename=self.file_formatter.file_list.currentText())

    def formatter_done_click(self):
        # FIXME Take data before closing
        self.file_formatter.close()

    def formatter_file_changed(self):
        return




