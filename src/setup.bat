cls

cd /d %~dp0

python setup.py clean --all

python setup.py build_ext --inplace

cd ..
