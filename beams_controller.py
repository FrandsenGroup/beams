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
        self.BEAMS_view.run_display.isolate_button.released.connect(lambda: self.run_display_isolate())
        self.BEAMS_view.run_display.plot_all_button.released.connect(lambda: self.run_display_plot_all())
        self.BEAMS_view.run_display.inspect_file_button.released.connect(lambda: self.run_display_inspect_file())
        self.BEAMS_view.run_display.inspect_hist_button.released.connect(lambda: self.run_display_inspect_hist())
        self.BEAMS_view.run_display.run_titles.currentTextChanged.connect(lambda: self.run_display_update())
        self.BEAMS_view.run_display.color_choices.currentIndexChanged.connect(lambda: self.run_display_color_change())

        self.BEAMS_view.file_manager.import_button.released.connect(lambda: self.file_manager_import())
        self.BEAMS_view.file_manager.write_button.released.connect(lambda: self.file_manager_write())
        self.BEAMS_view.file_manager.plot_button.released.connect(lambda: self.file_manager_plot())

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
        self.BEAMS_view.add_data_act.triggered.connect(lambda: self.file_manager_import())
        self.BEAMS_view.format_act.triggered.connect(lambda: self.launch_formatter())

    def run_display_isolate(self):
        '''Handles the user clicking the "Isolate" button'''
        self.plot_panel_clear()
        self.plot_panel_plot_runs(filename=self.BEAMS_view.run_display.run_titles.currentText())

    def run_display_plot_all(self):
        self.plot_panel_clear(plot=3)
        self.plot_panel_plot_runs(filename=None,plot=3,slider_moving=False)

    def run_display_inspect_file(self):
        self.file_display = beams_view.FileDisplayUI(filename=self.BEAMS_view.run_display.run_titles.currentText())
        self.file_display.show()

    def run_display_inspect_hist(self):
        hist_display = beams_view.PlotPanel(center=False)

        histogram = self.BEAMS_view.run_display.histograms.currentText()
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].retrieve_histogram_data()

        # Why is a bar chart so much slower then just plotting???
        hist_display.canvas_hist.axes_hist.plot(self.BEAMS_model.run_list[run_index].histogram_data[histogram].values,linestyle='None',marker="s")

        # self.hist_display.show()
        del self.BEAMS_model.run_list[run_index].histogram_data

    def run_display_update(self):
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        if run_index != -1:
            self.BEAMS_view.run_display.color_choices.setCurrentText(self.BEAMS_model.run_list[run_index].color)
            if self.BEAMS_model.is_BEAMS(self.BEAMS_view.run_display.run_titles.currentText()):
                self.BEAMS_view.run_display.histograms.clear()
                self.BEAMS_view.run_display.histograms.addItems(['Front','Back','Right','Left'])
                self.BEAMS_view.run_display.histograms.setEnabled(True)
                self.BEAMS_view.run_display.inspect_hist_button.setEnabled(True)

    def run_display_populate(self,filenames=None):
        if len(filenames) > 0:
            self.BEAMS_view.run_display.run_titles.clear()
            self.BEAMS_view.run_display.run_titles.addItems(filenames)
            self.BEAMS_view.run_display.color_choices.addItems(self.BEAMS_model.used_colors)
            self.BEAMS_view.run_display.color_choices.addItems(self.BEAMS_model.color_options)
            self.run_display_update()
            self.run_display_enable(isEnabled=True)
        else:
            self.BEAMS_view.run_display.run_titles.clear()
            self.run_display_enable(isEnabled=False)

    def run_display_enable(self,isEnabled=False):
        if not isEnabled:
            self.BEAMS_view.run_display.run_titles.addItem("No Runs Plotted")
            self.BEAMS_view.run_display.histograms.addItem("None")
            self.BEAMS_view.run_display.histograms.setEnabled(False)
            self.BEAMS_view.run_display.inspect_hist_button.setEnabled(False)
        self.BEAMS_view.run_display.color_choices.setEnabled(isEnabled)
        self.BEAMS_view.run_display.isolate_button.setEnabled(isEnabled)
        self.BEAMS_view.run_display.inspect_file_button.setEnabled(isEnabled)
        self.BEAMS_view.run_display.plot_all_button.setEnabled(isEnabled)

    def run_display_color_change(self):
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].color = self.BEAMS_view.run_display.color_choices.currentText()
        self.plot_panel_clear()
        self.plot_panel_plot_runs()

    def file_manager_import(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.BEAMS_view,'Add file','/home')[0]
        self.BEAMS_model.filenames.update(filenames) 
        for filename in filenames:
            file_root = os.path.split(filename)[1]
            file_item = QtWidgets.QListWidgetItem(file_root,self.BEAMS_view.file_manager.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

    def file_manager_write(self):
        print("Write button currently has no functionality ... ")

    def file_manager_plot(self):
        # Create a set of the checked filenames from the file manager panel.
        beams_checked_items = set()
        for index in range(self.BEAMS_view.file_manager.file_list.count()):
            if self.BEAMS_view.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                beams_checked_items.add(self.BEAMS_view.file_manager.file_list.item(index).text())

        # Use the check_files and read_files function from the BEAMSModel class
        beams_files,non_beams_files = self.BEAMS_model.check_files(beams_checked_items)
        self.BEAMS_model.read_files(beams_files)
        if non_beams_files:
            self.launch_formatter(filenames=non_beams_files)
        
        # Plot the runs
        self.plot_panel_clear(plot=3)
        self.plot_panel_plot_runs(filename=None,plot=3,slider_moving=False) # FIXME I think there is some intricacy with default paramaters. Test this.
        self.run_display_populate(filenames=self.BEAMS_model.current_read_files) # FIXME

    def plot_panel_clear(self,plot=3):
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
            
    def plot_panel_plot_runs(self,filename=None,plot=3,slider_moving=False):
        if not filename: # If no specific plot specified
            for run in self.BEAMS_model.run_list:
                if plot == 1 or plot == 3:
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_one.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_one.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_one.text())
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',\
                        marker='.',mfc=run.color,mec=run.color,ecolor=run.color)
                    self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')
                if plot == 2 or plot == 3:
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_two.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_two.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_two.text())
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',\
                        marker='.',mfc=run.color,mec=run.color,ecolor=run.color)
                    self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')
        else: 
            run = self.BEAMS_model.run_list[self.BEAMS_model.index_from_filename(filename=filename)]
            self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
            self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',\
                mfc=run.color,mec=run.color,ecolor=run.color)
            self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')
            self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
            self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle='None',marker='.',\
                mfc=run.color,mec=run.color,ecolor=run.color)
            self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')

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
                self.plot_panel_clear(plot=plot)
                self.plot_panel_plot_runs(plot=plot,slider_moving=slider_moving)
        else:
            self.plot_panel_clear(plot=plot)
            self.plot_panel_plot_runs(plot=plot,slider_moving=slider_moving)

            if xlims_changed:
                self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_two.text()))

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
        self.file_formatter.check_rhist.stateChanged.connect(lambda: self.formatter_checkbox(dtype="rhist"))
        self.file_formatter.check_time.stateChanged.connect(lambda: self.formatter_checkbox(dtype="time"))
        self.file_formatter.check_uncertain.stateChanged.connect(lambda: self.formatter_checkbox(dtype="uncertain"))

        self.file_formatter.apply_button.released.connect(lambda: self.formatter_apply_click(apply_all=False))
        self.file_formatter.apply_all_button.released.connect(lambda: self.formatter_apply_click(apply_all=True))
        self.file_formatter.done_button.released.connect(lambda: self.formatter_done_click())
        self.file_formatter.file_list.currentIndexChanged.connect(lambda: self.formatter_file_changed())
        self.file_formatter.skip_button.released.connect(lambda: self.formatter_skip_click())
        self.file_formatter.inspect_column.released.connect(lambda: self.formatter_inspect_column())

    def formatter_checkbox(self,dtype=None):
        if dtype == "asym":
            if self.file_formatter.spin_asym.isEnabled():
                self.file_formatter.spin_asym.setEnabled(False)
                self.file_formatter.selected_columns.remove('Asymmetry')
            else:
                self.file_formatter.spin_asym.setEnabled(True)
                self.file_formatter.selected_columns.append('Asymmetry')
                
        elif dtype == "bhist":
            if self.file_formatter.spin_bhist.isEnabled():
                self.file_formatter.spin_bhist.setEnabled(False)
                self.file_formatter.selected_columns.remove('Back')
            else:
                self.file_formatter.spin_bhist.setEnabled(True)
                self.file_formatter.selected_columns.append('Back')
                
        elif dtype == "fhist":
            if self.file_formatter.spin_fhist.isEnabled():
                self.file_formatter.spin_fhist.setEnabled(False)
                self.file_formatter.selected_columns.remove('Front')
            else:
                self.file_formatter.spin_fhist.setEnabled(True)
                self.file_formatter.selected_columns.append('Front')
                
        elif dtype == "lhist":
            if self.file_formatter.spin_lhist.isEnabled():
                self.file_formatter.spin_lhist.setEnabled(False)
                self.file_formatter.selected_columns.remove('Left')
            else:
                self.file_formatter.spin_lhist.setEnabled(True)
                self.file_formatter.selected_columns.append('Left')
                
        elif dtype == "rhist":
            if self.file_formatter.spin_rhist.isEnabled():
                self.file_formatter.spin_rhist.setEnabled(False)
                self.file_formatter.selected_columns.remove('Right')
            else:
                self.file_formatter.spin_rhist.setEnabled(True)
                self.file_formatter.selected_columns.append('Right')
                
        elif dtype == "time":
            if self.file_formatter.spin_time.isEnabled():
                self.file_formatter.spin_time.setEnabled(False)
                self.file_formatter.selected_columns.remove('Time')
            else:
                self.file_formatter.spin_time.setEnabled(True)
                self.file_formatter.selected_columns.append('Time')
                
        else:
            if self.file_formatter.spin_uncertain.isEnabled():
                self.file_formatter.spin_uncertain.setEnabled(False)
                self.file_formatter.selected_columns.remove('Uncertainty')
            else:
                self.file_formatter.spin_uncertain.setEnabled(True)
                self.file_formatter.selected_columns.append('Uncertainty')
                
        
        self.file_formatter.columns.clear()
        self.file_formatter.columns.addItems(self.file_formatter.selected_columns)

        if(self.file_formatter.check_fhist.isChecked() and self.file_formatter.check_bhist.isChecked()) or \
            (self.file_formatter.check_lhist.isChecked() and self.file_formatter.check_rhist.isChecked()):
            self.file_formatter.bin_input.setEnabled(True)
            self.file_formatter.initial_t.setEnabled(True)
        else:
            self.file_formatter.bin_input.setEnabled(False)
            self.file_formatter.initial_t.setEnabled(False)

    def formatter_apply_click(self,apply_all=False):
        self.formatter_create_section_dict()
        if not apply_all:
            fformat = self.BEAMS_model.check_unrecognized_format(sections=self.data_sections,filenames=[self.file_formatter.file_list.currentText()],\
                t0=self.file_formatter.initial_t.text(),header_rows=self.file_formatter.spin_header.value())
        else:
            fformat = self.BEAMS_model.check_unrecognized_format(sections=self.data_sections,filenames=self.file_formatter.filenames,\
                t0=self.file_formatter.initial_t.text(),header_rows=self.file_formatter.spin_header.value())

        if fformat == 'EB':
            self.error_message(error_type='EB')
        elif fformat == 'EH':
            self.error_message(error_type='EH')
        elif fformat == 'EC':
            self.error_message(error_type='EC',sections=self.data_sections)
        elif fformat == 'EF':
            self.error_message(error_type='EF')
        else:
            if not apply_all:
                self.BEAMS_model.read_unrecognized_format(sections=self.data_sections,filenames=[self.file_formatter.file_list.currentText()],\
                    header_rows=self.file_formatter.spin_header.value(),fformat=fformat)
                self.BEAMS_model.current_read_files.add(self.file_formatter.file_list.currentText())
            else:
                self.BEAMS_model.read_unrecognized_format(sections=self.data_sections,filenames=self.file_formatter.filenames,\
                    header_rows=self.file_formatter.spin_header.value(),fformat=fformat)
                self.BEAMS_model.current_read_files.update(self.file_formatter.filenames)


    def formatter_create_section_dict(self):
        self.data_sections = dict()
        if self.file_formatter.check_asym.isChecked():
            self.data_sections['Asymmetry'] = self.file_formatter.spin_asym.value() 
        if self.file_formatter.check_bhist.isChecked():
            self.data_sections['Back'] = self.file_formatter.spin_bhist.value()
        if self.file_formatter.check_error.isChecked(): 
            self.data_sections['Error'] = self.file_formatter.spin_error.value()
        if self.file_formatter.check_fhist.isChecked(): 
            self.data_sections['Front'] = self.file_formatter.spin_fhist.value() 
        if self.file_formatter.check_lhist.isChecked():
            self.data_sections['Left'] = self.file_formatter.spin_lhist.value() 
        if self.file_formatter.check_rhist.isChecked():
            self.data_sections['Right'] = self.file_formatter.spin_rhist.value() 
        if self.file_formatter.check_time.isChecked():
            self.data_sections['Time'] = self.file_formatter.spin_time.value() 
        if self.file_formatter.check_uncertain.isChecked():
            self.data_sections['Uncertainty'] = self.file_formatter.spin_uncertain.value() 

    def formatter_done_click(self):
        self.file_formatter.close()
        self.plot_panel_plot_runs()

    def formatter_file_changed(self):
        self.file_formatter.set_intitial_states()
        if self.file_formatter.file_list.currentText():
            self.file_formatter.file_display.setPlainText(open(self.file_formatter.file_list.currentText()).read())

    def formatter_skip_click(self):
        self.file_formatter.file_list.removeItem(self.file_formatter.file_list.currentIndex())

    def formatter_inspect_column(self):
        self.formatter_create_section_dict()
        self.BEAMS_model.inspect_unrecognized_column(filename=self.file_formatter.file_list.currentText(),\
            column=self.data_sections[self.file_formatter.columns.currentText()],header_rows=self.file_formatter.spin_header.value())
        hist_display = beams_view.PlotPanel(center=False)
        hist_display.canvas_hist.axes_hist.plot(self.BEAMS_model.column_data.values,linestyle='None',marker="s")
        del self.BEAMS_model.column_data

    def error_message(self,error_type=None,sections=None):
        error_dialog = beams_view.ErrorMessageUI(error_type=error_type,sections=sections)
        error_dialog.show()

    def test(self,output=True,GUI=False):
        # FORMATTER TEST CASES
        # Inspect a column that doesn't exist
        return
