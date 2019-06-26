# BEAMS specific modules
import BeamsViews
import BeamsModel
import BeamsUtility

# Standard Library modules
import sys
import os
import subprocess
import time
import pickle
import threading

# Installed modules
from PyQt5 import QtWidgets, QtCore
import matplotlib.pyplot as plt
import numpy as np


class ProgramController:
    """ Main controller responsible for initializing and starting the application. """
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)

        # Initialize the model
        # Note: The model holds most application-relevant data and the 'business logic' of the application.
        self.model = BeamsModel.BEAMSModel()

        # Initialize all the GUIs with their controllers
        # Note: The controllers are responsible for handling user input on the GUIs. The GUIs will update based on
        # changes in the model
        self.main_window_v = BeamsViews.MainGUIWindow()  # Builds Main Window GUI with all the connected panels
        self.set_callbacks()

        self.file_manager_controller = FileManagerController(file_manager_panel=self.main_window_v.file_manager,
                                                             model=self.model, parent=self)
        self.plot_editor_controller = PlotController(plot_editor_panel=self.main_window_v.plot_editor,
                                                     plot_panel=self.main_window_v.plot_panel,
                                                     model=self.model, parent=self)
        self.run_display_controller = RunDisplayController(run_display_panel=self.main_window_v.run_display,
                                                           model=self.model, parent=self)

        self.main_window_v.show()
        sys.exit(self.app.exec_())

    def set_callbacks(self):
        self.main_window_v.save_session_act.triggered.connect(self.save_session)
        self.main_window_v.open_session_act.triggered.connect(self.open_session)
        self.main_window_v.add_data_act.triggered.connect(self.add_data_file)
        self.main_window_v.format_act.triggered.connect(self.format_files)
        self.main_window_v.exit_act.triggered.connect(sys.exit)

    @staticmethod
    def format_files():
        BeamsViews.FileFormatterUI()

    def add_data_file(self):
        """ Prompts the user for and stores full file paths in model.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        # Open a dialog to prompt users for file(s)
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.main_window_v, 'Add file', '/home')[0]

        for filename in filenames:  # Adds only the filename root (i.e. 0065156.dat) to the File Manager Panel
            file_root = os.path.split(filename)[1]
            self.model.update_file_list(file_path=filename, file_name=file_root)  # Store as dict in model

    def save_session(self):
        """ Prompts the user for a file path to save the current run data to and uses pickle to dump the data. """
        saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.main_window_v, 'Specify file',
                                                                os.getcwd(), 'BEAMS(*.beams)')[0]
        if not saved_file_path:
            return

        saved_file = open(saved_file_path, 'wb')
        pickle.dump(self.model.run_list, saved_file)
        saved_file.close()

    def open_session(self):
        """ Prompts the user for a .beams file (old session) to read in with pickle. """
        if self.model.run_list:
            message = '\t\tWould you like to save your current session before closing?\t\t'
            BeamsViews.PermissionsMessageUI(message, pos_function=self.save_session)

        open_file_path = QtWidgets.QFileDialog.getOpenFileNames(self.main_window_v, 'Choose previous session',
                                                                os.getcwd(), 'BEAMS(*.beams)')
        if open_file_path[0]:
            open_file_path = open_file_path[0][0]
        else:
            return

        if os.path.splitext(open_file_path)[1] != '.beams':
            message = '\t\t\tInvalid file chosen\t\t\t'
            BeamsViews.ErrorMessageUI(message)
            return

        open_file = open(open_file_path, 'rb')

        try:
            data = pickle.load(open_file)
        except pickle.UnpicklingError:
            message = '\t\t\tCould not read in data from {}\t\t\t'.format(open_file_path)
            BeamsViews.ErrorMessageUI(message)
        else:
            self.model.open_save_session(data)

        open_file.close()


class FileManagerController:
    """ Controller responsible for managing user input on the File Manager Panel. """
    def __init__(self, file_manager_panel=None, model=None, parent=None):
        """ Initializes the FileManagerController and sets callbacks for the GUI"""

        if not file_manager_panel or not model or not parent:  # Raise error if not properly instantiated
            raise AttributeError('FileManagerController did not receive all necessary inputs.')

        self.file_manager = file_manager_panel
        self.model = model
        self.program_controller = parent
        self.formats = {}
        self.popup = None

        self.model.observers[BeamsModel.FILE_CHANGED].append(self)

        self.set_callbacks()

    def __repr__(self):
        return 'FileManagerController(file_manager_panel={}, model={}, parent={})'\
            .format(self.file_manager, self.model, self.program_controller)

    def __str__(self):
        return 'File Manager Controller'

    def set_callbacks(self):
        """ Sets the callbacks for events in the File Manager Panel. """
        self.file_manager.import_button.released.connect(lambda: self.b_add())
        self.file_manager.write_button.released.connect(lambda: self.b_write())
        self.file_manager.plot_button.released.connect(lambda: self.b_plot())
        self.file_manager.convert_button.released.connect(lambda: self.b_convert())
        self.file_manager.remove_button.released.connect(lambda: self.b_remove())
        self.file_manager.select_all.stateChanged.connect(lambda: self.c_select_all())

    def c_select_all(self):
        """ Selects or deselects all files based on the checked state of the select all checkbox. """
        for index in range(self.file_manager.file_list.count()):
            if self.file_manager.select_all.checkState():
                self.file_manager.file_list.item(index).setCheckState(QtCore.Qt.Checked)
            else:
                self.file_manager.file_list.item(index).setCheckState(QtCore.Qt.Unchecked)

    def b_remove(self):
        """ Removes the currently selected files from the file manager. """
        def remove():
            for file_root in selected_files:
                for index in range(self.file_manager.file_list.count()):
                    if file_root == self.file_manager.file_list.item(index).text():
                        self.file_manager.file_list.takeItem(index)
                        self.model.update_file_list(file_root, remove=True)
                        break

        selected_files = self.get_selected_files()
        message = 'Are you sure you would like to remove all currently selected files?'
        BeamsViews.PermissionsMessageUI(message, pos_function=remove)

    def b_add(self):
        """ Prompts the user for and stores full file paths in model.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        # Open a dialog to prompt users for file(s)
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.file_manager, 'Add file', '/home')[0]

        for filename in filenames:  # Adds only the filename root (i.e. 0065156.dat) to the File Manager Panel
            file_root = os.path.split(filename)[1]
            self.model.update_file_list(file_path=filename, file_name=file_root)  # Store as dict in model

    def b_plot(self):
        """ Sends all checked files to the model to read.
            Note: If the model creates or alters current RunData objects the PlotPanelController will be notified.
            See update() in PlotPanelController class. """
        # Get all checked filenames then get the full file paths that are stored in the model.
        filenames = self.get_selected_files()
        checked_items = [self.model.all_full_filepaths[file_root] for file_root in filenames]

        beams_files, other_dat, msr_files, bad_files = BeamsUtility.check_files(checked_items)

        if msr_files:  # Users must give permission to read and convert .msr files to .dat
            message = 'MUD Files selected, would you like them to be converted?'
            BeamsViews.PermissionsMessageUI(message, pos_function=self.b_convert)

        elif bad_files:  # Throw error message for unsupported file types
            message = 'The following files are not supported or cannot be found/opened: \n{}'.format(
                [(filename + '\n') for filename in bad_files])
            BeamsViews.ErrorMessageUI(message)

        elif beams_files or other_dat:  # Collect the formats of each file to send to the model.
            self.prompt_formats(beams_files, other_dat)

        else:  # No files were selected, inform the user.
            BeamsViews.ErrorMessageUI(error_message='No files selected.')

    def b_convert(self):
        """ Converts currently selected .msr files to .dat files and saves them in the current directory.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        def remove_msr():
            for file_root in checked_items:
                if os.path.splitext(file_root)[1] == '.msr':
                    for index in range(self.file_manager.file_list.count()):
                        if file_root == self.file_manager.file_list.item(index).text():
                            self.file_manager.file_list.takeItem(index)
                            self.model.update_file_list(file_root, remove=True)
                            break

        checked_items = self.get_selected_files()
        for file in checked_items:
            full_file = self.model.all_full_filepaths[file]  # Get full file path from the Model for each file

            if BeamsUtility.check_ext(full_file, '.msr'):  # Check extension of input and output files
                out_file = os.path.splitext(full_file)[0] + '.dat'
                out_file_root = os.path.split(out_file)[1]

                if BeamsUtility.convert_msr(full_file, out_file, flags=['-v', '-all']):  # Run the MUD executable on the .msr file
                    self.model.update_file_list(file_path=out_file, file_name=out_file_root)

                else:
                    # Usually occurs when their have been changes in the .msr files
                    message = 'Error reading .msr file.\n {} has possibly been corrupted.'.format(full_file)
                    BeamsViews.ErrorMessageUI(error_message=message)
                    return
        remove_msr()

    def b_write(self):
        """ Launches the Writer GUI.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        self.popup = WriterController(model=self.model, selected_files=self.get_selected_files())

    def prompt_formats(self, b_files, o_files):
        """ Collects the formats of the files user selected to plot. Formats for BEAMS files can
            all be obtained from the header. Launch Formatter to handle non-BEAMS files.

            Format Example: {filename: {header:value,bin_size:value, etc...}} -> format[filename][header] = value """
        if self.formats:
            self.formats.clear()

        # Formats from BEAMS formatted files can all be obtained from the header.
        if b_files:
            self.formats = {file: file_format for file, file_format in
                            zip(b_files, [BeamsUtility.get_header(file) for file in b_files])}

        # Users need to specify the formats of other .dat files through the FormatterGUI
        if o_files:
            self.popup = FormatterController(o_files, parent=self)
        else:
            # If no other .dat files to format we can prompt for histograms here.
            # Otherwise the FormatterController will launch the GUI when all formats are specified.
            self.prompt_histograms()

    def prompt_histograms(self):
        """ Launches PlotDataGUI to prompt users to specify which histograms should be used
            to calculate the asymmetry. Users can change this later in the RunDisplayPanel"""
        self.popup = PlotDataController(self.formats, model=self.model, plot=True)

    def get_selected_files(self):
        """ Returns all currently selected files in the File Manager Panel. """
        checked_items = set()
        for index in range(self.file_manager.file_list.count()):
            if self.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                checked_items.add(self.file_manager.file_list.item(index).text())
        return checked_items

    def get_all_files(self):
        """ Returns all files in the File Manager Panel. """
        files = set()
        for index in range(self.file_manager.file_list.count()):
            files.add(self.file_manager.file_list.item(index).text())
        return files

    def update_model(self):
        self.model.update_runs(self.formats)

    def update(self, signal=None):
        """ Called by the model when one of its FileManagerPanel-relevant attributes changes. """
        if signal == BeamsModel.FILE_CHANGED:  # Expects list of files to add the ListWidget in FileManagerPanel
            print("Updating File Manager")
            current_files = self.get_all_files()

            # First checks to see if any new files have been added to the model's file list. Adds them to the view.
            for file_root in self.model.all_full_filepaths.keys():
                if file_root not in current_files:
                    file_item = QtWidgets.QListWidgetItem(file_root, self.file_manager.file_list)
                    file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    file_item.setCheckState(QtCore.Qt.Unchecked)

            # Then checks to see if any files have been removed from the model's file list. Removes them from the view.
            for file_root in current_files:
                if file_root not in self.model.all_full_filepaths.keys():
                    for index in range(self.file_manager.file_list.count()):
                        if file_root == self.file_manager.file_list.item(index).text():
                            self.file_manager.file_list.takeItem(index)
                            break
        else:
            raise ValueError('Unexpected Signal from Model in {}'.format(self))


