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
import random
from datetime import datetime

from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
from VmdWriter import VmdWriter, VmdMorphFrame
from VmdReader import VmdReader, VmdMotion
import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(pmx_path, min_value, max_value, iter_value, target_morphs):
    print("処理対象PMXファイル: %s" % pmx_path)
    print("モーフ最小値: %s" % min_value)
    print("モーフ最大値: %s" % max_value)
    print("モーフ増加量: %s" % iter_value)
    print("対象モーフ: %s" % ','.join([str(i) for i in target_morphs]))

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
        all_morph_names = []

        for mk, mv in model.morphs.items():
            if mv.display and mv.name in target_morphs:
                all_morphs.append(mv)
                all_morph_names.append(mk)

        # 変化量
        ratio_values = [iter_value*x for x in range(math.ceil(min_value/iter_value),math.ceil(max_value/iter_value)+1)]

        brend_cnt = 0
        brend_morph_by_frames = {}
        prev_sum = 0

        # モーフの組合せ数別に出力
        morph_cnt = len(all_morphs)

        # モーフの組合せ
        morph_comb = list(itertools.combinations(all_morphs, morph_cnt))

        # 変化量の直積（同じ値を許容する）
        ratio_product = list(itertools.product(ratio_values, repeat=morph_cnt))

        # モーフと変化量の組み合わせ
        brend_mr_pairs_list = list(itertools.product(morph_comb, ratio_product))
        logger.debug("mr_pairs_list: %s", brend_mr_pairs_list)

        brend_cnt += len(brend_mr_pairs_list)

        writer = VmdWriter()

        for (morph_list, ratio_list) in brend_mr_pairs_list:
            # ファイル用モーションデータ

            # モーフ名組合せタプル
            morph_names = tuple([x.name for x in morph_list])
            
            # モーフ登録フレーム設定
            mframe = len(brend_morph_by_frames)
            if mframe not in brend_morph_by_frames:
                brend_morph_by_frames[mframe] = []
            
            # 指定フレームにモーフ登録
            for (mv, ratio) in zip(morph_list, ratio_list):
                morph = VmdMorphFrame()
                morph.frame = mframe
                morph.format_name = mv.name
                # ～とかが出力できないので、回避策
                morph.name = mv.name.encode('cp932').decode('shift_jis').encode('shift_jis')
                morph.ratio = ratio
                morph.key = True
                
                brend_morph_by_frames[mframe].append(morph)

                sum_cnt = len(brend_morph_by_frames) * len(target_morphs)
                if sum_cnt // 10000 > prev_sum:
                    print("ブレンド: 総モーフ数: %s" % sum_cnt)
                    prev_sum = sum_cnt // 10000

        # target_morph_frames = [x for x in brend_morph_frames if x.key == True]
        # フレーム番号順にソート
        # sorted_brend_morph_by_frames = sorted(brend_morph_by_frames.items())
        # シャッフル
        sorted_brend_morph_by_frames = random.sample(brend_morph_by_frames.items(), len(brend_morph_by_frames))

        # 区切りはモーフ上限以内で
        step = int(19000 / len(target_morphs))
        for idx in range(0, len(sorted_brend_morph_by_frames), step):
            # モーフの組合せ分ずつに区切って出力する
            start = idx
            end = min(idx + step, len(sorted_brend_morph_by_frames))

            target_morph_frames = []
            for n in range(start, end):
                for mf in sorted_brend_morph_by_frames[n][1]:
                    mf.frame = n - start
                    target_morph_frames.append(mf)

            fpath = re.sub(r'\.pmx$', "_blend_{0:%Y%m%d_%H%M%S}_{1:08d}.vmd".format(datetime.now(), end), pmx_path)
            writer.write_vmd_file(fpath, model.name, [], target_morph_frames, [], [], [], [])
            print("モーフブレンドVMD出力成功(%s): %s" % (len(target_morph_frames), fpath))

        #         # # モーフと変化量の組み合わせの全リスト
        #         # mr_pairs_list = [p for p in itertools.product(*list(mv_rv_pair.values())) if len(set(p)) == len(p)]
        #         # logger.debug("p:%s, n:%s, l: %s, mc: %s", panel, cnt, len(mr_pairs_list), mr_pairs_list[0])


        # for amidx, am in enumerate(all_morphs):
        #     for cnt in range(len(all_morphs)*2):
        #         if cnt % 2 == 0:
        #             # 2で割れる場合、最小値
        #             ratio = min_value
        #         else:
        #             # 2で割れない場合、最大値
        #             ratio = max_value
                
        #         # フレーム番号(キーを打つタイミングをずらして登録する)
        #         frame = ( mframe_cnt * cnt ) + amidx
        #         logger.info("am: %s, f: %s, r: %s", am.name, frame, ratio)

        #         morph = VmdMorphFrame()
        #         morph.frame = frame
        #         # ～とかが出力できないので、回避策
        #         morph.name = am.name.encode('cp932').decode('shift_jis').encode('shift_jis')
        #         morph.ratio = ratio
        #         morph_frames.append(morph)          



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
    parser.add_argument('--min_value', dest='min_value', help='min_value', type=float)
    parser.add_argument('--max_value', dest='max_value', help='max_value', type=float)
    parser.add_argument('--iter_value', dest='iter_value', help='iter_value', type=float)
    parser.add_argument('--target_morphs', dest='target_morphs', help='target_morphs', type=str)
    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.pmx_path, "PMXファイル", ".pmx", True) == False:
        sys.exit(-1)

    main(args.pmx_path, args.min_value, args.max_value, args.iter_value, args.target_morphs.split(","))