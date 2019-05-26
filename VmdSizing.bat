@echo off
rem --- 
rem ---  vmdデータのトレースモデルを変換
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

rem ---  入力vmdファイルパス
echo 調整するvmdファイルのフルパスを指定して下さい。
echo この設定は必須項目です。
set INPUT_VMD=
set /P INPUT_VMD=■調整対象vmdファイルパス: 
rem echo INPUT_VMD：%INPUT_VMD%

IF /I "%INPUT_VMD%" EQU "" (
    ECHO 調整対象vmdファイルパスが設定されていないため、処理を中断します。
    EXIT /B
)


rem ---  トレース元モデルPMXファイル
echo --------------
set MODEL_PMX=born\あにまさ式ミク準標準.csv
echo トレース元モデルのPMXファイルの相対パスを入力して下さい。
echo 何も入力せず、ENTERを押下した場合、「%MODEL_PMX%」のファイルを読み込みます。
set /P MODEL_PMX="■トレース元モデルPMXファイル: "

rem ---  トレース変換先モデルPMXファイル
echo --------------
set REPLACE_MODEL_PMX=born\あにまさ式ミク準標準.csv
echo トレース変換先モデルのPMXファイルの相対パスを入力して下さい。
echo 何も入力せず、ENTERを押下した場合、「%REPLACE_MODEL_PMX%」のファイルを読み込みます。
set /P REPLACE_MODEL_PMX="■トレース変換先モデルPMXファイル: "


rem ---  頂点回避有無

echo --------------
echo 頭部と腕の頂点回避を行うか、yes か no を入力して下さい。
echo 何も入力せず、ENTERを押下した場合、頂点回避を行いません。
set AVOIDANCE=0
set IS_AVOIDANCE=no
set /P IS_AVOIDANCE="■頂点回避処理[yes/no]: "

IF /I "%IS_AVOIDANCE%" EQU "yes" (
    set AVOIDANCE=1
)

rem ---  詳細ログ有無

echo --------------
echo 詳細なログを出すか、yes か no を入力して下さい。
echo 何も入力せず、ENTERを押下した場合、通常ログを出力します。
set VERBOSE=2
set IS_DEBUG=no
set /P IS_DEBUG="■詳細ログ[yes/no]: "

IF /I "%IS_DEBUG%" EQU "yes" (
    set VERBOSE=3
)

rem ---  python 実行
python src/main.py --vmd_path %INPUT_VMD% --trace_pmx_path %MODEL_PMX% --replace_pmx_path %REPLACE_MODEL_PMX% --avoidance %AVOIDANCE% --verbose %VERBOSE%


