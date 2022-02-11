@echo off
rem --- 
rem ---  exeを生成
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

activate vmdsizing_cython && src\setup_install.bat && pyinstaller --clean vmdising_np64.spec && copy /y archive\Readme.txt dist\Readme.txt && copy /y archive\β版Readme.txt dist\β版Readme.txt


