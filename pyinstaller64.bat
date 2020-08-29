@echo off
rem --- 
rem ---  exeを生成
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

rem activate vmdsizing_cython_exe1 && src\setup_install.bat && pyinstaller --clean vmdising_np64.spec

pyinstaller --clean vmdising_np64.spec

