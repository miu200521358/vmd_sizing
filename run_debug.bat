@echo off
rem --- 
rem ---  vmdデータのトレースモデルを変換
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

src\setup.bat && activate vmdsizing_cython && python src\executor.py --out_log 1 --verbose 10 --is_saving 1

