@echo off
rem --- 
rem ---  スムージング
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

set MOTION_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\愛言葉III なつき\nac_aikotoba3_300-468_らぶ式ミク_準標準_T_20200917_222601.vmd"
set MODEL_PATH=D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\らぶ式ミク\らぶ式ミク_準標準.pmx
set LOOP_CNT=2
set INTERPOLATION=0
set BONE_LIST="右腕;右腕捩;右ひじ;右手捩;右手首;左腕;左腕捩;左ひじ;左手捩;左手首;"
rem set BONE_LIST="右ひじ"
rem set BONE_LIST="右腕"
rem set BONE_LIST="左手首"

set VERBOSE="10"


activate vmdsizing_cython && src\setup.bat && python src/executor_smooth.py --motion_path %MOTION_PATH%  --model_path %MODEL_PATH%  --loop_cnt %LOOP_CNT%  --interpolation %INTERPOLATION%  --bone_list %BONE_LIST% --verbose %VERBOSE% 


