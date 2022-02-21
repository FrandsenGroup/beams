# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
a = Analysis(['__main__.py'],
             pathex=[],
             binaries=[
                ('app/resources/binaries/*', 'app/resources/binaries')
             ],
             datas=[
                ('app/resources/icons/*', 'app/resources/icons'),
                ('app/resources/fonts/*', 'app/resources/fonts'),
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='beams',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          uac_admin=True,
          icon="app/resources/icons/icon.ico")

app = BUNDLE(exe,
         name='beams.app',
         icon='app/resources/icons/icon.icns',
         bundle_identifier=None)