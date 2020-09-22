@echo off
cls

cd /d %~dp0

rem -- 行プロファイル用
rem kernprof -l setup.py build_ext --inplace


rem -- 通常用
python setup.py build_ext --inplace

cd ..