class PlotController:
    def __init__(self, plot_editor_panel=None, plot_panel=None, model=None, parent=None):
        """ Initializes the PlotEditorController and sets callbacks for the GUI"""

        if not plot_editor_panel or not model or not parent:  # Raise error if not properly instantiated
            raise AttributeError('PlotEditorController did not receive all necessary inputs.')

        self.plot_editor = plot_editor_panel
        self.plot_panel = plot_panel
        self.model = model
        self.program_controller = parent
        self.popup = None

        self.model.observers[BeamsModel.RUN_DATA_CHANGED].append(self)

        self.plot_parameters = {'XMinOne': self.plot_editor.input_xmin_one.text,
                                'XMinTwo': self.plot_editor.input_xmin_two.text,
                                'XMaxOne': self.plot_editor.input_xmax_one.text,
                                'XMaxTwo': self.plot_editor.input_xmax_two.text,
                                'YMinOne': self.plot_editor.input_ymin_one.text,
                                'YMinTwo': self.plot_editor.input_ymin_two.text,
                                'YMaxOne': self.plot_editor.input_ymax_one.text,
                                'YMaxTwo': self.plot_editor.input_ymax_two.text,
                                'BinInputOne': self.plot_editor.input_slider_one.text,
                                'BinInputTwo': self.plot_editor.input_slider_two.text,
                                'SliderOne': self.plot_editor.slider_one.value,
                                'SliderTwo': self.plot_editor.slider_two.value,
                                'YAutoOne': self.plot_editor.check_autoscale_one.isChecked,
                                'YAutoTwo': self.plot_editor.check_autoscale_two.isChecked,
                                'PlotLines': self.plot_editor.check_plot_lines.isChecked,
                                'Annotations': self.plot_editor.check_annotation.isChecked,
                                'Spline': self.plot_editor.check_spline.isChecked,
                                'Uncertainty': self.plot_editor.check_uncertain.isChecked,
                                'LineStyle': self.display_plot_lines}

        self.model.plot_parameters = self.plot_parameters
        self.set_callbacks()

    def __repr__(self):
        return 'PlotEditorController(plot_editor_panel={}, model={}, parent={})'\
            .format(self.plot_editor, self.model, self.program_controller)

    def __str__(self):
        return 'Plot Controller'

    def set_callbacks(self):
        """ Sets callbacks for events in the Plot Editor Panel. """
        self.plot_editor.input_xmin_one.returnPressed.connect(lambda: self.visual_data_change(plot=1))
        self.plot_editor.input_xmin_two.returnPressed.connect(lambda: self.visual_data_change(plot=2))
        self.plot_editor.input_xmax_one.returnPressed.connect(lambda: self.visual_data_change(plot=1))
        self.plot_editor.input_xmax_two.returnPressed.connect(lambda: self.visual_data_change(plot=2))
        self.plot_editor.input_ymin_one.returnPressed.connect(lambda: self.visual_data_change(plot=1))
        self.plot_editor.input_ymin_two.returnPressed.connect(lambda: self.visual_data_change(plot=2))
        self.plot_editor.input_ymax_one.returnPressed.connect(lambda: self.visual_data_change(plot=1))
        self.plot_editor.input_ymax_two.returnPressed.connect(lambda: self.visual_data_change(plot=2))
        self.plot_editor.input_slider_one.returnPressed.connect(lambda: self.bin_changed(moving=False, plot=1))
        self.plot_editor.input_slider_two.returnPressed.connect(lambda: self.bin_changed(moving=False, plot=2))
        self.plot_editor.slider_one.sliderMoved.connect(lambda: self.bin_changed(moving=True, plot=1))
        self.plot_editor.slider_two.sliderMoved.connect(lambda: self.bin_changed(moving=True, plot=2))
        self.plot_editor.slider_one.sliderReleased.connect(lambda: self.bin_changed(moving=False, plot=1))
        self.plot_editor.slider_two.sliderReleased.connect(lambda: self.bin_changed(moving=False, plot=2))
        self.plot_editor.check_annotation.stateChanged.connect(lambda: self.visual_data_change())
        self.plot_editor.check_plot_lines.stateChanged.connect(lambda: self.visual_data_change())
        self.plot_editor.check_uncertain.stateChanged.connect(lambda: self.visual_data_change())
        self.plot_editor.check_spline.stateChanged.connect(lambda: self.visual_data_change())
        self.plot_editor.check_autoscale_one.stateChanged.connect(lambda: self.check_y_limits(plot=1))
        self.plot_editor.check_autoscale_two.stateChanged.connect(lambda: self.check_y_limits(plot=2))
        self.plot_editor.save_button.released.connect(self.save_plots)

    def save_plots(self):
        self.popup = SavePlotController(canvases=[self.plot_panel.canvas_one, self.plot_panel.canvas_two])

    def bin_changed(self, moving=None, plot=None):
        """ Handles the bin size changing on either the slider or the text box. If one changes then
            the other is updated. """
        if moving:
            self.plot_editor.input_slider_one.setText(str(self.plot_parameters['SliderOne']()))
            self.plot_editor.input_slider_two.setText(str(self.plot_parameters['SliderTwo']()))
            if plot == 1:
                if self.plot_parameters['SliderOne']() % 5 is not 0:
                    return
            elif plot == 2:
                if self.plot_parameters['SliderTwo']() % 5 is not 0:
                    return
        else:
            self.plot_editor.slider_one.setValue(int(np.ceil(float(self.plot_parameters['BinInputOne']()))))
            self.plot_editor.slider_two.setValue(int(np.ceil(float(self.plot_parameters['BinInputTwo']()))))

        self.visual_data_change(plot=plot, moving=moving)

    def visual_data_change(self, plot=None, moving=False):
        """ Handles the changes made to Plot Editor widgets that necessitate recalculation of the Run Data. """
        start = time.time()
        if plot:
            if plot == 1:
                thread_one = threading.Thread(target=self.update_canvas_one(moving), daemon=True)
                thread_one.start()
            else:
                thread_two = threading.Thread(target=self.update_canvas_two(moving), daemon=True)
                thread_two.start()
        else:
            thread_one = threading.Thread(target=self.update_canvas_one(moving), daemon=True)
            thread_one.start()
            thread_two = threading.Thread(target=self.update_canvas_two(moving), daemon=True)
            thread_two.start()
        print('Moving on')
        self.display_y_limits()
        print('\tBinned and Plotted all runs in {} seconds'.format(time.time()-start))

    # @BeamsUtility.profile
    def update_canvas_one(self, moving=False):
        print('starting one')
        # FIXME this function has gotten a bit out of hand, refactor time!
        self.plot_panel.canvas_one.axes_time.clear()
        self.plot_panel.canvas_one.axes_freq.clear()

        max_y = -1
        min_y = 1
        max_mag = 0
        max_freq = 0

        self.plot_panel.canvas_one.axes_time.set_xlim(float(self.plot_parameters['XMinOne']()),
                                                      float(self.plot_parameters['XMaxOne']()))
        for run in self.model.run_list:
            if run.visibility:
                asymmetry, times, uncertainty = run.bin_data(final_bin_size=float(self.plot_parameters['BinInputOne']()),
                                                             slider_moving=moving)
                if moving:
                    self.plot_panel.canvas_one.axes_time.plot(times, asymmetry, color=run.color, linestyle='None',
                                                              marker='.')
                elif not self.plot_parameters['Uncertainty']():
                    frequencies, magnitudes = run.calculate_fft(asymmetry=asymmetry, times=times,
                                                                spline=self.plot_parameters['Spline']())
                    self.plot_panel.canvas_one.axes_time.plot(times, asymmetry, color=run.color, marker='.',
                                                              linestyle=self.plot_parameters['LineStyle']())
                    self.plot_panel.canvas_one.axes_freq.plot(frequencies, magnitudes, color=run.color, marker='.',
                                                              label=self.display_annotations(run))

                    max_mag = np.max(magnitudes) if np.max(magnitudes) > max_mag else max_mag
                    max_freq = np.max(frequencies) if np.max(frequencies) > max_freq else max_freq

                else:
                    frequencies, magnitudes = run.calculate_fft(asymmetry=asymmetry, times=times,
                                                                spline=self.plot_parameters['Spline']())
                    self.plot_panel.canvas_one.axes_time.errorbar(times, asymmetry, uncertainty, color=run.color,
                                                                  linestyle=self.plot_parameters['LineStyle'](),
                                                                  marker='.', label=run.f_formats['RunNumber'])
                    self.plot_panel.canvas_one.axes_freq.plot(frequencies, magnitudes, color=run.color, marker='.',
                                                              label=self.display_annotations(run))

                    max_mag = np.max(magnitudes) if np.max(magnitudes) > max_mag else max_mag
                    max_freq = np.max(frequencies) if np.max(frequencies) > max_freq else max_freq

                frac_start = float(self.plot_parameters['XMinOne']()) / (times[len(times) - 1] - times[0])
                frac_end = float(self.plot_parameters['XMaxOne']()) / (times[len(times) - 1] - times[0])
                start_index = int(np.floor(len(asymmetry) * frac_start))
                end_index = int(np.floor(len(asymmetry) * frac_end))

                max_y = np.max(asymmetry[start_index:end_index]) if \
                    np.max(asymmetry[start_index:end_index]) > max_y else max_y

                min_y = np.min(asymmetry[start_index:end_index]) if \
                    np.min(asymmetry[start_index:end_index]) < min_y else min_y

        # max_mag = 20 if max_mag > 20 else max_mag

        self.plot_panel.canvas_one.axes_freq.set_xlim(0, max_freq * 1.1)
        self.plot_panel.canvas_one.axes_freq.set_ylim(0, max_mag * 1.1)

        if not self.plot_parameters['YAutoOne']():
            self.plot_panel.canvas_one.axes_time.set_ylim(float(self.plot_parameters['YMinOne']()),
                                                          float(self.plot_parameters['YMaxOne']()))
        else:
            self.plot_panel.canvas_one.axes_time.set_ylim(min_y - abs(min_y * 0.1), max_y + abs(max_y * 0.1))

        self.plot_panel.canvas_one.set_style()
        print('ending one')

    def update_canvas_two(self, moving=False):
        print('starting two')
        # FIXME Much room for improvement in this function.
        self.plot_panel.canvas_two.axes_time.clear()
        self.plot_panel.canvas_two.axes_freq.clear()

        self.plot_panel.canvas_two.axes_time.set_xlim(float(self.plot_parameters['XMinTwo']()),
                                                      float(self.plot_parameters['XMaxTwo']()))
        max_y = -2
        min_y = 2
        max_mag = 0
        max_freq = 0

        for run in self.model.run_list:
            if run.visibility:
                asymmetry, times, uncertainty = run.bin_data(final_bin_size=float(self.plot_parameters['BinInputTwo']()),
                                                             slider_moving=moving)
                if moving:
                    self.plot_panel.canvas_two.axes_time.plot(times, asymmetry, color=run.color, linestyle='None',
                                                              marker='.')
                elif not self.plot_parameters['Uncertainty']():
                    frequencies, magnitudes = run.calculate_fft(asymmetry=asymmetry, times=times,
                                                                spline=self.plot_parameters['Spline']())

                    self.plot_panel.canvas_two.axes_time.plot(times, asymmetry, color=run.color, marker='.',
                                                              linestyle=self.plot_parameters['LineStyle']())
                    self.plot_panel.canvas_two.axes_freq.plot(frequencies, magnitudes, color=run.color, marker='.',
                                                              label=self.display_annotations(run))

                    max_mag = np.max(magnitudes) if np.max(magnitudes) > max_mag else max_mag
                    max_freq = np.max(frequencies) if np.max(frequencies) > max_freq else max_freq

                else:
                    frequencies, magnitudes = run.calculate_fft(asymmetry=asymmetry, times=times,
                                                                spline=self.plot_parameters['Spline']())
                    self.plot_panel.canvas_two.axes_time.errorbar(times, asymmetry, uncertainty, color=run.color,
                                                                  linestyle=self.plot_parameters['LineStyle'](),
                                                                  marker='.')
                    self.plot_panel.canvas_two.axes_freq.plot(frequencies, magnitudes, color=run.color, marker='.',
                                                              label=self.display_annotations(run))

                    max_mag = np.max(magnitudes) if np.max(magnitudes) > max_mag else max_mag
                    max_freq = np.max(frequencies) if np.max(frequencies) > max_freq else max_freq

                frac_start = float(self.plot_parameters['XMinTwo']()) / (times[len(times)-1] - times[0])
                frac_end = float(self.plot_parameters['XMaxTwo']()) / (times[len(times)-1] - times[0])
                start_index = int(np.floor(len(asymmetry)*frac_start))
                end_index = int(np.floor(len(asymmetry)*frac_end))

                max_y = np.max(asymmetry[start_index:end_index]) if \
                    np.max(asymmetry[start_index:end_index]) > max_y else max_y

                min_y = np.min(asymmetry[start_index:end_index]) if \
                    np.min(asymmetry[start_index:end_index]) < min_y else min_y

        # print(max_mag, max_freq)
        # max_mag = 20 if max_mag > 20 else max_mag
        # print(max_mag, max_freq)

        self.plot_panel.canvas_two.axes_freq.set_xlim(0, max_freq * 1.1)
        self.plot_panel.canvas_two.axes_freq.set_ylim(0, max_mag * 1.1)

        if not self.plot_parameters['YAutoTwo']():
            self.plot_panel.canvas_two.axes_time.set_ylim(float(self.plot_parameters['YMinTwo']()),
                                                          float(self.plot_parameters['YMaxTwo']()))
        else:
            self.plot_panel.canvas_two.axes_time.set_ylim(min_y - abs(min_y * 0.1), max_y + abs(max_y * 0.1))

        self.plot_panel.canvas_two.set_style()
        print('ending two')

    def display_annotations(self, run):
        return run.f_formats['Title'] if self.plot_parameters['Annotations']() else None

    def display_plot_lines(self):
        return '-' if self.plot_parameters['PlotLines']() else 'None'

    def display_y_limits(self):
        y_min, y_max = self.plot_panel.canvas_one.axes_time.get_ylim()
        self.plot_editor.input_ymin_one.setText('{0:.3f}'.format(y_min))
        self.plot_editor.input_ymax_one.setText('{0:.3f}'.format(y_max))

        y_min, y_max = self.plot_panel.canvas_two.axes_time.get_ylim()
        self.plot_editor.input_ymin_two.setText('{0:.3f}'.format(y_min))
        self.plot_editor.input_ymax_two.setText('{0:.3f}'.format(y_max))

    def check_y_limits(self, plot=None):
        if plot == 1:
            self.plot_editor.input_ymin_one.setEnabled(not self.plot_parameters['YAutoOne']())
            self.plot_editor.input_ymax_one.setEnabled(not self.plot_parameters['YAutoOne']())
        else:
            self.plot_editor.input_ymin_two.setEnabled(not self.plot_parameters['YAutoTwo']())
            self.plot_editor.input_ymax_two.setEnabled(not self.plot_parameters['YAutoTwo']())
        self.visual_data_change(plot=plot, moving=False)

    def update(self, signal=None):
        if signal == BeamsModel.RUN_DATA_CHANGED:
            print("Updating the Plots")
            self.visual_data_change(moving=False)
        elif signal == BeamsModel.RUN_LIST_CHANGED:
            print("Updating the Plots")
            self.visual_data_change(moving=False)


