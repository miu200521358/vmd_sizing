#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys
import itertools
import math

from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
from VmdWriter import VmdWriter, VmdMorphFrame
from VmdReader import VmdReader, VmdMotion
import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(pmx_path, min_value, max_value, iter_value):
    print("処理対象PMXファイル: %s" % pmx_path)
    print("モーフ最小値: %s" % min_value)
    print("モーフ最大値: %s" % max_value)
    print("モーフ増加量: %s" % iter_value)
    # print("パネル: %s" % panel_name)

    # panel = 1
    # if panel_name == "眉":
    #     panel = 1
    # elif panel_name == "目":
    #     panel = 2
    # elif panel_name == "口":
    #     panel = 3
    # elif panel_name == "他":
    #     panel = 4

    try:
        # PMX読み込み
        model = PmxReader().read_pmx_file(pmx_path)
        logger.info("model: %s", model.name)

        logger.info("min: %s, %s", min_value, min_value/iter_value)
        logger.info("max: %s, %s", max_value, max_value/iter_value)

        # キーを打つタイミング
        mframe_cnt = math.ceil(max_value/iter_value - min_value/iter_value)
        logger.info("mframe_cnt: %s", mframe_cnt)

        all_morphs = []

        for mk, mv in model.morphs.items():
            if mv.display:
                print("〇モーフ表示 mk: %s, panel: %s" % (mk, mv.get_panel_name()))
                all_morphs.append(mv)
            else:
                logger.debug("－モーフ非表示 mk: %s, mv: %s", mk, mv)

        # ファイル用モーションデータ
        morph_frames = {}

        for amidx, am in enumerate(all_morphs):
            for cnt in range(len(all_morphs)*2):
                if cnt % 2 == 0:
                    # 2で割れる場合、最小値
                    ratio = min_value
                else:
                    # 2で割れない場合、最大値
                    ratio = max_value
                
                # フレーム番号(キーを打つタイミングをずらして登録する)
                frame = ( mframe_cnt * cnt ) + amidx
                logger.info("am: %s, f: %s, r: %s", am.name, frame, ratio)

                morph = VmdMorphFrame()
                morph.frame = frame
                # ～とかが出力できないので、回避策
                morph.name = am.name.encode('cp932').decode('shift_jis').encode('shift_jis')
                morph.ratio = ratio

                if frame not in morph_frames:
                    morph_frames[frame] = []

                morph_frames[frame].append(morph)          

        fpath = re.sub(r".pmx$", "_モーフブレンド.vmd", pmx_path)
        VmdWriter().write_vmd_file(fpath, model.name, [], morph_frames, [], [], [], [])
        print("モーフブレンドVMD出力成功: %s" % fpath)



        # ratio_values = [iter_value*x for x in range(math.ceil(min_value/iter_value),math.ceil(max_value/iter_value)+1)]
        
        # logger.info("ratio_values: %s", ratio_values)
        
        # all_morphs = []
        
        # for mk, mv in model.morphs.items():
        #     if mv.display and mv.panel == panel:
        #         logger.info("〇モーフ表示 mk: %s, panel: %s", mk, mv.panel)
        #         all_morphs.append(mk)
        #     else:
        #         logger.debug("－モーフ非表示 mk: %s, mv: %s", mk, mv)

        # # VMD出力先
        # writer = VmdWriter()
        # # モーションファイル生成
        # morph_frames = []
        # # 登録モーフ数
        # morph_cnt = 0
        # # ファイルINDEX
        # fidx = 1
        # # フレーム数
        # frame = 0

        # # パネル別モーフの全組み合わせ
        # for cnt in range(1, len(all_morphs)+1):
        #     for morph_comb in list(itertools.combinations(all_morphs, cnt)):                
        #         # モーフと変化量の組み合わせ（キー：モーフ名、値：モーフと変化量のタプルリスト）          
        #         mv_rv_pair = {}
        #         for mc in list(morph_comb):
        #             mv_rv_pair[mc] = []
        #             for rv in ratio_values:
        #                 mv_rv_pair[mc].append((mc, rv))

        #         # モーフと変化量の組み合わせの全リスト
        #         mr_pairs_list = [p for p in itertools.product(*list(mv_rv_pair.values())) if len(set(p)) == len(p)]
        #         logger.debug("p:%s, n:%s, l: %s, mc: %s", panel, cnt, len(mr_pairs_list), mr_pairs_list[0])

        #         for mr_pairs in mr_pairs_list:
        #             # logger.info("mr_pairs: %s", mr_pairs)
        #             if morph_cnt + len(mr_pairs) > 20000:
        #                 # 2万を超えるモーフは登録不可
        #                 fpath = re.sub(r".pmx$", "_morph{0:010}.vmd".format(fidx), pmx_path)
        #                 writer.write_vmd_file(fpath, model.name, [], morph_frames, [], [], [], [])
        #                 print("モーフブレンドVMD出力成功: %s" % fpath)

        #                 # 新しいモーションファイル準備
        #                 morph_frames = []
        #                 morph_cnt = 0
        #                 frame = 0
        #                 fidx += 1

        #             for mr_pair in mr_pairs:
        #                 morph_cnt += 1

        #                 morph = VmdMorphFrame()
        #                 morph.frame = frame
        #                 morph.name = mr_pair[0].encode('shift-jis')
        #                 morph.ratio = mr_pair[1]

        #                 morph_frames.append(morph)
                    
        #             frame += 1

        # fpath = re.sub(r".pmx$", "_morph{0:010}.vmd".format(fidx), pmx_path)
        # writer.write_vmd_file(fpath, model.name, [], morph_frames, [], [], [], [])
        # print("モーフブレンドVMD出力成功: %s" % fpath)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　モーフブレンド処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--pmx_path', dest='pmx_path', help='input pmx', type=str)
    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.pmx_path, "PMXファイル", ".pmx", True) == False:
        sys.exit(-1)

    main(args.pmx_path, -0.1, 1.2, 0.1)