# BEAMS specific modules
import BeamsViews
import BeamsModel
import BeamsUtility

# Standard Library modules
import sys
import os
import pickle
import threading
import warnings

# Installed modules
import requests
import numpy as np
from PyQt5 import QtWidgets, QtCore


class ProgramController:
    """ Main controller responsible for initializing and starting the application. """
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)

        self.app.setStyleSheet(BeamsViews.StyleFile(r'style/light_style.qss', r'style/light_style_vars.txt').style)

        # Initialize the model
        # Note: The model holds most application-relevant data and the 'business logic' of the application.
        self.service = BeamsModel.RunService()

        # Initialize all the GUIs with their controllers
        # Note: The controllers are responsible for handling user input on the GUIs. The GUIs will update based on
        # changes in the model
        self.main_window_v = BeamsViews.MainGUIWindow()  # Builds Main Window GUI with all the connected panels
        self._set_callbacks()

        self.file_manager_controller = FileManagerController(file_manager_panel=self.main_window_v.file_manager, parent=self)
        self.plot_editor_controller = PlotController(plot_editor_panel=self.main_window_v.plot_editor,
                                                     plot_panel=self.main_window_v.plot_panel, parent=self)
        self.run_display_controller = RunDisplayController(run_display_panel=self.main_window_v.run_display, parent=self)

        self.main_window_v.show()
        sys.exit(self.app.exec_())

    def _set_callbacks(self):
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

    def update(self, signal):
        BeamsViews.ErrorMessageUI('There was an error during the previous action. Please try again or restart program.')


class MuFytController:
    def __init__(self, mufyt_panel=None, model=None, parent=None):
        pass


class FileManagerController:
    """ Controller responsible for managing user input on the File Manager Panel. """
    def __init__(self, file_manager_panel=None, parent=None):
        """ Initializes the FileManagerController and sets callbacks for the GUI"""

        if not file_manager_panel or not parent:  # Raise error if not properly instantiated
            raise AttributeError('FileManagerController did not receive all necessary inputs.')

        self.file_manager = file_manager_panel
        self.service = BeamsModel.RunService()
        self.service.observers[BeamsModel.FILE_CHANGE].append(self)

        self.program_controller = parent
        self.formats = {}
        self.file_title_dict = dict()
        self.popup = None

        self._set_callbacks()

    def __str__(self):
        return 'File Manager Controller'

    def _set_callbacks(self):
        """ Sets the callbacks for events in the File Manager Panel. """
        self.file_manager.import_button.released.connect(lambda: self.add_file())
        self.file_manager.write_button.released.connect(lambda: self.write_file())
        self.file_manager.plot_button.released.connect(lambda: self.plot_file())
        self.file_manager.convert_button.released.connect(lambda: self.convert_file())
        self.file_manager.remove_button.released.connect(lambda: self.remove_file())
        self.file_manager.select_all.stateChanged.connect(lambda: self._select_all())

    def _select_all(self):
        """ Selects or deselects all files based on the checked state of the select all checkbox. """
        for index in range(self.file_manager.file_list.count()):
            if self.file_manager.select_all.checkState():
                self.file_manager.file_list.item(index).setCheckState(QtCore.Qt.Checked)
            else:
                self.file_manager.file_list.item(index).setCheckState(QtCore.Qt.Unchecked)

    def _get_selected_files(self):
        """ Returns all currently selected files in the File Manager Panel. """
        checked_items = set()
        for index in range(self.file_manager.file_list.count()):
            if self.file_manager.file_list.item(index).checkState() == QtCore.Qt.Checked:
                checked_items.add(self.file_manager.file_list.item(index).text())
        return checked_items

    def _get_all_files(self):
        """ Returns all files in the File Manager Panel. """
        files = set()
        for index in range(self.file_manager.file_list.count()):
            files.add(self.file_manager.file_list.item(index).text())
        return files

    def remove_file(self):
        """ Removes the currently selected files from the file manager. """
        def remove():
            for file_root in selected_files:
                for index in range(self.file_manager.file_list.count()):
                    if file_root == self.file_manager.file_list.item(index).text():
                        self.file_manager.file_list.takeItem(index)
                        break

            if len(self._get_selected_files()) == 0:
                self.file_manager.select_all.setChecked(False)

            full_file_paths = [self.file_title_dict[title] for title in selected_files]
            self.service.update_file_list(full_file_paths, remove=True)

        selected_files = self._get_selected_files()
        message = 'Are you sure you would like to remove all currently selected files?'
        BeamsViews.PermissionsMessageUI(message, pos_function=remove)

    def add_file(self):
        """ Prompts the user for and stores full file paths in model.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        BeamsViews.AddFileUI(self, WebServiceController)

    def add_file_from_disk(self):
        # Open a dialog to prompt users for file(s)
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self.file_manager, 'Add file', '/home')[0]
        self.service.update_file_list(filenames, remove=False)

    def plot_file(self):
        checked_files = {BeamsUtility.FileReader.BINARY_FILE: [],
                         BeamsUtility.FileReader.ASYMMETRY_FILE: [],
                         BeamsUtility.FileReader.HISTOGRAM_FILE: []}

        for file_path in [self.file_title_dict[title] for title in self._get_selected_files()]:
            file = BeamsUtility.FileReader(file_path)
            checked_files[file.get_type()].append(file)

        if len(checked_files[BeamsUtility.FileReader.BINARY_FILE]) != 0:
            message = 'MUD Files selected, would you like them to be converted?'
            BeamsViews.PermissionsMessageUI(message, pos_function=self.convert_file)
            return

        if len(checked_files[BeamsUtility.FileReader.ASYMMETRY_FILE]) != 0:
            threading.Thread(target=self.service.update_run_list(checked_files[BeamsUtility.FileReader.ASYMMETRY_FILE])).start()

        if len(checked_files[BeamsUtility.FileReader.HISTOGRAM_FILE]) != 0:
            self.popup = PlotDataController(checked_files[BeamsUtility.FileReader.HISTOGRAM_FILE], plot=True)

        if len(checked_files.values()) == 0:
            BeamsViews.ErrorMessageUI(error_message='No files selected.')

    def convert_file(self):
        """ Converts currently selected .msr files to .dat files and saves them in the current directory.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        def remove_msr():
            for file_root in checked_items:
                if os.path.splitext(file_root)[1] == '.msr':
                    for index in range(self.file_manager.file_list.count()):
                        if file_root == self.file_manager.file_list.item(index).text():
                            self.file_manager.file_list.takeItem(index)
                            self.service.update_file_list([self.file_title_dict[file_root]], remove=True)
                            break

        checked_items = self._get_selected_files()
        for file in checked_items:
            full_file = self.file_title_dict[file]

            if BeamsUtility.check_ext(full_file, '.msr'):  # Check extension of input and output files
                out_file = os.path.splitext(full_file)[0] + '.dat'

                if BeamsUtility.convert_msr(full_file, out_file, flags=['-v', '-all']):  # Run the MUD executable on the .msr file
                    self.service.update_file_list([out_file], remove=False)

                else:
                    # Usually occurs when their have been changes in the .msr files
                    message = 'Error reading .msr file.\n {} has possibly been corrupted.'.format(full_file)
                    BeamsViews.ErrorMessageUI(error_message=message)
                    return

        remove_msr()
        if len(self._get_selected_files()) == 0:
            self.file_manager.select_all.setChecked(False)
            self.file_manager.select_all.setChecked(True)

    def write_file(self):
        """ Launches the Writer GUI.
            Note: The change in the model will notify and result in update of GUI. See update(). """
        full_selected_file_paths = [self.file_title_dict[title] for title in self._get_selected_files()]
        self.popup = WriterController(selected_files=full_selected_file_paths)

    def update(self, signal=None):
        """ Called by the model when one of its FileManagerPanel-relevant attributes changes. """
        for index in range(self.file_manager.file_list.count()-1, -1, -1):
            self.file_manager.file_list.takeItem(index)
        print(1)
        files = self.service.get_run_files()

        file_titles = []
        for file in files:
            print(file)
            file_title = BeamsUtility.create_file_key(file)
            print(file_title)
            file_titles.append(file_title)
            print(file_titles)
            self.file_title_dict[file_title] = file
            print(self.file_title_dict)

        file_titles = sorted(file_titles)
        for title in file_titles:
            print(4)
            file_item = QtWidgets.QListWidgetItem(title, self.file_manager.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)
        print(5)

