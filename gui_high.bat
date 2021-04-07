@echo off
rem --- 
rem ---  vmdデータのトレースモデルを変換
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

activate vmdsizing_cython && src\setup.bat && python src\executor.py --out_log 1 --verbose 20 --is_saving 0

