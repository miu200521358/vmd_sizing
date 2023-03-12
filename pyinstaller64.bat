@echo off
rem --- 
rem ---  exe�𐶐�
rem --- 

rem ---  �J�����g�f�B���N�g�������s��ɕύX
cd /d %~dp0

cls

activate vmdsizing_cython && src\setup_install.bat && pyinstaller --clean vmdising_np64.spec && copy /y archive\Readme.txt dist\Readme.txt && copy /y archive\����Readme.txt dist\����Readme.txt