class PlotController:
    def __init__(self, plot_editor_panel=None, plot_panel=None, parent=None):
        """ Initializes the PlotEditorController and sets callbacks for the GUI"""

        if not plot_editor_panel or not parent:  # Raise error if not properly instantiated
            raise AttributeError('PlotEditorController did not receive all necessary inputs.')

        self.plot_editor = plot_editor_panel
        self.plot_panel = plot_panel
        self.service = BeamsModel.RunService()
        self.service.observers[BeamsModel.RUN_DATA_CHANGE].append(self)
        self.service.observers[BeamsModel.STYLE_CHANGE].append(self)
        self.service.observers[BeamsModel.RUN_LIST_CHANGE].append(self)
        self.canvases = [self.plot_panel.canvas_one, self.plot_panel.canvas_two]

        self.program_controller = parent
        self.popup = None

        self.plot_parameters = {
                                'TimeXMinOne': self.plot_panel.input_time_xmin_one.text,
                                'TimeXMinTwo': self.plot_panel.input_time_xmin_two.text,
                                'TimeXMaxOne': self.plot_panel.input_time_xmax_one.text,
                                'TimeXMaxTwo': self.plot_panel.input_time_xmax_two.text,
                                'TimeYMinOne': self.plot_panel.input_time_ymin_one.text,
                                'TimeYMinTwo': self.plot_panel.input_time_ymin_two.text,
                                'TimeYMaxOne': self.plot_panel.input_time_ymax_one.text,
                                'TimeYMaxTwo': self.plot_panel.input_time_ymax_two.text,

                                'FreqXMinOne': self.plot_panel.input_freq_xmin_one.text,
                                'FreqXMinTwo': self.plot_panel.input_freq_xmin_two.text,
                                'FreqXMaxOne': self.plot_panel.input_freq_xmax_one.text,
                                'FreqXMaxTwo': self.plot_panel.input_freq_xmax_two.text,
                                'FreqYMinOne': self.plot_panel.input_freq_ymin_one.text,
                                'FreqYMinTwo': self.plot_panel.input_freq_ymin_two.text,
                                'FreqYMaxOne': self.plot_panel.input_freq_ymax_one.text,
                                'FreqYMaxTwo': self.plot_panel.input_freq_ymax_two.text,

                                'BinInputOne': self.plot_panel.input_slider_one.text,
                                'BinInputTwo': self.plot_panel.input_slider_two.text,
                                'SliderOne': self.plot_panel.slider_one.value,
                                'SliderTwo': self.plot_panel.slider_two.value,

                                'TimeYAutoOne': self.plot_panel.check_time_y_autoscale_one.isChecked,
                                'TimeYAutoTwo': self.plot_panel.check_time_y_autoscale_two.isChecked,
                                'FreqYAutoOne': self.plot_panel.check_freq_y_autoscale_one.isChecked,
                                'FreqYAutoTwo': self.plot_panel.check_freq_y_autoscale_two.isChecked,
                                'FreqXAutoOne': self.plot_panel.check_freq_x_autoscale_one.isChecked,
                                'FreqXAutoTwo': self.plot_panel.check_freq_x_autoscale_two.isChecked,

                                'PlotLines': self.plot_editor.check_plot_lines.isChecked,
                                'Annotations': self.plot_editor.check_annotation.isChecked,
                                'Spline': self.plot_editor.check_spline.isChecked,
                                'Uncertainty': self.plot_editor.check_uncertain.isChecked,
                                'LineStyle': self._display_plot_lines
        }

        self._set_callbacks()

    def __str__(self):
        return 'Plot Controller'

    def _set_callbacks(self):
        """ Sets callbacks for events in the Plot Editor Panel. """
        self.plot_panel.input_time_xmin_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_time_xmin_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_time_xmax_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_time_xmax_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_time_ymin_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_time_ymin_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_time_ymax_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_time_ymax_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_freq_xmin_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_freq_xmin_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_freq_xmax_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_freq_xmax_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_freq_ymin_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_freq_ymin_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_freq_ymax_one.returnPressed.connect(lambda: self._visual_data_change(plot=1))
        self.plot_panel.input_freq_ymax_two.returnPressed.connect(lambda: self._visual_data_change(plot=2))
        self.plot_panel.input_slider_one.returnPressed.connect(lambda: self._bin_changed(moving=False, plot=1))
        self.plot_panel.input_slider_two.returnPressed.connect(lambda: self._bin_changed(moving=False, plot=2))
        self.plot_panel.slider_one.sliderMoved.connect(lambda: self._bin_changed(moving=True, plot=1))
        self.plot_panel.slider_two.sliderMoved.connect(lambda: self._bin_changed(moving=True, plot=2))
        self.plot_panel.slider_one.sliderReleased.connect(lambda: self._bin_changed(moving=False, plot=1))
        self.plot_panel.slider_two.sliderReleased.connect(lambda: self._bin_changed(moving=False, plot=2))
        self.plot_editor.check_annotation.stateChanged.connect(lambda: self._visual_data_change())
        self.plot_editor.check_plot_lines.stateChanged.connect(lambda: self._visual_data_change())
        self.plot_editor.check_uncertain.stateChanged.connect(lambda: self._visual_data_change())
        self.plot_editor.check_spline.stateChanged.connect(lambda: self._visual_data_change())
        self.plot_panel.check_time_y_autoscale_one.stateChanged.connect(lambda: self._check_y_limits(1, 'TimeYAuto'))
        self.plot_panel.check_time_y_autoscale_two.stateChanged.connect(lambda: self._check_y_limits(2, 'TimeYAuto'))
        self.plot_panel.check_freq_y_autoscale_one.stateChanged.connect(lambda: self._check_y_limits(1, 'FreqYAuto'))
        self.plot_panel.check_freq_y_autoscale_two.stateChanged.connect(lambda: self._check_y_limits(2, 'FreqYAuto'))
        self.plot_panel.check_freq_x_autoscale_one.stateChanged.connect(lambda: self._check_y_limits(1, 'FreqXAuto'))
        self.plot_panel.check_freq_x_autoscale_two.stateChanged.connect(lambda: self._check_y_limits(2, 'FreqXAuto'))

    def _bin_changed(self, moving=None, plot=None):
        """ Handles the bin size changing on either the slider or the text box. If one changes then
            the other is updated. """
        if moving:
            self.plot_panel.input_slider_one.setText(str(self.plot_parameters['SliderOne']()))
            self.plot_panel.input_slider_two.setText(str(self.plot_parameters['SliderTwo']()))
            if plot == 1:
                if self.plot_parameters['SliderOne']() % 5 is not 0:
                    return
            elif plot == 2:
                if self.plot_parameters['SliderTwo']() % 5 is not 0:
                    return
        else:
            self.plot_panel.slider_one.setValue(int(np.ceil(float(self.plot_parameters['BinInputOne']()))))
            self.plot_panel.slider_two.setValue(int(np.ceil(float(self.plot_parameters['BinInputTwo']()))))

        self._visual_data_change(plot=plot, moving=moving)

    def _visual_data_change(self, plot=None, moving=False):
        """ Handles the changes made to Plot Editor widgets that necessitate recalculation of the Run Data. """
        if plot:
            if plot == 1:
                threading.Thread(target=self._update_canvas(1, moving), daemon=True).start()
            else:
                threading.Thread(target=self._update_canvas(2, moving), daemon=True).start()
        else:
            threading.Thread(target=self._update_canvas(1, moving), daemon=True).start()
            threading.Thread(target=self._update_canvas(2, moving), daemon=True).start()

        self._display_y_limits()
        self._display_x_limits()

    def _update_canvas(self, can_int, moving=False):
        # Get the appropriate plotting parameters for the specified canvas
        canvas = self.canvases[can_int-1]
        xmin = self.plot_parameters['TimeXMinOne']() if can_int == 1 else self.plot_parameters['TimeXMinTwo']()
        xmax = self.plot_parameters['TimeXMaxOne']() if can_int == 1 else self.plot_parameters['TimeXMaxTwo']()
        bin = self.plot_parameters['BinInputOne']() if can_int == 1 else self.plot_parameters['BinInputTwo']()
        timeyauto = self.plot_parameters['TimeYAutoOne']() if can_int == 1 else self.plot_parameters['TimeYAutoTwo']()
        freqyauto = self.plot_parameters['FreqYAutoOne']() if can_int == 1 else self.plot_parameters['FreqYAutoTwo']()
        freqxauto = self.plot_parameters['FreqXAutoOne']() if can_int == 1 else self.plot_parameters['FreqXAutoTwo']()

        canvas.axes_time.clear()
        canvas.axes_freq.clear()

        max_y = -1
        min_y = 1
        max_mag = 0
        max_freq = 0

        canvas.axes_time.set_xlim(float(xmin), float(xmax))

        for run in self.service.get_runs():
            style = run.style
            if style.visibility:
                asymmetry, times, uncertainty = self.service.get_run_binned(run.run_id, float(bin), moving)
                if moving:
                    canvas.axes_time.plot(times, asymmetry, color=style.color, linestyle='None', marker=style.marker)

                else:
                    if not self.plot_parameters['Uncertainty']():
                        canvas.axes_time.plot(times, asymmetry, color=style.color, marker=style.marker,
                                              linestyle=self.plot_parameters['LineStyle'](), fillstyle='none')

                    else:
                        canvas.axes_time.errorbar(times, asymmetry, uncertainty, color=style.color,
                                                                      linestyle=self.plot_parameters['LineStyle'](),
                                                                      marker=style.marker, fillstyle='none')

                    frequencies, magnitudes = BeamsModel.calculate_fft(asymmetry, times, self.plot_parameters['Spline']())

                    canvas.axes_freq.plot(frequencies, magnitudes, color=style.color, marker='.',
                                                                  label=self._display_annotations(run))

                    max_mag = np.max(magnitudes) if np.max(magnitudes) > max_mag else max_mag
                    max_freq = np.max(frequencies) if np.max(frequencies) > max_freq else max_freq

                frac_start = float(xmin) / (times[len(times) - 1] - times[0])
                frac_end = float(xmax) / (times[len(times) - 1] - times[0])
                start_index = int(np.floor(len(asymmetry) * frac_start))
                end_index = int(np.floor(len(asymmetry) * frac_end))

                max_y = np.max(asymmetry[start_index:end_index]) if \
                    np.max(asymmetry[start_index:end_index]) > max_y else max_y

                min_y = np.min(asymmetry[start_index:end_index]) if \
                    np.min(asymmetry[start_index:end_index]) < min_y else min_y

        if not timeyauto:
            ymin = self.plot_parameters['TimeYMinOne']() if can_int == 1 else self.plot_parameters['TimeYMinTwo']()
            ymax = self.plot_parameters['TimeYMaxOne']() if can_int == 1 else self.plot_parameters['TimeYMaxTwo']()
            canvas.axes_time.set_ylim(float(ymin), float(ymax))
        else:
            canvas.axes_time.set_ylim(min_y - abs(min_y * 0.1), max_y + abs(max_y * 0.1))

        if not freqyauto:
            ymin = self.plot_parameters['FreqYMinOne']() if can_int == 1 else self.plot_parameters['FreqYMinTwo']()
            ymax = self.plot_parameters['FreqYMaxOne']() if can_int == 1 else self.plot_parameters['FreqYMaxTwo']()
            canvas.axes_freq.set_ylim(float(ymin), float(ymax))
        else:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                canvas.axes_freq.set_ylim(0, max_mag * 1.1)

        if not freqxauto:
            xmin = self.plot_parameters['FreqXMinOne']() if can_int == 1 else self.plot_parameters['FreqXMinTwo']()
            xmax = self.plot_parameters['FreqXMaxOne']() if can_int == 1 else self.plot_parameters['FreqXMaxTwo']()
            canvas.axes_freq.set_xlim(float(xmin), float(xmax))

        canvas.set_style(moving)

        canvas.axes_time.figure.canvas.draw()

    def _display_annotations(self, run):
        return run.meta['Title'] if self.plot_parameters['Annotations']() else None

    def _display_plot_lines(self):
        return '-' if self.plot_parameters['PlotLines']() else 'None'

    def _display_x_limits(self):
        x_min, x_max = self.plot_panel.canvas_one.axes_freq.get_xlim()
        self.plot_panel.input_freq_xmin_one.setText('{0:.3f}'.format(x_min))
        self.plot_panel.input_freq_xmax_one.setText('{0:.3f}'.format(x_max))

        x_min, x_max = self.plot_panel.canvas_two.axes_freq.get_xlim()
        self.plot_panel.input_freq_xmin_two.setText('{0:.3f}'.format(x_min))
        self.plot_panel.input_freq_xmax_two.setText('{0:.3f}'.format(x_max))

    def _display_y_limits(self):
        y_min, y_max = self.plot_panel.canvas_one.axes_time.get_ylim()
        self.plot_panel.input_time_ymin_one.setText('{0:.3f}'.format(y_min))
        self.plot_panel.input_time_ymax_one.setText('{0:.3f}'.format(y_max))

        y_min, y_max = self.plot_panel.canvas_two.axes_time.get_ylim()
        self.plot_panel.input_time_ymin_two.setText('{0:.3f}'.format(y_min))
        self.plot_panel.input_time_ymax_two.setText('{0:.3f}'.format(y_max))

        y_min, y_max = self.plot_panel.canvas_one.axes_freq.get_ylim()
        self.plot_panel.input_freq_ymin_one.setText('{0:.3f}'.format(y_min))
        self.plot_panel.input_freq_ymax_one.setText('{0:.3f}'.format(y_max))

        y_min, y_max = self.plot_panel.canvas_two.axes_freq.get_ylim()
        self.plot_panel.input_freq_ymin_two.setText('{0:.3f}'.format(y_min))
        self.plot_panel.input_freq_ymax_two.setText('{0:.3f}'.format(y_max))

    def _check_y_limits(self, plot=None, option='TimeYAuto'):
        if option == 'TimeYAuto':
            if plot == 1:
                self.plot_panel.input_time_ymin_one.setEnabled(not self.plot_parameters['TimeYAutoOne']())
                self.plot_panel.input_time_ymax_one.setEnabled(not self.plot_parameters['TimeYAutoOne']())
            else:
                self.plot_panel.input_time_ymin_two.setEnabled(not self.plot_parameters['TimeYAutoTwo']())
                self.plot_panel.input_time_ymax_two.setEnabled(not self.plot_parameters['TimeYAutoTwo']())
        elif option == 'FreqYAuto':
            if plot == 1:
                self.plot_panel.input_freq_ymin_one.setEnabled(not self.plot_parameters['FreqYAutoOne']())
                self.plot_panel.input_freq_ymax_one.setEnabled(not self.plot_parameters['FreqYAutoOne']())
            else:
                self.plot_panel.input_freq_ymin_two.setEnabled(not self.plot_parameters['FreqYAutoTwo']())
                self.plot_panel.input_freq_ymax_two.setEnabled(not self.plot_parameters['FreqYAutoTwo']())
        elif option == 'FreqXAuto':
            if plot == 1:
                self.plot_panel.input_freq_xmin_one.setEnabled(not self.plot_parameters['FreqXAutoOne']())
                self.plot_panel.input_freq_xmax_one.setEnabled(not self.plot_parameters['FreqXAutoOne']())
            else:
                self.plot_panel.input_freq_xmin_two.setEnabled(not self.plot_parameters['FreqXAutoTwo']())
                self.plot_panel.input_freq_xmax_two.setEnabled(not self.plot_parameters['FreqXAutoTwo']())

        self._visual_data_change(plot=plot, moving=False)

    def update(self, signal=None):
        self._visual_data_change(moving=False)


