@echo off
cls

cd /d %~dp0

python setup_install.py clean

python setup_install.py build_ext --force --inplace

cd ..
