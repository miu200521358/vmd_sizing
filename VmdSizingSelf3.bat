@echo off
rem --- 
rem ---  vmdデータのトレースモデルを変換
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls


rem set REPLACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク_盗賊つばき流Ｍトレースモデル配布 v1.07\Tda式初音ミク_盗賊つばき流Mトレースモデルv1.07.pmx"
set REPLACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\_VMDサイジング\8頭身審神者 猫のしもべ\8頭身審神者3.pmx"
rem set REPLACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ゲーム\ドラクエ\竜酸式グレイグ配布用_1.09.3\竜酸式グレイグ_1.09.3.pmx"

set VMD_PATH="E:\MMD\MikuMikuDance_v926x64\Work\202001_sizing\ひじ分離\nac_aikotoba3_腕系のみ_0-1000.vmd"
rem set VMD_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\愛言葉III なつき\nac_aikotoba3_0-500_操作中心.vmd"
rem set VMD_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\愛言葉III なつき\nac_aikotoba3.vmd"
rem set VMD_PATH="E:\MMD\MikuMikuDance_v926x64\Work\202001_sizing\ひじ分離\右ひじグルグル_test_20200210.vmd"
set TRACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\らぶ式ミク\らぶ式ミク_準標準.pmx"

rem set VMD_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\おねがいダーリン_モーションv1.2 hino\おねがいダーリン_Lat式.vmd"
rem set TRACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Lat式ミクVer2.31\Lat式ミクVer2.31_Sailor夏服_準標準.pmx"

set VMD_PATH="E:\MMD\MikuMikuDance_v926x64\Work\202001_sizing\ひじ分離\udez_less.vmd"
set TRACE_PMX_PATH="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\_VMDサイジング\fumizuki_14th_shirt\文月14歳_シャツ.pmx"

set ALTERNATIVE_MODEL=0
set ADD_DELEGATE=1
set VERBOSE=3

set AVOIDANCE=0
set AVOIDANCE_FINGER=0
set HAND_IK=0
set HAND_DISTANCE=0
set FLOOR_HAND=0
set FLOOR_HAND_UP=0
set FLOOR_HAND_DOWN=0
set HAND_FLOOR_DISTANCE=0
set LEG_FLOOR_DISTANCE=0
set FINGER_IK=0
set FINGER_DISTANCE=0
set VMD_CHOICE_VALUES=
set REP_CHOICE_VALUES=
set REP_RATE_VALUES=
set CAMERA_VMD_PATH=
set CAMERA_PMX_PATH=
set CAMERA_Y_OFFSET=0
set TARGET_AVOIDANCE_RIGIDS=
set TARGET_AVOIDANCE_BONES=
set TEST_PARAM=

python src\wrapper.py --vmd_path %VMD_PATH% --trace_pmx_path %TRACE_PMX_PATH% --replace_pmx_path %REPLACE_PMX_PATH% --avoidance "%AVOIDANCE%" --avoidance_finger "%AVOIDANCE_FINGER%" --hand_ik "%HAND_IK%" --hand_distance "%HAND_DISTANCE%" --floor_hand "%FLOOR_HAND%" --floor_hand_up "%FLOOR_HAND_UP%" --floor_hand_down "%FLOOR_HAND_DOWN%" --hand_floor_distance "%HAND_FLOOR_DISTANCE%" --leg_floor_distance "%LEG_FLOOR_DISTANCE%" --finger_ik "%FINGER_IK%" --finger_distance "%FINGER_DISTANCE%" --vmd_choice_values "%VMD_CHOICE_VALUES%" --rep_choice_values "%REP_CHOICE_VALUES%" --rep_rate_values "%REP_RATE_VALUES%" --camera_vmd_path "%CAMERA_VMD_PATH%" --camera_pmx_path "%CAMERA_PMX_PATH%" --camera_y_offset "%CAMERA_Y_OFFSET%" --output_path "%OUTPUT_PATH%" --alternative_model "%ALTERNATIVE_MODEL%" --add_delegate "%ADD_DELEGATE%" --target_avoidance_rigids "%TARGET_AVOIDANCE_RIGIDS%" --target_avoidance_bones "%TARGET_AVOIDANCE_BONES%" --test_param "%TEST_PARAM%" --verbose "%VERBOSE%" --output_path ""

