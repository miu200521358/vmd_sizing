#-----------------------------------------------------------------------------
# Copyright (c) 2013-2018, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------
# exeサイズ削減のため、binariesをコンパイル対象に含めない
# "<Anacondaインストールパス>\envs\vmdsizing_inst_32\Lib\site-packages\PyInstaller\hooks\hook-PyQt5.QtGui.py"に配置
# "<Anacondaインストールパス>\envs\vmdsizing_inst_64\Lib\site-packages\PyInstaller\hooks\hook-PyQt5.QtGui.py"に配置
from PyInstaller.utils.hooks import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
binaries = []
