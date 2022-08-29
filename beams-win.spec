# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['beams\\__main__.py'],
             pathex=['beams'],
             binaries=[],
             datas=[('beams/app/resources/icons/*', 'app/resources/icons'), ('beams/app/resources/fonts/*', 'app/resources/fonts'), ('beams/app/resources/binaries/*', 'app/resources/binaries')],
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
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='beams\\app\\resources\\icons\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='beams')
