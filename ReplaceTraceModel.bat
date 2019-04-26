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


rem ---  トレース元モデルボーン構造CSVファイル
echo --------------
set MODEL_BONE_CSV=born\あにまさ式ミク準標準.csv
echo トレース元モデルのボーン構造CSVファイルの相対パスを入力して下さい。
echo 何も入力せず、ENTERを押下した場合、「%MODEL_BONE_CSV%」のファイルを読み込みます。
set /P MODEL_BONE_CSV="■トレース元モデルボーン構造CSVファイル: "

rem ---  トレース変換先モデルボーン構造CSVファイル
echo --------------
set REPLACE_MODEL_BONE_CSV=born\あにまさ式ミク準標準.csv
echo トレース変換先モデルのボーン構造CSVファイルの相対パスを入力して下さい。
echo 何も入力せず、ENTERを押下した場合、「%REPLACE_MODEL_BONE_CSV%」のファイルを読み込みます。
set /P REPLACE_MODEL_BONE_CSV="■トレース変換先モデルボーン構造CSVファイル: "


rem rem ---  トレース変換先モデル頂点構造CSVファイル
rem echo --------------
set REPLACE_MODEL_VERTEX_CSV=%REPLACE_MODEL_BONE_CSV:born=vertex%
rem echo トレース変換先モデルの頂点構造CSVファイルの相対パスを入力して下さい。
rem echo 何も入力せず、ENTERを押下した場合、「%REPLACE_MODEL_VERTEX_CSV%」のファイルを読み込みます。
rem set /P REPLACE_MODEL_VERTEX_CSV="■トレース変換先モデル頂点構造CSVファイル: "


rem ---  詳細ログ有無

echo --------------
echo 詳細なログを出すか、yes か no を入力して下さい。
echo 何も入力せず、ENTERを押下した場合、通常ログを出力します。
set VERBOSE=2
set IS_DEBUG=yes
set /P IS_DEBUG="■詳細ログ[yes/no]: "

IF /I "%IS_DEBUG%" EQU "yes" (
    set VERBOSE=3
)

rem ---  python 実行
python src/main.py --vmd_path %INPUT_VMD% --trace_bone_path %MODEL_BONE_CSV% --replace_bone_path %REPLACE_MODEL_BONE_CSV% --replace_vertex_path %REPLACE_MODEL_VERTEX_CSV% --verbose %VERBOSE%