class RunDisplayController:
    def __init__(self, run_display_panel=None, model=None, parent=None):
        self.run_display = run_display_panel
        self.model = model
        self.program_controller = parent
        self.popup = None

        self.model.observers[BeamsModel.RUN_LIST_CHANGED].append(self)

        self.set_callbacks()

    def __str__(self):
        return 'Run Display Controller'

    def set_callbacks(self):
        """ Sets callbacks for events in the Run Display Panel. """
        self.run_display.isolate_button.released.connect(lambda: self.isolate_plot())
        self.run_display.plot_all_button.released.connect(lambda: self.plot_all())
        self.run_display.inspect_file_button.released.connect(lambda: self.inspect_file())
        self.run_display.inspect_hist_button.released.connect(lambda: self.inspect_hist())
        self.run_display.color_choices.currentIndexChanged.connect(lambda: self.change_color())
        self.run_display.current_runs.currentRowChanged.connect(lambda: self.update_run_display())
        self.run_display.current_runs.itemChanged.connect(lambda: self.change_title())
        self.run_display.header_data.currentIndexChanged.connect(lambda: self.change_metadata())

    def isolate_plot(self):
        self.model.update_visibilities(file=self.run_display.current_file.text(), isolate=True)

    def plot_all(self):
        self.model.update_visibilities(isolate=False)

    def inspect_file(self):
        if BeamsUtility.is_found(self.run_display.current_file.text()):
            self.popup = BeamsViews.FileDisplayUI(filename=self.run_display.current_file.text())
            self.popup.show()
        else:
            message = 'File not found.'
            BeamsViews.ErrorMessageUI(message)

    def inspect_hist(self):
        for run in self.model.run_list:
            if run.filename == self.run_display.current_file.text():
                histogram = run.retrieve_histogram_data(specific_hist=self.run_display.histograms.currentText()).values

                plt.ioff()  # Need to turn off interactive plotting to create the new figure for this histograms
                self.popup = BeamsViews.HistogramDisplay(histogram=histogram)
                self.popup.show()
                plt.ion()

                break

    def change_color(self):
        self.model.update_run_color(file=self.run_display.current_file.text(),
                                    color=self.run_display.color_choices.currentText())

    def update_run_display(self):
        index = self.run_display.current_runs.currentRow()
        self.run_display.histograms.clear()

        self.run_display.current_file.setText(self.model.run_list[index].filename)
        self.run_display.color_choices.setCurrentText(self.model.run_list[index].color)
        self.run_display.histograms.addItems(self.model.run_list[index].f_formats['HistTitles'])
        self.update_metadata()

    def update_metadata(self):
        index = self.run_display.current_runs.currentRow()
        self.run_display.header_data.clear()
        self.run_display.header_data.addItems([key for key in self.model.run_list[index].f_formats.keys()])

    def change_metadata(self):
        if self.run_display.header_data.currentText():
            index = self.run_display.current_runs.currentRow()
            key = self.run_display.header_data.currentText()
            value = self.model.run_list[index].f_formats[key]
            self.run_display.header_display.setText(str(value))

    def change_title(self):
        if self.run_display.current_runs.currentItem():
            self.model.update_title(file=self.run_display.current_file.text(),
                                    new_title=self.run_display.current_runs.currentItem().text())

    def populate_run_display(self):
        if self.model.run_list:
            self.run_display.current_runs.clear()
            self.run_display.current_file.setText(self.model.run_list[0].filename)
            self.run_display.current_runs.addItems([run.f_formats['Title'] for run in self.model.run_list])
            for index in range(self.run_display.current_runs.count()):
                item = self.run_display.current_runs.item(index)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.run_display.current_runs.setCurrentRow(0)

            self.run_display.color_choices.setEnabled(True)
            self.run_display.isolate_button.setEnabled(True)
            self.run_display.histograms.setEnabled(True)
            self.run_display.inspect_hist_button.setEnabled(True)
            self.run_display.inspect_file_button.setEnabled(True)
            self.run_display.plot_all_button.setEnabled(True)
            self.run_display.header_data.setEnabled(True)
            self.run_display.header_display.setEnabled(True)
        else:
            self.run_display.color_choices.clear()
            self.run_display.histograms.clear()
            self.run_display.color_choices.setEnabled(False)
            self.run_display.isolate_button.setEnabled(False)
            self.run_display.histograms.setEnabled(False)
            self.run_display.inspect_hist_button.setEnabled(False)
            self.run_display.inspect_file_button.setEnabled(False)
            self.run_display.plot_all_button.setEnabled(False)
            self.run_display.header_data.setEnabled(False)
            self.run_display.header_display.setEnabled(False)

    def update(self, signal):
        if signal == BeamsModel.RUN_LIST_CHANGED:
            print("Updating the Run Display")
            self.populate_run_display()


