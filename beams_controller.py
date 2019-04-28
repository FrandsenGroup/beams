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
    '''Accepts input and converts it to commands for the model or view.'''
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

        self.BEAMS_view.plot_editor.input_xmax_one.returnPressed.connect(lambda: self.editor_paramter_change(plot=1,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmax_two.returnPressed.connect(lambda: self.editor_paramter_change(plot=2,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmin_one.returnPressed.connect(lambda: self.editor_paramter_change(plot=1,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_xmin_two.returnPressed.connect(lambda: self.editor_paramter_change(plot=2,slider_moving=False,xlims_changed=True))
        self.BEAMS_view.plot_editor.input_slider_one.returnPressed.connect(lambda: self.editor_paramter_change(plot=1,slider_moving=False,bin_changed=True))
        self.BEAMS_view.plot_editor.input_slider_two.returnPressed.connect(lambda: self.editor_paramter_change(plot=2,slider_moving=False,bin_changed=True))
        self.BEAMS_view.plot_editor.slider_one.sliderMoved.connect(lambda: self.editor_paramter_change(plot=1,slider_moving=True))
        self.BEAMS_view.plot_editor.slider_two.sliderMoved.connect(lambda: self.editor_paramter_change(plot=2,slider_moving=True))
        self.BEAMS_view.plot_editor.slider_one.sliderReleased.connect(lambda: self.editor_paramter_change(plot=1,slider_moving=False))
        self.BEAMS_view.plot_editor.slider_two.sliderReleased.connect(lambda: self.editor_paramter_change(plot=2,slider_moving=False))
        self.BEAMS_view.plot_editor.check_uncertain.stateChanged.connect(lambda: self.editor_show_uncertainty())
        self.BEAMS_view.plot_editor.check_annotation.stateChanged.connect(lambda: self.editor_show_annotations())
        self.BEAMS_view.plot_editor.check_plot_lines.stateChanged.connect(lambda: self.editor_show_plot_lines())

        self.BEAMS_view.exit_act.triggered.connect(QtWidgets.qApp.quit)
        self.BEAMS_view.add_data_act.triggered.connect(lambda: self.file_manager_import())
        self.BEAMS_view.format_act.triggered.connect(lambda: self.launch_formatter())

    def run_display_isolate(self):
        '''Plots only the user specified run'''
        self.plot_panel_clear()
        self.plot_panel_plot_runs(filename=self.BEAMS_view.run_display.run_titles.currentText())

    def run_display_plot_all(self):
        '''Plots all runs currently in the model'''
        self.plot_panel_clear(plot=3)
        self.plot_panel_plot_runs(filename=None,plot=3,slider_moving=False)

    def run_display_inspect_file(self):
        '''Opens up a window displaying the user specified file'''
        self.file_display = beams_view.FileDisplayUI(filename=self.BEAMS_view.run_display.run_titles.currentText())
        self.file_display.show()

    def run_display_inspect_hist(self):
        '''Opens up a figure displaying the user specified histogram'''
        hist_display = beams_view.PlotPanel(center=False)

        histogram = self.BEAMS_view.run_display.histograms.currentText()
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].retrieve_histogram_data()

        # Why is a bar chart so much slower then just plotting??? Working on figuring out how to do a faster bar chart.
        hist_display.canvas_hist.axes_hist.plot(self.BEAMS_model.run_list[run_index].histogram_data[histogram].values,linestyle='None',marker="s")

        del self.BEAMS_model.run_list[run_index].histogram_data

    def run_display_update(self):
        '''Updates the data displayed on Run Display when user chooses a different file'''
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        if run_index != -1:
            self.BEAMS_view.run_display.color_choices.setCurrentText(self.BEAMS_model.run_list[run_index].color)
            if self.BEAMS_model.is_BEAMS(self.BEAMS_view.run_display.run_titles.currentText()):
                self.BEAMS_view.run_display.histograms.clear()
                self.BEAMS_view.run_display.histograms.addItems(['Front','Back','Right','Left']) 
                self.BEAMS_view.run_display.histograms.setEnabled(True)
                self.BEAMS_view.run_display.inspect_hist_button.setEnabled(True)

    def run_display_populate(self,filenames=None):
        '''Populates the Run Display with all the filenames and relevent data for each currently plotted run'''
        if len(filenames) > 0:
            self.BEAMS_view.run_display.run_titles.clear()
            self.BEAMS_view.run_display.run_titles.addItems(filenames)
            self.BEAMS_view.run_display.color_choices.addItems(self.BEAMS_model.used_colors)
            self.BEAMS_view.run_display.color_choices.addItems(self.BEAMS_model.color_options)
            self.run_display_update()
            self.run_display_enable(isEnabled=True)
        else: # If no runs are plotted we want to disable the Run Display.
            self.BEAMS_view.run_display.run_titles.clear()
            self.run_display_enable(isEnabled=False)

    def run_display_enable(self,isEnabled=False):
        '''Enables the run display interface when there are runs currently plotted'''
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
        '''Updates the object for that run with correct color and re-plots the runs'''
        run_index = self.BEAMS_model.index_from_filename(self.BEAMS_view.run_display.run_titles.currentText())
        self.BEAMS_model.run_list[run_index].color = self.BEAMS_view.run_display.color_choices.currentText()

        self.plot_panel_clear()
        self.plot_panel_plot_runs()

    def file_manager_import(self):
        '''Opens dialog for user to specify file(s) to add to the file manager, no data is added to the model besides the filenames'''
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.BEAMS_view,'Add file','/home')[0]
        self.BEAMS_model.filenames.update(filenames) 
        for filename in filenames:  # Adds only the filename root (i.e. 0065156.dat) to the File Manager Panel
            file_root = os.path.split(filename)[1]
            file_item = QtWidgets.QListWidgetItem(file_root,self.BEAMS_view.file_manager.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

    def file_manager_write(self):
        '''Allows user to export currently binned data to a .dat file'''
        print("Write button currently has no functionality ... ")

    def file_manager_plot(self):
        '''Reads in runs from specified files, plots those runs, and updates the run display'''
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
        '''Clears the plots (only the ones that need to be, i.e. left (1), right (2) or both (3))'''
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
        '''Plots all the runs that are currently stored in the model'''
        if not filename: # If no specific plot specified
            for run in self.BEAMS_model.run_list:
                if plot == 1 or plot == 3:
                    # Bin the data
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_one.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_one.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_one.text())
                    # Plot set x limits on axes
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                    # Plot on the time domain
                    self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,\
                        linestyle=self.BEAMS_view.plot_panel.linestyle,marker='.',color=run.color)
                    # Plot on the frequency domain
                    self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')

                if plot == 2 or plot == 3:
                    # Same process as above.
                    run.bin_data(slider_moving=slider_moving,bin_size=self.BEAMS_view.plot_editor.slider_two.value(),\
                        xmin=self.BEAMS_view.plot_editor.input_xmin_two.text(),xmax=self.BEAMS_view.plot_editor.input_xmax_two.text())
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                        float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
                    self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,\
                        linestyle=self.BEAMS_view.plot_panel.linestyle,marker='.',color=run.color)
                    self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')

        else: 
            # Same process as above but for only the file specified
            run = self.BEAMS_model.run_list[self.BEAMS_model.index_from_filename(filename=filename)]
            self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
            self.BEAMS_view.plot_panel.canvas_one.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle=self.BEAMS_view.plot_panel.linestyle,\
                marker='.',color=run.color)
            self.BEAMS_view.plot_panel.canvas_one.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')
            self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                float(self.BEAMS_view.plot_editor.input_xmax_two.text()))
            self.BEAMS_view.plot_panel.canvas_two.axes_time.errorbar(run.new_times,run.new_asymmetry,run.new_uncertainty,linestyle=self.BEAMS_view.plot_panel.linestyle,\
                marker='.',color=run.color)
            self.BEAMS_view.plot_panel.canvas_two.axes_freq.plot(run.x_smooth,run.y_smooth**2,mfc=run.color,mec=run.color,color=run.color,marker='.')

        # Resets the styles on the plots (they are lost when they are cleared)
        self.BEAMS_view.plot_panel.canvas_one.set_style()
        self.BEAMS_view.plot_panel.canvas_two.set_style()

    def editor_show_uncertainty(self):
        '''Toggles the errorbars on the plots'''
        if not self.BEAMS_view.plot_editor.check_uncertain.isChecked():
            for run in self.BEAMS_model.run_list:
                run.uncertainty.fill(0)
            self.plot_panel_clear()
            self.plot_panel_plot_runs()
        else:
            for run in self.BEAMS_model.run_list:
                run.re_calculate_uncertainty()
            self.plot_panel_clear()
            self.plot_panel_plot_runs()

    def editor_show_annotations(self):
        '''Toggles the annotations on the plots'''
        return

    def editor_show_plot_lines(self):
        '''Toggles the lines connecting datapoints on plots on and off'''
        if self.BEAMS_view.plot_editor.check_plot_lines.isChecked():
            self.BEAMS_view.plot_panel.linestyle = '-'
            self.plot_panel_clear()
            self.plot_panel_plot_runs()
        else:
            self.BEAMS_view.plot_panel.linestyle = 'None'
            self.plot_panel_clear()
            self.plot_panel_plot_runs()

    def editor_paramter_change(self,plot=3,slider_moving=False,xlims_changed=False,bin_changed=False):
        '''Updates the plots when the user changes a parameter relevant to graphing (i.e. bin size)'''
        if bin_changed: # Re-bin data if the bin size was changed
            self.BEAMS_view.plot_editor.slider_one.setValue(float(self.BEAMS_view.plot_editor.input_slider_one.text())) if plot == 1 \
                else self.BEAMS_view.plot_editor.slider_two.setValue(float(self.BEAMS_view.plot_editor.input_slider_two.text()))
        if slider_moving: # Only shows changes in the time domain while the slider is moving
            self.BEAMS_view.plot_editor.input_slider_one.setText(str(self.BEAMS_view.plot_editor.slider_one.value())) if plot == 1 \
                else self.BEAMS_view.plot_editor.input_slider_two.setText(str(self.BEAMS_view.plot_editor.slider_two.value()))
            mod_value = self.BEAMS_view.plot_editor.slider_one.value()%5 if plot == 1 else self.BEAMS_view.plot_editor.slider_two.value()%5  
            if mod_value == 0:
                self.plot_panel_clear(plot=plot)
                self.plot_panel_plot_runs(plot=plot,slider_moving=slider_moving)
        else: # Recalculate and plot in both the time and frequency domain
            self.plot_panel_clear(plot=plot)
            self.plot_panel_plot_runs(plot=plot,slider_moving=slider_moving)

            if xlims_changed:
                self.BEAMS_view.plot_panel.canvas_one.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_one.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_one.text()))
                self.BEAMS_view.plot_panel.canvas_two.axes_time.set_xlim(float(self.BEAMS_view.plot_editor.input_xmin_two.text()),\
                    float(self.BEAMS_view.plot_editor.input_xmax_two.text()))

    def launch_formatter(self,filenames=None):
        '''Creates an instance of the formatter user interface for unfamiliar file formats'''
        self.file_formatter = beams_view.FileFormatterUI(filenames=filenames)
        self.set_formatter_events()
        self.file_formatter.file_display.setPlainText(open(filenames[0]).read())
        self.file_formatter.show()

    def set_formatter_events(self):
        '''Sets events for the FileFormatterUI'''
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
        '''Changes the state of the spin boxes and input boxes when checkboxes are checked'''
        # This first section disables a spin box when the checkbox next to it is unchecked and vice versa
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
                
        # Keeps track of which column descriptors are checked
        self.file_formatter.columns.clear()
        self.file_formatter.columns.addItems(self.file_formatter.selected_columns)

        # If the front and back or left and right histograms are checked the user is able to specify binsize
        # and the bin area where positrons are first beginning to be detected.
        if(self.file_formatter.check_fhist.isChecked() and self.file_formatter.check_bhist.isChecked()) or \
            (self.file_formatter.check_lhist.isChecked() and self.file_formatter.check_rhist.isChecked()):
            self.file_formatter.bin_input.setEnabled(True)
            self.file_formatter.initial_t.setEnabled(True)
        else:
            self.file_formatter.bin_input.setEnabled(False)
            self.file_formatter.initial_t.setEnabled(False)

    def formatter_apply_click(self,apply_all=False):
        '''Checks the user specified format and gives appropriate errors or plots the runs'''
        # Checks user specified format with files for possible errors
        self.formatter_create_section_dict()
        if not apply_all: # Applies to all non-BEAMS files or to only the currently selected one.
            fformat = self.BEAMS_model.check_unrecognized_format(sections=self.data_sections,filenames=[self.file_formatter.file_list.currentText()],\
                t0=self.file_formatter.initial_t.text(),header_rows=self.file_formatter.spin_header.value())
        else:
            fformat = self.BEAMS_model.check_unrecognized_format(sections=self.data_sections,filenames=self.file_formatter.filenames,\
                t0=self.file_formatter.initial_t.text(),header_rows=self.file_formatter.spin_header.value())

        # Launches the appropriate error window or plots the runs with the user specified format.
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
        '''Creates a dictionary of the columns as keys and their column number as values'''
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
        '''Closes the formatter, plots all runs in the model and updates the run display'''
        self.file_formatter.close()
        self.plot_panel_clear()
        self.plot_panel_plot_runs()
        self.run_display_populate(filenames=self.BEAMS_model.current_read_files)

    def formatter_file_changed(self):
        '''Resets the formatter input areas to their initial states when a new file is chosen and updates the file display'''
        self.file_formatter.set_intitial_states()
        if self.file_formatter.file_list.currentText():
            self.file_formatter.file_display.setPlainText(open(self.file_formatter.file_list.currentText()).read())

    def formatter_skip_click(self):
        '''Removes the current non-BEAMS file from the formatter'''
        # File is still checked on the file manager though, feature or bug?
        self.file_formatter.file_list.removeItem(self.file_formatter.file_list.currentIndex())

    def formatter_inspect_column(self):
        '''Opens up a figure displaying the user specified histogram'''
        self.formatter_create_section_dict()
        self.BEAMS_model.inspect_unrecognized_column(filename=self.file_formatter.file_list.currentText(),\
            column=self.data_sections[self.file_formatter.columns.currentText()],header_rows=self.file_formatter.spin_header.value())
        hist_display = beams_view.PlotPanel(center=False)
        hist_display.canvas_hist.axes_hist.plot(self.BEAMS_model.column_data.values,linestyle='None',marker="s")
        del self.BEAMS_model.column_data

    def error_message(self,error_type=None,sections=None):
        '''Opens up an error message based on error type from program'''
        error_dialog = beams_view.ErrorMessageUI(error_type=error_type,sections=sections)
        error_dialog.show()

    def test(self,output=True,GUI=False):
        '''Function for automated running through test cases'''
        return