class RunDisplayController:
    def __init__(self, run_display_panel=None, parent=None):
        self.run_display = run_display_panel
        self.service = BeamsModel.RunService()
        self.service.observers[BeamsModel.RUN_LIST_CHANGE].append(self)
        self.program_controller = parent
        self.popup = None
        self.run_id_title = dict()

        self._set_callbacks()
        self._change_selection = False

    def __str__(self):
        return 'Run Display Controller'

    def _set_callbacks(self):
        """ Sets callbacks for events in the Run Display Panel. """
        self.run_display.isolate_button.released.connect(lambda: self.isolate_plot())
        self.run_display.plot_all_button.released.connect(lambda: self.plot_all())
        self.run_display.inspect_file_button.released.connect(lambda: self.inspect_file())
        self.run_display.inspect_hist_button.released.connect(lambda: self.inspect_hist())
        self.run_display.color_choices.currentIndexChanged.connect(lambda: self.change_color())
        self.run_display.marker_choices.currentIndexChanged.connect(lambda: self.change_marker())
        self.run_display.current_runs.currentRowChanged.connect(lambda: self.update_run_display())
        self.run_display.current_runs.itemChanged.connect(lambda: self.change_title())
        self.run_display.header_data.currentIndexChanged.connect(lambda: self.change_metadata())
        self.run_display.input_alpha.returnPressed.connect(lambda: self.apply_correction())
        self.run_display.correction_button.released.connect(lambda: self.apply_correction())
        self.run_display.integrate_button.released.connect(lambda: self.integrate_plots())

    def apply_correction(self):
        try:
            alpha = float(self.run_display.input_alpha.text())
        except ValueError:
            return

        run_ids = [self.run_id_title[item.text()] for item in self.run_display.current_runs.selectedItems()]
        self.service.update_run_correction(run_ids, alpha)

    def isolate_plot(self):
        selected_run_ids = [self.run_id_title[item.text()] for item in self.run_display.current_runs.selectedItems()]
        self.service.update_visible_runs(selected_run_ids)

    def plot_all(self):
        visible_runs = [v for k, v in self.run_id_title.items()]
        self.service.update_visible_runs(visible_runs)

    def integrate_plots(self):
        selected_run_ids = [self.run_id_title[item.text()] for item in self.run_display.current_runs.selectedItems()]

        asymmetry_integrations = self.service.get_run_integrations(selected_run_ids)

        if self.run_display.integrate_choices.currentText() == "Field":
            x_axis_data = self.service.get_run_fields(selected_run_ids)
            x_axis = 'Field (G)'
        else:
            x_axis_data = self.service.get_run_temperatures(selected_run_ids)
            x_axis = 'Temperature (K)'

        self.popup = BeamsViews.IntegrationDisplay(asymmetry_integrations, x_axis, x_axis_data)
        self.popup.show()

    def inspect_file(self):
        if BeamsUtility.is_found(self.run_display.output_current_file.text()):
            self.popup = BeamsViews.FileDisplayUI(filename=self.run_display.output_current_file.text())
            self.popup.show()
        else:
            message = 'File not found.'
            BeamsViews.ErrorMessageUI(message)

    def inspect_hist(self):
        for run in self.service.get_runs():
            if run.filename == self.run_display.output_current_file.text():
                histogram = self.service.get_run_histogram(run.run_id, self.run_display.histograms.currentText())
                self.popup = BeamsViews.HistogramDisplay(histogram=histogram)
                self.popup.show()
                break

    def change_color(self):
        if len(self.service.get_runs()) == 0 or self.run_display.current_runs.currentItem() is None:
            return

        if not self._change_selection:
            run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
            self.service.update_run_style(run_id, BeamsModel.STYLE_COLOR, self.run_display.color_choices.currentText())

    def change_marker(self):
        if len(self.service.get_runs()) == 0 or self.run_display.current_runs.currentItem() is None:
            return

        if not self._change_selection:
            run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
            self.service.update_run_style(run_id, BeamsModel.STYLE_MARKER, self.run_display.marker_choices.currentText())

    def update_run_display(self):
        if len(self.service.get_runs()) == 0 or self.run_display.current_runs.currentItem() is None:
            return

        self._change_selection = True
        run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
        run = self.service.get_run_by_id(run_id)
        self.run_display.histograms.clear()

        styler = BeamsModel.RunStyler()

        self.run_display.output_current_file.setText(run.filename)
        self.run_display.input_alpha.setText(str(run.alpha))
        self.run_display.color_choices.setCurrentText(styler.color_options[run.style.color])
        self.run_display.marker_choices.setCurrentText(styler.marker_options[run.style.marker])

        if run.type != BeamsUtility.FileReader.HISTOGRAM_FILE:
            self.run_display.histograms.setEnabled(False)
            self.run_display.inspect_hist_button.setEnabled(False)
        else:
            self.run_display.histograms.setEnabled(True)
            self.run_display.histograms.setEnabled(True)
            self.run_display.histograms.addItems(run.meta[BeamsUtility.HIST_TITLES_KEY])

        self.update_metadata()
        self._change_selection = False

    def update_metadata(self):
        run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
        run = self.service.get_run_by_id(run_id)
        self.run_display.header_data.clear()

        self.run_display.header_data.addItems([key for key in run.meta.keys()])

    def change_metadata(self):
        if len(self.service.get_runs()) == 0 or self.run_display.current_runs.currentItem() is None:
            return

        if self.run_display.header_data.currentText():
            run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
            run = self.service.get_run_by_id(run_id)
            key = self.run_display.header_data.currentText()
            value = run.meta[key]
            self.run_display.output_header_display.setText(str(value))

    def change_title(self):
        if len(self.service.get_runs()) == 0 or self.run_display.current_runs.currentItem() is None:
            return

        if self.run_display.current_runs.currentItem():
            run_id = self.run_id_title[self.run_display.current_runs.currentItem().text()]
            self.service.update_run_style(run_id, BeamsModel.STYLE_TITLE, self.run_display.current_runs.currentItem().text())

    def populate_run_display(self):
        runs = self.service.get_runs()
        if len(runs) != 0:
            self.run_display.current_runs.clear()
            self.run_display.output_current_file.setText(runs[0].filename)

            self.run_id_title = dict()
            for run in runs:
                self.run_id_title[run.meta[BeamsUtility.TITLE_KEY]] = run.run_id
                self.run_display.current_runs.addItem(run.meta[BeamsUtility.TITLE_KEY])

            for index in range(self.run_display.current_runs.count()):
                item = self.run_display.current_runs.item(index)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

            self.run_display.current_runs.setCurrentRow(0)

            self.run_display.marker_choices.setEnabled(True)
            self.run_display.color_choices.setEnabled(True)
            self.run_display.isolate_button.setEnabled(True)
            self.run_display.histograms.setEnabled(True)
            self.run_display.inspect_hist_button.setEnabled(True)
            self.run_display.inspect_file_button.setEnabled(True)
            self.run_display.plot_all_button.setEnabled(True)
            self.run_display.header_data.setEnabled(True)
            self.run_display.output_header_display.setEnabled(True)
            self.run_display.correction_button.setEnabled(True)
            self.run_display.input_alpha.setEnabled(True)
            self.run_display.integrate_choices.setEnabled(True)
            self.run_display.integrate_button.setEnabled(True)
        else:
            # self.run_display.color_choices.clear()
            # self.run_display.marker_choices.clear()
            self.run_display.header_data.clear()
            self.run_display.current_runs.clear()
            self.run_display.histograms.clear()
            self.run_display.output_current_file.clear()
            self.run_display.output_header_display.clear()
            self.run_display.input_alpha.clear()
            self.run_display.color_choices.setEnabled(False)
            self.run_display.isolate_button.setEnabled(False)
            self.run_display.histograms.setEnabled(False)
            self.run_display.inspect_hist_button.setEnabled(False)
            self.run_display.inspect_file_button.setEnabled(False)
            self.run_display.plot_all_button.setEnabled(False)
            self.run_display.header_data.setEnabled(False)
            self.run_display.output_header_display.setEnabled(False)
            self.run_display.correction_button.setEnabled(False)
            self.run_display.input_alpha.setEnabled(False)
            self.run_display.integrate_choices.setEnabled(False)
            self.run_display.integrate_button.setEnabled(False)

    def update(self, signal):
        self.populate_run_display()


