# -*- mode: python -*-

block_cipher = None

a = Analysis(['WorkLog.py'],
             pathex=['.'],
             binaries=[],
             datas=[
              ('icon/app.png', 'icon'),
              ('icon/calendar.png', 'icon'),
              ('icon/exit.png', 'icon'),
              ('icon/project.png', 'icon'),
              ('icon/settings.png', 'icon'),
              ('icon/today.png', 'icon'),
              ('icon/week.png', 'icon'),
              ('icon/working.png', 'icon'),
              ('icon/WorkLog.png', 'icon'),
              ('icon/workstate.png', 'icon'),
             ],
             hiddenimports=[
                 'hiddenimports'
             ],
             hookspath=[],
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
          name='WorkLog',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='WorkLog')
