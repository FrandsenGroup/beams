# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
a = Analysis(['__main__.py'],
             pathex=[],
             binaries=[
                ('app/resources/binaries/*', 'resources/binaries')
             ],
             datas=[
                ('app/resources/icons/*', 'resources/icons'),
                ('app/resources/fonts/*', 'resources/fonts'),
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
          [],
          exclude_binaries=True,
          name='beams',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

app = BUNDLE(exe,
         name='beams.app',
         icon=None,
         bundle_identifier=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='beams')