class FormatterController:
    """ FormatterController paired with FileFormatterUI prompts the user to
            specify the formats for each file.

            Instantiated by FileManagerController class only."""
    def __init__(self, files=None, parent=None):
        if not parent or type(parent) is not FileManagerController:
            raise AttributeError('Parameter parent=FileManagerController not passed.')
            # FormatterController calls _prompt_histograms() in FileManagerController after GUI closes

        self.formatter_gui = BeamsViews.FileFormatterUI(filenames=files)
        self.parent_controller = parent
        self.service = BeamsModel.RunService()
        self._set_callbacks()
        self.formatter_gui.show()

    def _set_callbacks(self):
        self.formatter_gui.done_button.released.connect(lambda: self.b_done_formatting())

    def b_apply_formats(self, apply_all=False):
        pass

    def b_skip_file(self):
        pass

    @staticmethod
    def c_column_checked(check_box, input_box):
        input_box.setEnabled(check_box.isChecked())


class WriterController:
    def __init__(self, selected_files):
        self.writer_gui = BeamsViews.WriteDataUI()
        self.writer_gui.file_list.addItems(selected_files)

        self.service = BeamsModel.RunService()
        self.files = selected_files
        self.custom_file = False

        self.popup = None
        self.formats = None

        self._set_callbacks()
        self.writer_gui.show()

        for file in self.files:
            if self.service.get_run_id_by_filename(file) is None:
                message = 'Some of the files you\'ve selected haven\'t been read in yet. Would you like to now?'
                BeamsViews.PermissionsMessageUI(message, pos_function=self.read_files,
                                                neg_function=self.writer_gui.close)
                break

    def read_files(self):
        checked_files = {BeamsUtility.FileReader.BINARY_FILE: [],
                         BeamsUtility.FileReader.ASYMMETRY_FILE: [],
                         BeamsUtility.FileReader.HISTOGRAM_FILE: []}

        files = self.files.copy()
        for file_path in files:
            file = BeamsUtility.FileReader(file_path)
            checked_files[file.get_type()].append(file)
            if file.get_type() == BeamsUtility.FileReader.BINARY_FILE:
                self.files.remove(file_path)

        if len(checked_files[BeamsUtility.FileReader.BINARY_FILE]) != 0:
            BeamsViews.ErrorMessageUI(error_message='Can not write from binary file, you need to convert first.')

        if len(checked_files[BeamsUtility.FileReader.ASYMMETRY_FILE]) != 0:
            threading.Thread(target=self.service.update_run_list(checked_files[BeamsUtility.FileReader.ASYMMETRY_FILE])).start()

        if len(checked_files[BeamsUtility.FileReader.HISTOGRAM_FILE]) != 0:
            self.popup = PlotDataController(checked_files[BeamsUtility.FileReader.HISTOGRAM_FILE], plot=False)

    def _set_callbacks(self):
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
        for run in self.service.get_runs():
            if self.writer_gui.file_list.currentText() == run.filename or \
                    (all_files and run.filename in self.files):
                if self.custom_file:
                    file_path = self.writer_gui.input_filename.text()
                    if count:
                        file_path = os.path.splitext(file_path)[0]
                        file_path += '({}).asy'.format(count)
                else:
                    if 'RunNumber' in run.meta.keys():
                        file_path = os.path.split(run.filename)[0] + BeamsUtility.get_separator() \
                                    + str(run.meta['RunNumber']) + '.asy'
                    else:
                        file_path = os.path.splitext(run.filename)[0] + '.asy'

                if self.writer_gui.radio_binned.isChecked():
                    bin_size = float(self.writer_gui.radio_binned_size.text())
                    meta_string = BeamsUtility.TITLE_KEY + ":" + str(run.meta[BeamsUtility.TITLE_KEY]) + "," \
                                  + BeamsUtility.BIN_SIZE_KEY + ":" + str(bin_size) + "," \
                                  + BeamsUtility.TEMPERATURE_KEY + ":" + str(run.meta[BeamsUtility.TEMPERATURE_KEY]) + "," \
                                  + BeamsUtility.FIELD_KEY + ":" + str(run.meta[BeamsUtility.FIELD_KEY]) + "," \
                                  + BeamsUtility.T0_KEY + ":" + str(run.t0) + "\n"
                    asymmetry, time, uncertainty = self.service.get_run_binned(run.run_id, bin_size, False)
                    np.savetxt(file_path, np.c_[time, asymmetry, uncertainty],
                               fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "Time, Asymmetry, Uncertainty")
                elif self.writer_gui.radio_full.isChecked():
                    meta_string = BeamsUtility.TITLE_KEY + ":" + str(run.meta[BeamsUtility.TITLE_KEY]) + "," \
                                  + BeamsUtility.BIN_SIZE_KEY + ":" + str(run.meta[BeamsUtility.BIN_SIZE_KEY]) + "," \
                                  + BeamsUtility.TEMPERATURE_KEY + ":" + str(run.meta[BeamsUtility.TEMPERATURE_KEY]) + "," \
                                  + BeamsUtility.FIELD_KEY + ":" + str(run.meta[BeamsUtility.FIELD_KEY]) + "," \
                                  + BeamsUtility.T0_KEY + ":" + str(run.t0) + "\n"
                    np.savetxt(file_path, np.c_[run.time, run.asymmetry, run.uncertainty],
                               fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "Time, Asymmetry, Uncertainty")
                else:
                    print('FFT not supported.')
                count += 1

    def remove_file(self):
        self.writer_gui.file_list.removeItem(self.writer_gui.file_list.currentIndex())


