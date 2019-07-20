@echo off
rem --- 
rem ---  VMDサイジングのテストケース実行処理
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

rem ---  python 実行
python test/test_utils.py
python test/test_arm_ik.py
python test/test_morph.py

