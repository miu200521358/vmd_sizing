# -*- coding: utf-8 -*-
# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\executor.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['wx._adv', 'wx._html', 'pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['mkl','libopenblas'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.datas += [('.\\src\\vmdsizing.ico','.\\src\\vmdsizing.ico', 'Data')]
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='VmdSizing_5.00_β47_64bit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='.\\src\\vmdsizing.ico')