class PlotDataController:
    """ PlotDataController paired with PlotDataUI prompts the user to specify which histograms
            will be used to calculate the asymmetry for each file.

            Instantiated by FileManagerController class only."""
    def __init__(self, files=None, plot=True):
        """ Instantiates an object of the PlotDataController class, connects it to the PlotDataGUI
                and its calling class (FileManagerController). """

        self.plot_data_gui = BeamsViews.PlotDataUI()
        self.plot = plot
        self.service = BeamsModel.RunService()
        self.files = files

        self._set_callbacks()
        self.plot_data_gui.c_file_list.addItems([file.get_file_path() for file in self.files])

        self.plot_data_gui.show()

    def _set_callbacks(self):
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
            for file in self.files:
                file.get_meta()['CalcHists'] = calc_hists

        # Else only save it with the current file
        else:
            file_path = self.plot_data_gui.c_file_list.currentText()
            for file in self.files:
                if file.get_file_path() == file_path:
                    file.get_meta()['CalcHists'] = calc_hists

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
        threading.Thread(target=self.service.update_run_list(self.files, self.plot), daemon=True).start()

    def remove_file(self):
        """ Removes the currently selected file from the file list and from the format list. """
        for file in self.files:
            if file.get_file_path() == self.plot_data_gui.c_file_list.currentText():
                self.files.remove(file)
        self.plot_data_gui.c_file_list.removeItem(self.plot_data_gui.c_file_list.currentIndex())

    def file_changed(self):
        """ Changes the histograms displayed to match the currently selected file. """
        self.plot_data_gui.c_hist_one.clear()
        self.plot_data_gui.c_hist_two.clear()

        if self.plot_data_gui.c_file_list.currentText():  # Stop displaying if no files left in file list
            for file in self.files:
                if file.get_file_path() == self.plot_data_gui.c_file_list.currentText():
                    self.plot_data_gui.c_hist_one.addItems(file.get_meta()['HistTitles'])
                    self.plot_data_gui.c_hist_two.addItems(file.get_meta()['HistTitles'])