class FormatterController:
    """ FormatterController paired with FileFormatterUI prompts the user to
            specify the formats for each file.

            Instantiated by FileManagerController class only."""
    def __init__(self, files=None, parent=None):
        if not parent or type(parent) is not FileManagerController:
            raise AttributeError('Parameter parent=FileManagerController not passed.')
            # FormatterController calls prompt_histograms() in FileManagerController after GUI closes

        self.formatter_gui = BeamsViews.FileFormatterUI(filenames=files)
        self.parent_controller = parent
        self.set_callbacks()
        self.formatter_gui.show()

    def set_callbacks(self):
        self.formatter_gui.done_button.released.connect(lambda: self.b_done_formatting())

    def b_apply_formats(self, apply_all=False):
        pass

    def b_skip_file(self):
        pass

    def b_done_formatting(self):
        self.formatter_gui.close()
        self.parent_controller.prompt_histograms()

    @staticmethod
    def c_column_checked(check_box, input_box):
        input_box.setEnabled(check_box.isChecked())


class WriterController:
    def __init__(self, model=None, selected_files=None):
        self.writer_gui = BeamsViews.WriteDataUI()
        self.writer_gui.file_list.addItems(selected_files)

        self.model = model
        self.files = selected_files
        self.custom_file = False

        self.popup = None
        self.formats = None

        self.set_callbacks()
        self.writer_gui.show()

        current_runs = [os.path.split(run.filename)[1] for run in self.model.run_list]
        print(current_runs, self.files)
        for file in self.files:
            if file not in current_runs:
                message = 'Some of the files you\'ve selected haven\'t been read in yet. Would you like to now?'
                BeamsViews.PermissionsMessageUI(message, pos_function=self.read_files,
                                                neg_function=self.writer_gui.close)
                break

    def read_files(self):
        check_files = [self.model.all_full_filepaths[key] for key in self.files]
        beams_files, *_ = BeamsUtility.check_files(check_files)
        if self.formats:
            self.formats.clear()

        if beams_files:
            self.formats = {file: file_format for file, file_format in
                            zip(beams_files, [BeamsUtility.get_header(file) for file in beams_files])}

            self.popup = PlotDataController(self.formats, model=self.model, plot=False)

    def set_callbacks(self):
        self.writer_gui.select_folder.released.connect(lambda: self.custom_file_choice())
        self.writer_gui.write_file.released.connect(lambda: self.write_files(all_files=False))
        self.writer_gui.write_all.released.connect(lambda: self.write_files(all_files=True))
        self.writer_gui.skip_file.released.connect(lambda: self.remove_file())
        self.writer_gui.done.released.connect(lambda: self.writer_gui.close())

    def custom_file_choice(self):
        """ Prompts the user for a custom file path. """
        saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.writer_gui, 'Specify file',
                                                                os.getcwd(), 'ASY(*.asy)')[0]
        if not saved_file_path:
            return
        else:
            self.writer_gui.input_filename.setText(saved_file_path)
            self.custom_file = True

    def write_files(self, all_files=False):
        """ Writes the user-specified run data (if they are read in) to a .dat file. """
        count = 0
        for run in self.model.run_list:
            if os.path.split(run.filename)[1] == self.writer_gui.file_list.currentText() or \
                    (all_files and os.path.split(run.filename)[1] in self.files):

                if self.custom_file:
                    file_path = self.writer_gui.input_filename.text()
                    if count:
                        file_path = os.path.splitext(file_path)[0]
                        file_path += '({}).asy'.format(count)
                else:
                    if 'RunNumber' in run.f_formats.keys():
                        file_path = os.path.split(run.filename)[0] + '\\' + str(run.f_formats['RunNumber']) + '.asy'
                    else:
                        file_path = os.path.splitext(run.filename)[0] + '.asy'

                if self.writer_gui.radio_binned.isChecked():
                    np.savetxt(file_path, np.c_[run.binned_time, run.binned_asymmetry, run.binned_uncertainty],
                               fmt='%2.9f, %2.4f, %2.4f', header='BEAMS\nTime, Asymmetry, Uncertainty')
                elif self.writer_gui.radio_full.isChecked():
                    np.savetxt(file_path, np.c_[run.time, run.asymmetry, run.uncertainty],
                               fmt='%2.9f, %2.4f, %2.4f', header='BEAMS\nTime, Asymmetry, Uncertainty')
                else:
                    print('FFT not supported.')
                count += 1

    def remove_file(self):
        self.writer_gui.file_list.removeItem(self.writer_gui.file_list.currentIndex())


