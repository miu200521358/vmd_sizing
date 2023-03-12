# -*- coding: utf-8 -*-
# -*- mode: python -*-
# VMDサイジング 64bit版

exclude_keys = ['mkl', 'tkinter', 'win32comgenpy', 'traitlets', 'PIL', 'IPython', 'pydoc', 'lib2to3', 'pygments', 'matplotlib', 'libopenblas64']
exclude_dlls = ['mfc140u.dll', 'libcrypto-1_1-x64.dll', 'libssl-1_1-x64.dll', '_multiarray_umath.cp39-win_amd64.pyd', '_multiarray_tests.cp38-win_amd64.pyd', '_multiarray_tests.cp39-win_amd64.pyd']
include_dlls = []

def remove_from_list(input):
    outlist = []
    for item in sorted(input):
        name, _, _ = item
        flag = 0
        for exclude_key in exclude_keys:
            if (exclude_key in name or name in exclude_dlls) and name not in include_dlls:
                flag = 1
        print(f"{' OK ' if not flag else '*NG*'} [{name}] = {flag}")
        if flag != 1:
            outlist.append(item)
    return outlist

a = Analysis(['src\\executor.py'],
             pathex=['src'],
             binaries=[],
             datas=[('src\\vmdsizing.ico', 'src')],
             hiddenimports=['pkg_resources', 'wx._adv', 'wx._html', 'bezier', 'quaternion', 'module.MParams', 'numpy.core.multiarray'],
             hookspath=[],
             runtime_hooks=[],
             excludes=exclude_keys,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)

print('scripts -----')
a.scripts = remove_from_list(a.scripts)
# print([(f" - {s}\n") for s in a.scripts])

print('binaries -----')
a.binaries = remove_from_list(a.binaries)
# print([(f" - {s}\n") for s in a.binaries])

print('zipfiles -----')
a.zipfiles = remove_from_list(a.zipfiles)
# print([(f" - {s}\n") for s in a.zipfiles])

print('datas -----')
a.datas = remove_from_list(a.datas)
# print([(f" - {s}\n") for s in a.datas])

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='VmdSizing_5.01.09_β01_64bit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='.\\src\\vmdsizing.ico')
