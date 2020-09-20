from pathlib import Path
import os
import stat

LOGO_IMAGE = str(Path('beams/app/resources/icons/logo_3.jpg'))
MAXIMIZE_IMAGE = str(Path('beams/app/resources/icons/maximize_black.png'))
MINIMIZE_IMAGE = str(Path('beams/app/resources/icons/minimize_black.png'))
RESTORE_IMAGE = str(Path('beams/app/resources/icons/restore_black.png'))
CLOSE_IMAGE = str(Path('beams/app/resources/icons/close_black.png'))
SPLASH_IMAGE = str(Path('beams/app/resources/icons/splash.jpg'))

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

Path('./beams/app/resources/mud/PSI_LINUX').chmod(stat.S_IEXEC)
Path('./beams/app/resources/mud/PSI_WINDOWS.exe').chmod(stat.S_IEXEC)
Path('./beams/app/resources/mud/TRIUMF_LINUX').chmod(stat.S_IEXEC)
Path('./beams/app/resources/mud/TRIUMF_MAC').chmod(stat.S_IEXEC)
Path('./beams/app/resources/mud/TRIUMF_WINDOWS.exe').chmod(stat.S_IEXEC)

CONFIGURATION_FILE = str(Path('beams/app/resources/config.txt'))
with open(CONFIGURATION_FILE, 'w+') as f:
    pass