class PlotDataController:
    """ PlotDataController paired with PlotDataUI prompts the user to specify which histograms
            will be used to calculate the asymmetry for each file.

            Instantiated by FileManagerController class only."""
    def __init__(self, formats=None, model=None, plot=True):
        """ Instantiates an object of the PlotDataController class, connects it to the PlotDataGUI
                and its calling class (FileManagerController). """

        self.plot_data_gui = BeamsViews.PlotDataUI()
        self.plot = plot
        self.model = model
        self.set_callbacks()
        self.formats = formats
        self.plot_data_gui.c_file_list.addItems([file for file in self.formats.keys()])

        self.plot_data_gui.show()

    def set_callbacks(self):
        """ Sets the callbacks for the events handled in the PlotDataGUI"""
        self.plot_data_gui.b_apply.released.connect(lambda: self.add_format())
        self.plot_data_gui.b_apply_all.released.connect(lambda: self.add_format(all_files=True))
        self.plot_data_gui.b_cancel.released.connect(lambda: self.plot_data_gui.close())
        self.plot_data_gui.b_skip.released.connect(lambda: self.remove_file())
        self.plot_data_gui.b_plot.released.connect(lambda: self.plot_formatted_files())
        self.plot_data_gui.c_file_list.currentIndexChanged.connect(lambda: self.file_changed())

    def add_format(self, all_files=False):
        """ Takes the currently selected histograms and adds them to the file(s) format. """
        calc_hists = self.current_histograms()
        num_files = self.plot_data_gui.c_file_list.count()
        if not calc_hists:  # If calc_hists is None user needs to choose histograms.
            return

        # If applying to all files, save the currently selected hists in each files format
        if all_files:
            for index in range(num_files):
                file = self.plot_data_gui.c_file_list.itemText(index)
                self.formats[file]['CalcHists'] = calc_hists

        # Else only save it with the current file
        else:
            file = self.plot_data_gui.c_file_list.currentText()
            self.formats[file]['CalcHists'] = calc_hists

            # Update the file list to display the next file.
            if self.plot_data_gui.c_file_list.currentIndex() < num_files:
                self.plot_data_gui.c_file_list.setCurrentIndex(self.plot_data_gui.c_file_list.currentIndex()+1)

    def current_histograms(self):
        """ Returns the currently selected histograms as [left histogram, right histogram]. """
        calc_hists = [self.plot_data_gui.c_hist_one.currentText(), self.plot_data_gui.c_hist_two.currentText()]

        if calc_hists[0] == calc_hists[1]:  # Check if both histograms are the same
            message = 'Cannot calculate asymmetry from the same histograms.'
            BeamsViews.ErrorMessageUI(message)
        else:
            return calc_hists
        return None

    def plot_formatted_files(self):
        """ Closes the GUI and calls update_model() in the parent class FileManagerControl. """
        self.plot_data_gui.close()

        update_thread = threading.Thread(target=self.model.update_runs(self.formats, plot=self.plot), daemon=True)
        update_thread.start()

    def remove_file(self):
        """ Removes the currently selected file from the file list and from the format list. """
        self.formats.pop(self.plot_data_gui.c_file_list.currentText())
        self.plot_data_gui.c_file_list.removeItem(self.plot_data_gui.c_file_list.currentIndex())

    def file_changed(self):
        """ Changes the histograms displayed to match the currently selected file. """
        self.plot_data_gui.c_hist_one.clear()
        self.plot_data_gui.c_hist_two.clear()

        if self.plot_data_gui.c_file_list.currentText():  # Stop displaying if no files left in file list
            self.plot_data_gui.c_hist_one.addItems(self.formats[
                                                       self.plot_data_gui.c_file_list.currentText()]['HistTitles'])
            self.plot_data_gui.c_hist_two.addItems(self.formats[
                                                       self.plot_data_gui.c_file_list.currentText()]['HistTitles'])