class SavePlotController:
    def __init__(self, canvases=None):
        self.save_plot_gui = BeamsViews.SavePlotUI()
        self.canvases = canvases
        self.extension_filters = self.get_supported_extensions()

        self.save_plot_gui.save_button.released.connect(self._save_plots)
        self.save_plot_gui.show()

    def get_supported_extensions(self):
        extensions = self.canvases[0].get_supported_filetypes().keys()
        extension_filters = ";;"
        extension_list = []

        [(extension_list.append("{}(*.{})".format(str(ext).upper(), ext))) for ext in extensions]
        extension_filters = extension_filters.join(extension_list)

        return extension_filters

    def _save_plots(self):
        if self.save_plot_gui.left_radio.isChecked():  # Setting the current figure to left or right (1 or 2)
            figure = self.canvases[0].figure
        elif self.save_plot_gui.right_radio.isChecked():
            figure = self.canvases[1].figure
        else:
            BeamsViews.ErrorMessageUI(error_message='You need to select a plot.')
            return

        saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self.save_plot_gui, 'Specify file', os.getcwd(),
                                                                filter=self.extension_filters)[0]
        if not saved_file_path:
            return

        try:
            figure.savefig(saved_file_path)
        except ValueError:
            BeamsViews.ErrorMessageUI(error_message='Invalid save file type.')
        else:
            self.save_plot_gui.close()


