"""
Stores constants for the paths of all our non-python resource files.
"""

from pathlib import Path
import os

# Using Path from pathlib is an easy way to fix the slash direction issue when switch between windows and unix systems.
LOGO_IMAGE = str(Path('beams/app/resources/icons/logo_3.jpg'))
MAXIMIZE_IMAGE = str(Path('beams/app/resources/icons/maximize_black.png'))
MINIMIZE_IMAGE = str(Path('beams/app/resources/icons/minimize_black.png'))
RESTORE_IMAGE = str(Path('beams/app/resources/icons/restore_black.png'))
CLOSE_IMAGE = str(Path('beams/app/resources/icons/close_black.png'))
SPLASH_IMAGE = str(Path('beams/app/resources/icons/splash.jpg'))
PLOTTING_IMAGE = str(Path('beams/app/resources/icons/plotting_icon.png'))
HISTOGRAM_IMAGE = str(Path('beams/app/resources/icons/histo_icon.png'))
FITTING_IMAGE = str(Path('beams/app/resources/icons/fitting_icon.png'))
DOWNLOAD_IMAGE = str(Path('beams/app/resources/icons/download_icon.png'))
QUESTION_IMAGE = str(Path('beams/app/resources/icons/question_icon.png'))
PLOTTING_CLICKED_IMAGE = str(Path('beams/app/resources/icons/plotting_icon_clicked.png'))
HISTOGRAM_CLICKED_IMAGE = str(Path('beams/app/resources/icons/histo_icon_clicked.png'))
FITTING_CLICKED_IMAGE = str(Path('beams/app/resources/icons/fitting_icon_clicked.png'))
DOWNLOAD_CLICKED_IMAGE = str(Path('beams/app/resources/icons/download_icon_clicked.png'))
QUESTION_CLICKED_IMAGE = str(Path('beams/app/resources/icons/question_icon_clicked.png'))
MENU_IMAGE = str(Path('beams/app/resources/icons/menu_icon.png'))
LOADING_GIF = str(Path('beams/app/resources/icons/loading.gif'))

LATO_BLACK_FONT = str(Path('beams/app/resources/Lato/Lato-Black.ttf'))
LATO_BLACK_ITALIC_FONT = str(Path('beams/app/resources/Lato/Lato-BlackItalic.ttf'))
LATO_BOLD_FONT = str(Path('beams/app/resources/Lato/Lato-Bold.ttf'))
LATO_BOLD_ITALIC_FONT = str(Path('beams/app/resources/Lato/Lato-BoldItalic.ttf'))
LATO_ITALIC_FONT = str(Path('beams/app/resources/Lato/Lato-Italic.ttf'))
LATO_LIGHT_FONT = str(Path('beams/app/resources/Lato/Lato-Light.ttf'))
LATO_LIGHT_ITALIC_FONT = str(Path('beams/app/resources/Lato/Lato-LightItalic.ttf'))
LATO_REGULAR_FONT = str(Path('beams/app/resources/Lato/Lato-Regular.ttf'))
LATO_THIN_FONT = str(Path('beams/app/resources/Lato/Lato-Thin.ttf'))
LATO_THIN_ITALIC_FONT = str(Path('beams/app/resources/Lato/Lato-ThinItalic.ttf'))

QSS_STYLE_SHEET = str(Path('beams/app/resources/light_style.qss'))
STYLE_SHEET_VARIABLES = str(Path('beams/app/resources/light_style_vars.txt'))

PSI_LINUX_CONVERSION = str(Path('/beams/app/resources/mud/PSI_LINUX'))
PSI_WINDOWS_CONVERSION = str(Path('/beams/app/resources/mud/PSI_WINDOWS.exe'))
TRIUMF_LINUX_CONVERSION = str(Path('/beams/app/resources/mud/TRIUMF_LINUX'))
TRIUMF_MAC_CONVERSION = str(Path('/beams/app/resources/mud/TRIUMF_MAC'))
TRIUMF_WINDOWS_CONVERSION = str(Path('/beams/app/resources/mud/TRIUMF_WINDOWS.exe'))


try:
    CONFIGURATION_FILE = str(Path('beams/app/resources/app.config'))

    if not os.path.exists(CONFIGURATION_FILE):
        with open(CONFIGURATION_FILE, 'w+') as f:
            pass

    QT_LOG_FILE = str(Path('beams/app/resources/qt.log'))

    with open(QT_LOG_FILE, 'w') as fp:
        fp.truncate(0)
except FileNotFoundError:
    CONFIGURATION_FILE = str(Path('app.config'))

    if not os.path.exists(CONFIGURATION_FILE):
        with open(CONFIGURATION_FILE, 'w+') as f:
            pass

    QT_LOG_FILE = str(Path('qt.log'))

    with open(QT_LOG_FILE, 'w') as fp:
        fp.truncate(0)