class SavePlotController:  # fixme just make this a smart UI in the views file, it's pretty short.
    def __init__(self, canvases=None):
        self.save_plot_gui = BeamsViews.SavePlotUI()
        self.canvases = canvases
        self.extension_filters = self.get_supported_extensions()

        self.save_plot_gui.save_button.released.connect(self.save_plots)
        self.save_plot_gui.show()

    @staticmethod
    def get_supported_extensions():
        extensions = plt.gcf().canvas.get_supported_filetypes().keys()
        extension_filters = ";;"
        extension_list = []

        [(extension_list.append("{}(*.{})".format(str(ext).upper(), ext))) for ext in extensions]
        extension_filters = extension_filters.join(extension_list)

        return extension_filters

    def save_plots(self):
        if self.save_plot_gui.left_radio.isChecked():  # Setting the current figure to left or right (1 or 2)
            plt.figure(1)
        elif self.save_plot_gui.right_radio.isChecked():
            plt.figure(2)
        else:
            BeamsViews.ErrorMessageUI(error_message='You need to select a plot.')
            return

        saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.save_plot_gui, 'Specify file', os.getcwd(),
                                                                filter=self.extension_filters)[0]
        if not saved_file_path:
            return

        try:
            plt.savefig(saved_file_path)
        except ValueError:
            BeamsViews.ErrorMessageUI(error_message='Invalid save file type.')
        else:
            self.save_plot_gui.close()
