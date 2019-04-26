# Controller for BEAMS Application

import beams_view
import beams_model

import numpy as np
from PyQt5 import QtWidgets, QtCore
import sys
import time
import os

# Matplotlib covers the plotting of the data, with necessary PyQt5 crossover libraries
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class BEAMSController():
    def __init__(self):
        '''Initializes controller with View and Model and sets events'''
        super(BEAMSController,self).__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.BEAMS_view = beams_view.MainGUIWindow()
        self.BEAMS_model = beams_model.BEAMSModel()
        self.set_main_events()
    
    def start_program(self):
        '''Shows the GUI'''
        self.BEAMS_view.show()
        sys.exit(self.app.exec_())

    def set_main_events(self):
        '''Sets functions for event handling with the View'''
        self.BEAMS_view.run_display.isolate_button.released.connect(lambda: self.isolate_click())
        self.BEAMS_view.run_display.plot_all_button.released.connect(lambda: self.plot_all_click())
        self.BEAMS_view.run_display.inspect_file_button.released.connect(lambda: self.inspect_file())
        self.BEAMS_view.run_display.inspect_hist_button.released.connect(lambda: self.inspect_hist())
        self.BEAMS_view.run_display.run_titles.currentTextChanged.connect(lambda: self.update_run_display())
        self.BEAMS_view.run_display.color_choices.currentIndexChanged.connect(lambda: self.color_changed())

        self.BEAMS_view.file_manager.import_button.released.connect(lambda: self.import_click())
        self.BEAMS_view.file_manager.write_button.released.connect(lambda: self.write_click())
        self.BEAMS_view.file_manager.plot_button.released.connect(lambda: self.plot_click())

        self.BEAMS_view.plot_editor.input_xmax_one.returnPressed.connect(lambda: self.plot_parameter_change(plot=1,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmax_two.returnPressed.connect(lambda: self.plot_parameter_change(plot=2,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmin_one.returnPressed.connect(lambda: self.plot_parameter_change(plot=1,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmin_two.returnPressed.connect(lambda: self.plot_parameter_change(plot=2,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_slider_one.returnPressed.connect(lambda: self.plot_parameter_change(plot=1,slider_moving=False,bin_changed=True))
        self.BEAMS_view.plot_editor.input_slider_two.returnPressed.connect(lambda: self.plot_parameter_change(plot=2,slider_moving=False,bin_changed=True))
        self.BEAMS_view.plot_editor.slider_one.sliderMoved.connect(lambda: self.plot_parameter_change(plot=1,slider_moving=True))
        self.BEAMS_view.plot_editor.slider_two.sliderMoved.connect(lambda: self.plot_parameter_change(plot=2,slider_moving=True))
        self.BEAMS_view.plot_editor.slider_one.sliderReleased.connect(lambda: self.plot_parameter_change(plot=1,slider_moving=False))
        self.BEAMS_view.plot_editor.slider_two.sliderReleased.connect(lambda: self.plot_parameter_change(plot=2,slider_moving=False))

        self.BEAMS_view.exit_act.triggered.connect(QtWidgets.qApp.quit)
        self.BEAMS_view.add_data_act.triggered.connect(lambda: self.import_click())
        self.BEAMS_view.format_act.triggered.connect(lambda: self.launch_formatter())

    def isolate_click(self):
        '''Handles the user clicking the "Isolate" button'''
        self.clear_plots()
        self.plot_runs(filename=self.BEAMS_view.run_display.run_titles.currentText())

    def import_click(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.BEAMS_view,'Add file','/home')[0]
        self.BEAMS_model.filenames.update(filenames) 
        for filename in filenames:
            file_root = os.path.split(filename)[1]
            file_item = QtWidgets.QListWidgetItem(file_root,self.BEAMS_view.file_manager.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

    def write_click(self):
        print("Write button currently has no functionality ... ")

    def plot_click(self):
        # Create a set of the checked filenames from the file manager panel.
        beams_checked_items = set()
        for index in range(self.BEAMS_view.file_manager.file_list.count()):
            if self.BEAMS_view.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                beams_checked_items.add(self.BEAMS_view.file_manager.file_list.item(index).text())

        # Use the check_files and read_files function from the BEAMSModel class
        beams_files,non_beams_files = self.BEAMS_model.check_files(beams_checked_items)
        self.BEAMS_model.read_files(beams_files)
        if non_beams_files:
            self.invalid_file_format(filenames=non_beams_files)
        
        # Plot the runs
        self.clear_plots(plot=3)
        self.plot_runs(filename=None,plot=3,slider_moving=False) # FIXME I think there is some intricacy with default paramaters. Test this.
        self.populate_run_display(filenames=self.BEAMS_model.current_read_files) # FIXME

    def plot_all_click(self):
        self.clear_plots(plot=3)
        self.plot_runs(filename=None,plot=3,slider_moving=False)

    def clear_plots(self,plot=3):
        # Only clears the plot that needs to be updated
        if plot == 1:
            self.BEAMS_view.plot_panel.canvas_one.axes_time.clear()
            self.BEAMS_view.plot_panel.canvas_one.axes_freq.clear()  
        elif plot == 2:
            self.BEAMS_view.plot_panel.canvas_two.axes_time.clear()
            self.BEAMS_view.plot_panel.canvas_two.axes_freq.clear()
        else:
            self.BEAMS_view.plot_panel.canvas_one.axes_time.clear()
            self.BEAMS_view.plot_panel.canvas_one.axes_freq.clear()
            self.BEAMS_view.plot_panel.canvas_two.axes_time.clear()
            self.BEAMS_view.plot_panel.canvas_two.axes_freq.clear()
            
    def plot_runs(self,filename=None,plot=3,slider_moving=False):
        if not filename: # If no specific plot specified
            for run in self.BEAMS_model.run_list:
                if plot == 1 or plot == 3:
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_one.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_one.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_one.text())
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',mfc=run.color,mec=run.color)
                    self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,marker='.')
                if plot == 2 or plot == 3:
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_two.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_two.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_two.text())
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',mfc=run.color,mec=run.color)
                    self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,marker='.')
        else: 
            run = self.BEAMS_model.run_list[self.BEAMS_model.index_from_filename(filename=filename)]
            self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
            self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',mfc=run.color,mec=run.color)
            self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,marker='.')
            self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
            self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',mfc=run.color,mec=run.color)
            self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,marker='.')

        self.BEAMS_view.plot_panel.canvas_one.set_style()
        self.BEAMS_view.plot_panel.canvas_two.set_style()

    def plot_parameter_change(self,plot=3,slider_moving=False,xlims_changed=False,bin_changed=False):
        if bin_changed:
            self.BEAMS_view.plot_editor.slider_one.setValue(float(self.BEAMS_view.plot_editor.input_slider_one.text())) if plot == 1 \
                else self.BEAMS_view.plot_editor.slider_two.setValue(float(self.BEAMS_view.plot_editor.input_slider_two.text()))
        if slider_moving:
            self.BEAMS_view.plot_editor.input_slider_one.setText(str(self.BEAMS_view.plot_editor.slider_one.value())) if plot == 1 \
                else self.BEAMS_view.plot_editor.input_slider_two.setText(str(self.BEAMS_view.plot_editor.slider_two.value()))
            mod_value = self.BEAMS_view.plot_editor.slider_one.value()%5 if plot == 1 else self.BEAMS_view.plot_editor.slider_two.value()%5  
            if mod_value == 0:
                self.clear_plots(plot=plot)
                self.plot_runs(plot=plot,slider_moving=slider_moving)
        else:
            self.clear_plots(plot=plot)
            self.plot_runs(plot=plot,slider_moving=slider_moving)

            if xlims_changed:
                self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_two.text()))

    def populate_run_display(self,filenames=None):
        if len(filenames) > 0:
            self.BEAMS_view.run_display.run_titles.clear()
            self.BEAMS_view.run_display.run_titles.addItems(filenames)
            self.BEAMS_view.run_display.color_choices.addItems(self.BEAMS_model.color_options)
            self.update_run_display()
            self.enable_run_display(isEnabled=True)
        else:
            self.BEAMS_view.run_display.run_titles.clear()
            self.enable_run_display(isEnabled=False)

    def enable_run_display(self,isEnabled=False):
        if not isEnabled:
            self.BEAMS_view.run_display.run_titles.addItem("No Runs Plotted")
            self.BEAMS_view.run_display.histograms.addItem("None")
            self.BEAMS_view.run_display.histograms.setEnabled(False)
            self.BEAMS_view.run_display.inspect_hist_button.setEnabled(False)
        self.BEAMS_view.run_display.color_choices.setEnabled(isEnabled)
        self.BEAMS_view.run_display.isolate_button.setEnabled(isEnabled)
        self.BEAMS_view.run_display.inspect_file_button.setEnabled(isEnabled)
        self.BEAMS_view.run_display.plot_all_button.setEnabled(isEnabled)

    def update_run_display(self):
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        if run_index != -1:
            self.BEAMS_view.run_display.color_choices.setCurrentText(self.BEAMS_model.run_list[run_index].color)
            if self.BEAMS_model.is_BEAMS(self.BEAMS_view.run_display.run_titles.currentText()):
                self.BEAMS_view.run_display.histograms.clear()
                self.BEAMS_view.run_display.histograms.addItems(['Front','Back','Right','Left'])
                self.BEAMS_view.run_display.histograms.setEnabled(True)
                self.BEAMS_view.run_display.inspect_hist_button.setEnabled(True)

    def color_changed(self):
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].color = self.BEAMS_view.run_display.color_choices.currentText()
        self.clear_plots()
        self.plot_runs()

    def inspect_file(self):
        self.file_display = beams_view.FileDisplayUI(filename=self.BEAMS_view.run_display.run_titles.currentText())
        self.file_display.show()

    def inspect_hist(self):
        hist_display = beams_view.PlotPanel(center=False)

        histogram = self.BEAMS_view.run_display.histograms.currentText()
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].retrieve_histogram_data()

        # Why is a bar chart so much slower then just plotting???
        hist_display.canvas_hist.axes_hist.plot(self.BEAMS_model.run_list[run_index].histogram_data[histogram].values,linestyle='None',marker="s")

        # self.hist_display.show()
        del self.BEAMS_model.run_list[run_index].histogram_data

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
        self.file_formatter.skip_button.released.connect(lambda: self.formatter_skip_click())

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
            self.BEAMS_model.read_unrecognized_files(sections=data_sections,\
                filename=self.file_formatter.file_list.currentText())

    def formatter_done_click(self):
        self.file_formatter.close()

    def formatter_file_changed(self):
        return

    def formatter_skip_click(self):
        return

    def test(self,output=True):
        return
