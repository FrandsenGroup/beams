"""
Stores constants for the paths of all our non-python resource files.
"""

from pathlib import Path
import os
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath("./beams")

    return os.path.join(base_path, relative_path)


# Using Path from pathlib is an easy way to fix the slash direction issue when switch between windows and unix systems.
LOGO_IMAGE = resource_path(str(Path('app/resources/icons/logo_3.jpg')))
MAXIMIZE_IMAGE = resource_path(str(Path('app/resources/icons/maximize_black.png')))
MINIMIZE_IMAGE = resource_path(str(Path('app/resources/icons/minimize_black.png')))
RESTORE_IMAGE = resource_path(str(Path('app/resources/icons/restore_black.png')))
CLOSE_IMAGE = resource_path(str(Path('app/resources/icons/close_black.png')))
SPLASH_IMAGE = resource_path(str(Path('app/resources/icons/splash.jpg')))
PLOTTING_IMAGE = resource_path(str(Path('app/resources/icons/plotting_icon.png')))
HISTOGRAM_IMAGE = resource_path(str(Path('app/resources/icons/histo_icon.png')))
FITTING_IMAGE = resource_path(str(Path('app/resources/icons/fitting_icon.png')))
DOWNLOAD_IMAGE = resource_path(str(Path('app/resources/icons/download_icon.png')))
QUESTION_IMAGE = resource_path(str(Path('app/resources/icons/question_icon.png')))
PLOTTING_CLICKED_IMAGE = resource_path(str(Path('app/resources/icons/plotting_icon_clicked.png')))
HISTOGRAM_CLICKED_IMAGE = resource_path(str(Path('app/resources/icons/histo_icon_clicked.png')))
FITTING_CLICKED_IMAGE = resource_path(str(Path('app/resources/icons/fitting_icon_clicked.png')))
DOWNLOAD_CLICKED_IMAGE = resource_path(str(Path('app/resources/icons/download_icon_clicked.png')))
QUESTION_CLICKED_IMAGE = resource_path(str(Path('app/resources/icons/question_icon_clicked.png')))
MENU_IMAGE = resource_path(str(Path('app/resources/icons/menu_icon.png')))
LOADING_GIF = resource_path(str(Path('app/resources/icons/loading.gif')))

LATO_BLACK_FONT = resource_path(str(Path('app/resources/fonts/fonts-Black.ttf')))
LATO_BLACK_ITALIC_FONT = resource_path(str(Path('app/resources/fonts/fonts-BlackItalic.ttf')))
LATO_BOLD_FONT = resource_path(str(Path('app/resources/fonts/fonts-Bold.ttf')))
LATO_BOLD_ITALIC_FONT = resource_path(str(Path('app/resources/fonts/fonts-BoldItalic.ttf')))
LATO_ITALIC_FONT = resource_path(str(Path('app/resources/fonts/fonts-Italic.ttf')))
LATO_LIGHT_FONT = resource_path(str(Path('app/resources/fonts/fonts-Light.ttf')))
LATO_LIGHT_ITALIC_FONT = resource_path(str(Path('app/resources/fonts/fonts-LightItalic.ttf')))
LATO_REGULAR_FONT = resource_path(str(Path('app/resources/fonts/fonts-Regular.ttf')))
LATO_THIN_FONT = resource_path(str(Path('app/resources/fonts/fonts-Thin.ttf')))
LATO_THIN_ITALIC_FONT = resource_path(str(Path('app/resources/fonts/fonts-ThinItalic.ttf')))

PSI_LINUX_CONVERSION = resource_path(str(Path('app/resources/binaries/PSI_LINUX')))
PSI_WINDOWS_CONVERSION = resource_path(str(Path('app/resources/binaries/PSI_WINDOWS.exe')))
TRIUMF_LINUX_CONVERSION = resource_path(str(Path('app/resources/binaries/TRIUMF_LINUX')))
TRIUMF_MAC_CONVERSION = resource_path(str(Path('app/resources/binaries/TRIUMF_MAC')))
TRIUMF_WINDOWS_CONVERSION = resource_path(str(Path('app/resources/binaries/TRIUMF_WINDOWS.exe')))

DARK_COLOR = '#19232D'
LIGHT_COLOR = '#FAFAFA'

CONFIGURATION_FILE = resource_path(str(Path('app/app.config')))

if not os.path.exists(CONFIGURATION_FILE):
    with open(CONFIGURATION_FILE, 'w+') as f:
        pass
