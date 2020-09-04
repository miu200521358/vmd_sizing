cls

cd /d %~dp0

rem -- 行プロファイル用
kernprof -l setup.py build_ext --inplace


rem -- 通常用
rem python setup.py build_ext --inplace

cd ..
