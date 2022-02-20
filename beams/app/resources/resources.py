"""
Stores constants for the paths of all our non-python resource files.
"""

from pathlib import Path
import os

DEVELOPMENT_PATH = str(Path('beams/app/resources'))
PRODUCTION_PATH = str(Path('resources'))

CURRENT_PATH = DEVELOPMENT_PATH if os.path.exists(DEVELOPMENT_PATH) else PRODUCTION_PATH


# Using Path from pathlib is an easy way to fix the slash direction issue when switch between windows and unix systems.
LOGO_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/logo_3.jpg')))
MAXIMIZE_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/maximize_black.png')))
MINIMIZE_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/minimize_black.png')))
RESTORE_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/restore_black.png')))
CLOSE_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/close_black.png')))
SPLASH_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/splash.jpg')))
PLOTTING_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/plotting_icon.png')))
HISTOGRAM_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/histo_icon.png')))
FITTING_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/fitting_icon.png')))
DOWNLOAD_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/download_icon.png')))
QUESTION_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/question_icon.png')))
PLOTTING_CLICKED_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/plotting_icon_clicked.png')))
HISTOGRAM_CLICKED_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/histo_icon_clicked.png')))
FITTING_CLICKED_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/fitting_icon_clicked.png')))
DOWNLOAD_CLICKED_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/download_icon_clicked.png')))
QUESTION_CLICKED_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/question_icon_clicked.png')))
MENU_IMAGE = os.path.join(CURRENT_PATH, str(Path('icons/menu_icon.png')))
LOADING_GIF = os.path.join(CURRENT_PATH, str(Path('icons/loading.gif')))

LATO_BLACK_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Black.ttf')))
LATO_BLACK_ITALIC_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-BlackItalic.ttf')))
LATO_BOLD_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Bold.ttf')))
LATO_BOLD_ITALIC_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-BoldItalic.ttf')))
LATO_ITALIC_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Italic.ttf')))
LATO_LIGHT_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Light.ttf')))
LATO_LIGHT_ITALIC_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-LightItalic.ttf')))
LATO_REGULAR_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Regular.ttf')))
LATO_THIN_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-Thin.ttf')))
LATO_THIN_ITALIC_FONT = os.path.join(CURRENT_PATH, str(Path('fonts/fonts-ThinItalic.ttf')))

PSI_LINUX_CONVERSION = os.path.join(CURRENT_PATH, str(Path('binaries/PSI_LINUX')))
PSI_WINDOWS_CONVERSION = os.path.join(CURRENT_PATH, str(Path('binaries/PSI_WINDOWS.exe')))
TRIUMF_LINUX_CONVERSION = os.path.join(CURRENT_PATH, str(Path('binaries/TRIUMF_LINUX')))
TRIUMF_MAC_CONVERSION = os.path.join(CURRENT_PATH, str(Path('binaries/TRIUMF_MAC')))
TRIUMF_WINDOWS_CONVERSION = os.path.join(CURRENT_PATH, str(Path('binaries/TRIUMF_WINDOWS.exe')))

DARK_COLOR = '#19232D'
LIGHT_COLOR = '#FAFAFA'

try:
    CONFIGURATION_FILE = os.path.join(CURRENT_PATH, str(Path('app.config')))

    if not os.path.exists(CONFIGURATION_FILE):
        with open(CONFIGURATION_FILE, 'w+') as f:
            pass

    LOG_FILE = os.path.join(CURRENT_PATH, str(Path('beams.log')))

    with open(LOG_FILE, 'w') as fp:
        fp.truncate(0)
except FileNotFoundError:
    CONFIGURATION_FILE = str(Path('app.config'))

    if not os.path.exists(CONFIGURATION_FILE):
        with open(CONFIGURATION_FILE, 'w+') as f:
            pass

    LOG_FILE = str(Path('beams.log'))

    with open(LOG_FILE, 'w') as fp:
        fp.truncate(0)