class WebServiceController:
    def __init__(self):
        self.dialog = BeamsViews.WebDownloadUI()
        self.service = BeamsModel.RunService()
        self._search_url = "http://musr.ca/mud/runSel.php"
        self._data_url = "http://musr.ca/mud/data/"

        self._set_callbacks()

        self.dialog.show()

    def _set_callbacks(self):
        self.dialog.search_button.released.connect(lambda: self.query())
        self.dialog.download_button.released.connect(lambda: self.download())
        self.dialog.done_button.released.connect(lambda: self.done())
        self.dialog.select_button.released.connect(lambda: self.save_to())

    def _assemble_query(self):
        query = "?"

        area = self.dialog.input_area.text()
        if len(area) > 0:
            query += "area={}&".format(area)

        year = self.dialog.input_year.text()
        if len(year) > 0:
            if len(year) == 4:
                try:
                    int(year)
                except ValueError:
                    self.dialog.output_web.insertPlainText("Give year as 4 digits.\n")
                    return
                query += "year={}&".format(year)
            else:
                self.dialog.output_web.insertPlainText("Give year as 4 digits.\n")
                return

        expt = self.dialog.input_expt.text()
        if len(expt) > 0:
            try:
                int(expt)
            except ValueError:
                self.dialog.output_web.insertPlainText("Experiment number should be an integer.\n")
                return
            query += "expt={}&".format(expt)

        runs = self.dialog.input_runs.text()
        if len(runs) > 0:
            if len(runs.split('-')) > 1 or len(runs) > 6:
                self.dialog.output_web.insertPlainText("Run number for search can not be a range, "
                                                       "must be single 6 digit maximum integer.\n")
                return
            try:
                int(runs)
            except ValueError:
                self.dialog.output_web.insertPlainText("Run number must be a six digit max integer.\n")
                return
            query += "run={}&".format(runs)

        return query

    def _assemble_downloads(self):
        download_string = ""

        area = self.dialog.input_area.text()
        if len(area) == 0:
            return
        download_string += "{}/".format(area)

        year = self.dialog.input_year.text()
        if len(year) == 0:
            return
        download_string += "{}/".format(year)

        runs = self.dialog.input_runs.text()
        if len(runs) == 0:
            return

        runs = runs.split('-')
        if len(runs) == 1:
            download_string += '{0:06d}.msr'.format(int(runs[0]))
            return [download_string]

        return [download_string + '{0:06d}.msr'.format(download) for download in range(int(runs[0]), int(runs[1])+1)]

    def _assemble_save(self, download):
        directory = self.dialog.input_file.text()

        if len(directory) == 0:
            directory = os.getcwd()

        return directory + "{}{}".format(BeamsUtility.get_separator(), download.split('/')[-1])

    def query(self):
        query = self._assemble_query()

        if query is None:
            return

        if len(query) < 2:
            self.dialog.output_web.insertPlainText("No query parameters filled.\n")
        else:
            self.dialog.output_web.insertPlainText("Sending query : {}\n".format(query))

        full_url = self._search_url + query

        try:
            response = requests.get(full_url)
        except requests.exceptions.ConnectionError:
            self.dialog.output_web.insertPlainText("Error: Check your internet connection.\n")
            return

        if response.status_code != 200:
            self.dialog.output_web.insertPlainText("Error : {}\n".format(response.status_code))
            return

        printed_response = False
        for x in response.text.split('TR>'):
            y = x.split('<TD')
            if len(y) > 2:
                year = y[2][1:5]
                area = y[3].split('<i>')[1].split('</i>')[0]
                expt = y[4].split('>')[1].split('<')[0]
                expt_type = y[5].split('>')[3].split('<')[0]
                run_numbers = y[6].split('"')
                if len(run_numbers) > 4:
                    run_number = run_numbers[3].split()[2]
                    self.dialog.output_web.insertPlainText('{}  Year: {}, Area: {}, '
                                                           'Expt: {}, Type: {}\n'.format(run_number, year, area,
                                                                                         expt, expt_type))
                    printed_response = True
                    
        if not printed_response:
            self.dialog.output_web.insertPlainText("No runs found.")

    def download(self):
        downloads = self._assemble_downloads()
        if downloads is None:
            self.dialog.output_web.insertPlainText('No runs specified.\n')
            return

        good = 0
        for i, download in enumerate(downloads):
            full_url = self._data_url + download

            try:
                response = requests.get(full_url)
            except requests.exceptions.ConnectionError:
                self.dialog.output_web.insertPlainText('Failed to download {}. Connection Error\n'.format(full_url))
                continue

            if response.status_code != 200:
                self.dialog.output_web.insertPlainText('Failed to download {}. Error {}\n'.format(full_url,
                                                                                                  response.status_code))
                continue

            save_file = self._assemble_save(download)
            print(save_file)
            with open(save_file, 'wb') as fb:
                for chunk in response.iter_content(100000):
                    fb.write(chunk)

            self.service.update_file_list([save_file], remove=False)

            self.dialog.output_web.insertPlainText('Successfully downloaded {}.\n'.format(full_url))
            good += 1

        self.dialog.output_web.insertPlainText('{}/{} Files downloaded successfully.\n'.format(good, len(downloads)))

    def done(self):
        self.dialog.close()

    def save_to(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(caption='Select directory to save MUD files to',)
        if path:
            self.dialog.input_file.setText(path)
