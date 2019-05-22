#! env python
# -*- coding: utf-8 -*-

import os.path
import traceback

import main

def is_valid_inputall(vmd_path, org_bone_path, rep_bone_path, rep_vertex_path):

    # 調整対象vmdファイル
    if is_valid_file(vmd_path, "調整対象vmdファイル") == False:
        return False

    # トレース元モデルボーン構造CSVファイル
    if is_valid_file(org_bone_path, "トレース元モデルボーン構造CSVファイル") == False:
        return False

    # トレース変換先モデルボーン構造CSVファイル
    if is_valid_file(rep_bone_path, "トレース変換先モデルボーン構造CSVファイル") == False:
        return False

    # # トレース変換先モデル頂点構造CSVファイルは必須ではないためチェックしない
    # result, msg = is_valid_file(rep_vertex_path, "トレース変換先モデル頂点構造CSVファイル")
    # if result == False:
    #     return False

    return True

def is_valid_file(file_path, file_type):

    if not os.path.exists(file_path):
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　"+ file_type +"ファイルが見つかりませんでした。")
        print("■　入力パス: "+ file_path )
        print("■■■■■■■■■■■■■■■■■")

        return False
    
    return True

def exec(vmd_path, org_bone_path, rep_bone_path, rep_vertex_path):
    print("■■■■■■■■■■■■■■■■■")
    print("■　VMDサイジング処理実行")
    print("■■■■■■■■■■■■■■■■■")


    try:
        main.main(vmd_path, org_bone_path, rep_bone_path, rep_vertex_path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())
