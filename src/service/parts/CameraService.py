# -*- coding: utf-8 -*-
#
import numpy as np
import math

from mmd.PmxData import PmxModel, Bone # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException

logger = MLogger(__name__, level=1)

# 顔系ボーン名
HEAD_BONE_NAMES = ["頭頂実体", "頭", "首", "左目", "右目", "首根元"]
# 体幹ボーン名
TRUNK_BONE_NAMES = ["上半身2", "上半身"]
# 足底ボーン名
LEG_BOTTOM_BONE_NAMES = ["右足底実体", "左足底実体"]


class CameraService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        logger.info("カメラ補正　", decoration=MLogger.DECORATION_LINE)

        try:
            # 腕処理対象データセットを取得
            self.target_data_set_idxs = self.get_target_set_idxs()
            logger.test("target_data_set_idxs: %s", self.target_data_set_idxs)

            if len(self.target_data_set_idxs) == 0:
                # データセットがない場合、処理スキップ
                logger.warning("カメラ補正ができるファイルセットが見つからなかったため、カメラ補正をスキップします。", decoration=MLogger.DECORATION_BOX)
                return True

            self.camera_options = {}

            for data_set_idx in self.target_data_set_idxs:
                self.prepare(data_set_idx)
            
            prev_fno = -1
            for fno in sorted(self.options.camera_motion.cameras.keys()):
                past_cf = VmdCameraFrame()
                cf = self.options.camera_motion.cameras[fno]
                # 1キーフレごとに見ていく（同一キーフレの可能性があるので、並列化不可）
                if prev_fno >= 0:
                    # 前回と同じカメラ位置の場合、前回のサイジング済みカメラ位置コピー
                    past_cf = self.options.camera_motion.cameras[prev_fno]
                    if past_cf.org_length == cf.length and past_cf.org_position == cf.position and past_cf.euler == cf.euler:
                        logger.info("%sフレーム目 前位置・距離コピー", fno)
                        cf.position = past_cf.position.copy()
                        cf.length = past_cf.length
                        continue

                # 比率計算
                org_inner_global_poses, org_inner_square_poses, rep_inner_global_poses, ratio, (nearest_data_set_idx, nearest_bone_name), \
                    (left_data_set_idx, left_bone_name), (right_data_set_idx, right_bone_name), (top_data_set_idx, top_bone_name), (bottom_data_set_idx, bottom_bone_name) \
                    = self.calc_camera_ratio(fno, cf)
                
                # カメラサイジング実行
                self.execute_rep_camera(fno, cf, past_cf, org_inner_global_poses, org_inner_square_poses, rep_inner_global_poses, ratio, nearest_data_set_idx, nearest_bone_name, \
                                        left_data_set_idx, left_bone_name, right_data_set_idx, right_bone_name, top_data_set_idx, top_bone_name, bottom_data_set_idx, bottom_bone_name, \
                                        self.options.camera_length)

                prev_fno = fno

            if self.options.now_process_ctrl:
                self.options.now_process += 1
                self.options.now_process_ctrl.write(str(self.options.now_process))

                self.options.tree_process_dict["カメラ補正"] = True
            
            return True
        except MKilledException as ke:
            raise ke
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc())
            raise e
    
    # 変換先モデル用カメラ作成
    def execute_rep_camera(self, fno: int, cf: VmdCameraFrame, past_cf: VmdCameraFrame, org_inner_global_poses: dict, org_inner_square_poses: dict, rep_inner_global_poses: dict, \
                           ratio: float, nearest_data_set_idx: int, nearest_bone_name: str, left_data_set_idx: int, left_bone_name: str, right_data_set_idx: int, right_bone_name: str, \
                           top_data_set_idx: int, top_bone_name: str, bottom_data_set_idx: int, bottom_bone_name: str, camera_length: float):

        # ------------------------

        # 画面内に映ってるボーンINDEXの中央値を仮の中央座標とする
        # 複数人モーションのカメラの場合を想定して、上下端は見ない
        org_target_vec = MVector3D(np.mean(np.array(list(org_inner_global_poses.values())), axis=0))
        rep_target_vec = MVector3D(np.mean(np.array(list(rep_inner_global_poses.values())), axis=0))

        # カメラ角度
        camera_qq = self.calc_camera_qq(cf)

        # カメラの原点（グローバル座標）
        mat_origin = MMatrix4x4()
        mat_origin.setToIdentity()
        mat_origin.translate(cf.position)
        mat_origin.rotate(camera_qq)
        mat_origin.translate(MVector3D(0, 0, cf.length))
        # 距離を加味したカメラの原点（距離0でこの位置に合わせると注視点が合う）
        camera_origin = mat_origin * MVector3D()
        logger.test("camera_origin: %s", camera_origin)

        # ボーンの相対位置
        org_nearest_relative_vec = (camera_origin - org_target_vec)
        logger.debug("org_target_vec: %s", org_target_vec.to_log())
        logger.debug("org_nearest_relative_vec: %s", org_nearest_relative_vec.to_log())

        # 距離0の場合のカメラの位置を算出
        cf_pos = rep_target_vec + (org_nearest_relative_vec * ratio)
        logger.debug("cf_pos: %s", cf_pos)

        length_ratio = ratio
        pos_ratio = ratio

        if camera_length < 5:
            # カメラの距離を再設定
            # 可動範囲内に収める（2020/10/22）
            length_ratio = min(camera_length, max(1 / camera_length, ratio))
            # 原点用比率は、距離が可動範囲内ならば比率そのまま、範囲外ならば体格比率まで
            pos_ratio = ratio if length_ratio == ratio else \
                min(self.camera_options[nearest_data_set_idx].body_ratio, max(1 / self.camera_options[nearest_data_set_idx].body_ratio, ratio))

        mat_len = MMatrix4x4()
        mat_len.setToIdentity()
        mat_len.translate(cf_pos)
        mat_len.rotate(camera_qq)
        mat_len.translate(MVector3D(0, 0, -cf.length * pos_ratio))
        # 距離を除いたカメラの原点に合わせる
        camera_length_origin = mat_len * MVector3D()
        logger.test("camera_length_origin: %s", camera_length_origin)

        # 距離を除いたカメラの原点を再設定
        cf.position = camera_length_origin

        cf.length = cf.length * length_ratio

        # 比率を保持
        cf.ratio = length_ratio

        offset_length = 0
        offset_angle = 0
    
        # ------------------------
        rep_inner_square_poses = {}

        # この時点の距離と位置で変換先モデルの体幹＋目の映り具合をチェック（上下が分かってないと大きさ取れない）
        # 距離制限が掛かっている場合、スルー
        if top_data_set_idx >= 0 and top_bone_name and bottom_data_set_idx >= 0 and bottom_bone_name and camera_length == 5:
            # 先モデル上下グローバル位置
            rep_top_pos = rep_inner_global_poses[(top_data_set_idx, top_bone_name)]
            rep_bottom_pos = rep_inner_global_poses[(bottom_data_set_idx, bottom_bone_name)]

            # 先モデル上下プロジェクション正規位置
            rep_inner_square_poses[(top_data_set_idx, top_bone_name)] = self.calc_project_square_vec(cf, MVector3D(rep_top_pos)).data()
            rep_inner_square_poses[(bottom_data_set_idx, bottom_bone_name)] = self.calc_project_square_vec(cf, MVector3D(rep_bottom_pos)).data()

            # 上下のY差
            org_diff = org_inner_square_poses[(bottom_data_set_idx, bottom_bone_name)][1] - org_inner_square_poses[(top_data_set_idx, top_bone_name)][1]
            rep_diff = rep_inner_square_poses[(bottom_data_set_idx, bottom_bone_name)][1] - rep_inner_square_poses[(top_data_set_idx, top_bone_name)][1]

            # 上下に取ったセットの全長比率をベースに距離を調整する
            length_unit = (((self.camera_options[top_data_set_idx].body_ratio + self.camera_options[bottom_data_set_idx].body_ratio) / 2) / 5) * np.sign(cf.length)

            cnt = 0
            while cnt < 20 and rep_diff - 0.1 >= org_diff:
                # 上下のY差を揃える

                # 距離を遠ざける
                cf.length += length_unit
                offset_length += length_unit

                if cnt % 9 == 0:
                    # 一定回数時には視野角も遠ざける
                    cf.angle += 1
                    offset_angle += 1

                # 先モデル上下プロジェクション正規位置
                rep_inner_square_poses[(top_data_set_idx, top_bone_name)] = self.calc_project_square_vec(cf, MVector3D(rep_top_pos)).data()
                rep_inner_square_poses[(bottom_data_set_idx, bottom_bone_name)] = self.calc_project_square_vec(cf, MVector3D(rep_bottom_pos)).data()

                # 上下のY差
                rep_diff = rep_inner_square_poses[(bottom_data_set_idx, bottom_bone_name)][1] - rep_inner_square_poses[(top_data_set_idx, top_bone_name)][1]

                cnt += 1

        logger.info("%sフレーム目 原点比率: %s, 距離比率: %s, 注視点: %s-%s, 上辺: %s-%s, 下辺: %s-%s, 距離オフセット: %s, 視野角オフセット: %s", \
                    cf.fno, round(pos_ratio, 5), round(length_ratio, 5), (nearest_data_set_idx + 1), nearest_bone_name.replace("実体", ""), \
                    (top_data_set_idx + 1), top_bone_name.replace("実体", ""), (bottom_data_set_idx + 1), bottom_bone_name.replace("実体", ""), \
                    round(offset_length, 5), offset_angle)
    
    # カメラ倍率計算
    def calc_camera_ratio(self, fno: int, cf: VmdCameraFrame):
        # 各データのグローバル位置算出
        all_org_global_poses = {}
        # 各データのプロジェクション座標位置
        all_org_project_square_poses = {}

        # 最も注視点に近いINDEX
        nearest_data_set_idx = -1
        nearest_bone_name = None
        ratio = 0

        # まず全体のグローバル位置とプロジェクション座標正規位置を算出
        self.calc_org_project_square_poses(fno, cf, 0, -1, all_org_global_poses, all_org_project_square_poses)
        # 画面内に映っているINDEXリスト
        org_inner_global_poses, org_inner_square_poses = self.calc_inner_index(fno, all_org_global_poses, all_org_project_square_poses, None, 0, 0.1)
        logger.debug("f: %s, inner: %s", fno, org_inner_global_poses.keys())

        # 画面内に映っている顔系INDEX(注視点直近算出のためなので、ちょっと範囲広め)
        org_face_inner_global_poses, org_face_inner_square_poses = self.calc_inner_index(fno, org_inner_global_poses, org_inner_square_poses, HEAD_BONE_NAMES, 0, 0.1)
        # 画面内に映っている体幹系INDEX
        org_trunk_inner_global_poses, org_trunk_inner_square_poses = self.calc_inner_index(fno, org_inner_global_poses, org_inner_square_poses, \
                                                                                           TRUNK_BONE_NAMES + LEG_BOTTOM_BONE_NAMES, 0, 0.1)

        if len(org_face_inner_square_poses.keys()) > 0:
            # 顔系が画面内に映っている場合、その時点で注視点直近を取得する
            face_near_indexes = self.calc_nearest_index(fno, cf, org_face_inner_square_poses)
            (nearest_data_set_idx, nearest_bone_name) = face_near_indexes[0]
        else:
            if len(org_trunk_inner_square_poses.keys()) > 0:
                # 体幹系が画面内に映っている場合、その時点で注視点直近を取得する
                trunk_near_indexes = self.calc_nearest_index(fno, cf, org_trunk_inner_square_poses)
                (nearest_data_set_idx, nearest_bone_name) = trunk_near_indexes[0]
            else:
                # 体幹が画面に映ってない場合、末端チェック

                # 体幹で最も注視点に近いINDEXを取得する（画面内とは限らない）
                all_near_indexes = self.calc_nearest_index(fno, cf, all_org_project_square_poses)

                # 末端込みでは映ってない場合も考慮して直近のを直接採用
                (nearest_data_set_idx, nearest_bone_name) = all_near_indexes[0]

                # innerに追加
                org_inner_global_poses[(nearest_data_set_idx, nearest_bone_name)] = all_org_global_poses[(nearest_data_set_idx, nearest_bone_name)]
                org_inner_square_poses[(nearest_data_set_idx, nearest_bone_name)] = all_org_project_square_poses[(nearest_data_set_idx, nearest_bone_name)]

        # 変換先モデルの画面内ボーンのグローバル位置
        rep_inner_global_poses = self.calc_rep_global_poses(fno, list(org_inner_global_poses.keys()))
        
        logger.debug("f: %s, nearest d: %s, k: %s, v: %s, s: %s", fno, nearest_data_set_idx, nearest_bone_name, \
                     all_org_global_poses[(nearest_data_set_idx, nearest_bone_name)], all_org_project_square_poses[(nearest_data_set_idx, nearest_bone_name)])

        # 画面端ボーンを計算する
        (top_data_set_idx, top_bone_name), (bottom_data_set_idx, bottom_bone_name) = self.calc_top_botom_index(fno, cf, org_inner_square_poses, org_inner_global_poses, 0, 0.1)
        (left_data_set_idx, left_bone_name), (right_data_set_idx, right_bone_name) = self.calc_left_right_index(fno, cf, org_inner_square_poses, org_inner_global_poses, 0, 0.1)
        
        org_top_diff = rep_top_diff = org_bottom_diff = rep_bottom_diff = 0

        if left_data_set_idx >= 0 and left_bone_name:
            logger.debug("f: %s, left d: %s, k: %s, v: %s, s: %s", fno, left_data_set_idx, left_bone_name, \
                         org_inner_global_poses[(left_data_set_idx, left_bone_name)], all_org_project_square_poses[(left_data_set_idx, left_bone_name)])
        
        if right_data_set_idx >= 0 and right_bone_name:
            logger.debug("f: %s, right d: %s, k: %s, v: %s, s: %s", fno, right_data_set_idx, right_bone_name, \
                         org_inner_global_poses[(right_data_set_idx, right_bone_name)], all_org_project_square_poses[(right_data_set_idx, right_bone_name)])

        if top_data_set_idx >= 0 and top_bone_name:
            logger.debug("f: %s, top d: %s, k: %s, v: %s, s: %s", fno, top_data_set_idx, top_bone_name, \
                         org_inner_global_poses[(top_data_set_idx, top_bone_name)], all_org_project_square_poses[(top_data_set_idx, top_bone_name)])

            org_top_diff = MVector3D(org_inner_global_poses[(top_data_set_idx, top_bone_name)]).distanceToPoint(MVector3D(org_inner_global_poses[(nearest_data_set_idx, nearest_bone_name)]))
            rep_top_diff = MVector3D(rep_inner_global_poses[(top_data_set_idx, top_bone_name)]).distanceToPoint(MVector3D(rep_inner_global_poses[(nearest_data_set_idx, nearest_bone_name)]))

        if bottom_data_set_idx >= 0 and bottom_bone_name:
            logger.debug("f: %s, bottom d: %s, k: %s, v: %s, s: %s", fno, bottom_data_set_idx, bottom_bone_name, \
                         org_inner_global_poses[(bottom_data_set_idx, bottom_bone_name)], all_org_project_square_poses[(bottom_data_set_idx, bottom_bone_name)])

            org_bottom_diff = MVector3D(org_inner_global_poses[(bottom_data_set_idx, bottom_bone_name)]).distanceToPoint(MVector3D(org_inner_global_poses[(nearest_data_set_idx, nearest_bone_name)]))
            rep_bottom_diff = MVector3D(rep_inner_global_poses[(bottom_data_set_idx, bottom_bone_name)]).distanceToPoint(MVector3D(rep_inner_global_poses[(nearest_data_set_idx, nearest_bone_name)]))
        
        if len(org_face_inner_square_poses.keys()) > 0 and len(org_trunk_inner_global_poses.keys()) == 0:
            # 顔のみが画面内に映っている場合、その時点で比率は顔固定
            ratio = self.camera_options[nearest_data_set_idx].head_ratio
        else:
            if 0 < org_top_diff and 0 < org_bottom_diff:
                # 画面上端も下端も見つかっている場合、全体の比率に合わせる
                ratio = (rep_top_diff + rep_bottom_diff) / (org_top_diff + org_bottom_diff)
            else:
                if 0 < org_top_diff:
                    # 画面上端が計算できている場合、上端の比率に合わせる
                    ratio = rep_top_diff / org_top_diff
                elif 0 < org_bottom_diff:
                    # 画面下端が計算ている場合、下端の比率に合わせる
                    ratio = rep_bottom_diff / org_bottom_diff
                else:
                    # 画面上端も下端もない場合、注視点のみが見つかっているので、身体の比率に合わせる
                    ratio = self.camera_options[nearest_data_set_idx].body_ratio

        logger.debug("f: %s, ratio: %s, nearest d: %s, k: %s, v: %s, s: %s", fno, ratio, nearest_data_set_idx, nearest_bone_name, \
                     all_org_global_poses[(nearest_data_set_idx, nearest_bone_name)], all_org_project_square_poses[(nearest_data_set_idx, nearest_bone_name)])

        return org_inner_global_poses, org_inner_square_poses, rep_inner_global_poses, ratio, (nearest_data_set_idx, nearest_bone_name), \
            (left_data_set_idx, left_bone_name), (right_data_set_idx, right_bone_name), (top_data_set_idx, top_bone_name), (bottom_data_set_idx, bottom_bone_name)
    
    # 指定されたボーンのうち、大体画面内に映っているINDEXを返す
    def calc_inner_index(self, fno: int, all_global_poses: dict, all_square_poses: dict, bone_name_list: list, x_offset: float, y_offset: float):
        inner_square_poses = {}
        inner_global_poses = {}

        if not bone_name_list:
            # ボーンリストが未指定である場合、全値から調べる
            square_poses = np.array(list(all_square_poses.values()))

            if len(square_poses) > 0:
                # 画面内に映っている対象となるINDEX
                refrected_indexes = np.where(((0 - x_offset) <= square_poses[:, 0]) & (square_poses[:, 0] <= (1 + x_offset)) \
                                             & ((0 - y_offset) <= square_poses[:, 1]) & (square_poses[:, 1] <= (1 + y_offset)) \
                                             & (0 < square_poses[:, 2]) & (square_poses[:, 2] < 1))
                
                all_square_key_list = list(all_square_poses.keys())
                for ri in refrected_indexes[0]:
                    inner_square_poses[all_square_key_list[ri]] = square_poses[ri]
                    inner_global_poses[all_square_key_list[ri]] = all_global_poses[all_square_key_list[ri]]
        else:
            # 指定されている場合、そのボーン名のみ調べる
            for (data_set_idx, bone_name), square_pos in all_square_poses.items():
                if bone_name in bone_name_list and (0 - x_offset) <= square_pos[0] <= (1 + x_offset) and (0 - y_offset) <= square_pos[1] <= (1 + y_offset) and 0 < square_pos[2] < 1:
                    # 大体画面内に映っていたら、INDEX保持
                    inner_square_poses[(data_set_idx, bone_name)] = square_pos
                    inner_global_poses[(data_set_idx, bone_name)] = all_global_poses[(data_set_idx, bone_name)]

        logger.debug("f: %s, inner_square_poses: %s", fno, inner_square_poses)

        return inner_global_poses, inner_square_poses

    # 画面端に最も近いINDEXを返す
    def calc_top_botom_index(self, fno: int, cf: VmdCameraFrame, all_square_poses: dict, org_inner_global_poses: dict, x_offset: float, y_offset: float):
        square_keys = list(all_square_poses.keys())
        square_poses = np.array(list(all_square_poses.values()))

        if len(square_poses) == 0:
            # 処理対象ボーンがない場合、-1
            return (-1, ""), (-1, "")

        # 画面内に映っている対象となるINDEX
        refrected_indexes = np.where(((0 - x_offset) <= square_poses[:, 0]) & (square_poses[:, 0] <= (1 + x_offset)) \
                                     & ((0 - y_offset) <= square_poses[:, 1]) & (square_poses[:, 1] <= (1 + y_offset)) \
                                     & (0 < square_poses[:, 2]) & (square_poses[:, 2] < 1))
        
        if len(refrected_indexes[0]) == 0:
            # 画面内に映っているボーンがない場合、-1
            return (-1, ""), (-1, "")
        
        y_indexes = np.argsort(square_poses[refrected_indexes][:, 1])
        logger.debug("f: %s, y_indexes: %s", fno, y_indexes)

        # 画面上端(Y最小)
        top_edge_index = refrected_indexes[0][y_indexes[0]]
        top_edge_pos = square_poses[top_edge_index]
        top_edge_key = square_keys[top_edge_index]
        top_edge_global_pos = org_inner_global_poses[top_edge_key]

        # 画面下端(Y最大)
        bottom_edge_index = refrected_indexes[0][y_indexes[-1]]
        bottom_edge_pos = square_poses[bottom_edge_index]
        bottom_edge_key = square_keys[bottom_edge_index]
        bottom_edge_global_pos = org_inner_global_poses[bottom_edge_key]

        # 上下のグローバル距離
        global_distance = MVector3D(top_edge_global_pos).distanceToPoint(MVector3D(bottom_edge_global_pos)) / 10

        for yi in y_indexes:
            if square_poses[yi][1] > square_poses[refrected_indexes[0][y_indexes[0]]][1] + 0.1:
                # 上端から画面0.2の距離までなめたら終了
                logger.debug("f: %s, 画面上端 break: yi: %s, top: %s", fno, yi, square_poses[refrected_indexes[0][y_indexes[0]]][1])
                break

            logger.debug("f: %s, 画面 check: square_poses[yi][1]: %s, square_poses[yi][2]: %s, top_edge_pos[1]: %s, top_edge_pos[2]: %s", \
                         fno, square_poses[yi][1], square_poses[yi][2], top_edge_pos[1], top_edge_pos[2])

            top_target_key = (int(square_keys[yi][0]), str(square_keys[yi][1]))
            top_target_global_pos = org_inner_global_poses[top_target_key]

            if top_target_global_pos[2] + global_distance < top_edge_global_pos[2]:
                # より前にある場合、そちらを採用
                top_edge_pos = square_poses[yi]
                top_edge_index = yi

        for yi in reversed(y_indexes):
            if square_poses[yi][1] < square_poses[refrected_indexes[0][y_indexes[-1]]][1] - 0.2:
                # 下端から画面0.2の距離までなめたら終了
                logger.debug("f: %s, 画面下端 break: yi: %s, top: %s", fno, yi, square_poses[refrected_indexes[0][y_indexes[-1]]][1])
                break

            logger.debug("f: %s, 画面 check: square_poses[yi][1]: %s, square_poses[yi][2]: %s, top_edge_pos[1]: %s, top_edge_pos[2]: %s", \
                         fno, square_poses[yi][1], square_poses[yi][2], bottom_edge_pos[1], bottom_edge_pos[2])

            bottom_target_key = (int(square_keys[yi][0]), str(square_keys[yi][1]))
            bottom_target_global_pos = org_inner_global_poses[bottom_target_key]

            if bottom_target_global_pos[2] + global_distance < bottom_edge_global_pos[2]:
                # より前にある場合、そちらを採用
                bottom_edge_pos = square_poses[yi]
                bottom_edge_index = yi

        return list(all_square_poses.keys())[top_edge_index], list(all_square_poses.keys())[bottom_edge_index]

    def calc_left_right_index(self, fno: int, cf: VmdCameraFrame, all_square_poses: dict, org_inner_global_poses: dict, x_offset: float, y_offset: float):
        square_keys = list(all_square_poses.keys())
        square_poses = np.array(list(all_square_poses.values()))

        if len(square_poses) == 0:
            # 処理対象ボーンがない場合、-1
            return (-1, None), (-1, None)

        # 画面内に映っている対象となるINDEX
        refrected_indexes = np.where(((0 - x_offset) <= square_poses[:, 0]) & (square_poses[:, 0] <= (1 + x_offset)) \
                                     & ((0 - y_offset) <= square_poses[:, 1]) & (square_poses[:, 1] <= (1 + y_offset)) \
                                     & (0 < square_poses[:, 2]) & (square_poses[:, 2] < 1))
        
        if len(refrected_indexes[0]) == 0:
            # 画面内に映っているボーンがない場合、-1
            return (-1, None), (-1, None)
        
        x_indexes = np.argsort(square_poses[refrected_indexes][:, 0])
        
        # 画面左端(X最小)
        left_edge_index = refrected_indexes[0][x_indexes[0]]
        left_edge_pos = square_poses[left_edge_index]
        left_edge_key = square_keys[left_edge_index]
        left_edge_global_pos = org_inner_global_poses[left_edge_key]

        # 画面右端(X最大)
        right_edge_index = refrected_indexes[0][x_indexes[-1]]
        right_edge_pos = square_poses[right_edge_index]
        right_edge_key = square_keys[right_edge_index]
        right_edge_global_pos = org_inner_global_poses[right_edge_key]

        # 左右のグローバル距離
        global_distance = MVector3D(left_edge_global_pos).distanceToPoint(MVector3D(right_edge_global_pos)) / 10

        for xi in x_indexes:
            if square_poses[xi][0] > square_poses[refrected_indexes[0][x_indexes[0]]][0] + 0.1:
                # 左端から画面1/10の距離までなめたら終了
                break

            if square_poses[xi][2] + global_distance < left_edge_pos[2]:
                # より前にある場合、そちらを採用
                left_edge_pos = square_poses[xi]
                left_edge_index = xi

        for xi in reversed(x_indexes):
            if square_poses[xi][0] < square_poses[refrected_indexes[0][x_indexes[-1]]][0] - 0.1:
                # 右端から画面1/10の距離までなめたら終了
                break

            if square_poses[xi][2] + global_distance < right_edge_pos[2]:
                # より前にある場合、そちらを採用
                right_edge_pos = square_poses[xi]
                right_edge_index = xi
        
        return list(all_square_poses.keys())[left_edge_index], list(all_square_poses.keys())[right_edge_index]

    # 注視点に最も近いINDEXを返す
    def calc_nearest_index(self, fno: int, cf: VmdCameraFrame, all_square_poses: dict):
        center_poses = np.array([0.5, 0.5, 1])
        square_poses = np.array(list(all_square_poses.values()))

        # 中央からの距離
        project_diff_lengths = np.sqrt(np.sum((center_poses - square_poses)**2, axis=1))
        # 中央からの距離が近い順に上位を抽出する
        project_near_indexes = np.argsort(project_diff_lengths)

        logger.test("f: %s", fno)
        logger.test(project_diff_lengths)
        logger.test(project_near_indexes)

        nearest_indexes = []
        for near_index in project_near_indexes[:10]:
            # 直近10件のみINDEXを抽出する
            nearest_indexes.append(list(all_square_poses.keys())[near_index])

        return nearest_indexes

    def calc_org_project_square_poses(self, fno: int, cf: VmdCameraFrame, start_idx: int, end_idx: int, all_org_global_poses: dict, all_org_project_square_poses: dict):
        for data_set_idx, camera_option in self.camera_options.items():
            for link_idx, org_link in enumerate(camera_option.org_links[start_idx:end_idx]):
                if len(org_link.all().keys()) == 0:
                    # 処理対象がなければスルー
                    continue

                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]

                # 元モデルのそれぞれのグローバル位置
                org_global_3ds = MServiceUtils.calc_global_pos(data_set.camera_org_model, org_link, data_set.org_motion, fno)
                for bone_name, org_vec in org_global_3ds.items():
                    if bone_name in camera_option.org_link_target.keys() and (data_set_idx, bone_name) not in all_org_project_square_poses:
                        # 処理対象ボーンである場合、データを保持
                        all_org_global_poses[(data_set_idx, bone_name)] = org_vec.data()
                        all_org_project_square_poses[(data_set_idx, bone_name)] = self.calc_project_square_vec(cf, org_vec).data()

        [logger.test("f: %s, k: %s, v: %s, s: %s", fno, k, v, sv) for (k, v), (sk, sv) in zip(all_org_global_poses.items(), all_org_project_square_poses.items())]

    def calc_rep_global_poses(self, fno: int, data_bone_name_list: list):
        rep_links = []
        for (data_set_idx, bone_name) in data_bone_name_list:
            # 処理対象カメラオプション
            camera_option = self.camera_options[data_set_idx]
            # 処理対象のボーンを計算するためのリンク
            rep_link = camera_option.rep_links[bone_name]
            if (data_set_idx, rep_link) not in rep_links:
                # まだ保持されていないリンクなら保持
                rep_links.append((data_set_idx, rep_link))

        rep_global_poses = {}
        for (data_set_idx, rep_link) in rep_links:
            # 処理対象データセット
            data_set = self.options.data_set_list[data_set_idx]
            # 処理対象カメラオプション
            camera_option = self.camera_options[data_set_idx]
            
            # 先モデルのそれぞれのグローバル位置
            rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, rep_link, data_set.motion, fno)

            for bone_name, rep_vec in rep_global_3ds.items():
                if (data_set_idx, bone_name) in data_bone_name_list:
                    # 処理対象ボーンである場合、データを保持
                    rep_global_poses[(data_set_idx, bone_name)] = rep_vec.data()

        return rep_global_poses

    # プロジェクション座標からグローバル座標の位置際算出
    def calc_unproject_vec_from_square(self, cf: VmdCameraFrame, square_vec: MVector3D):
        # モデル座標系
        model_view = self.create_model_view(cf)

        # プロジェクション座標系
        projection_view = self.create_projection_view(cf)

        # viewport
        viewport_rect = MRect(0, 0, 16, 9)

        # 画面サイズに広げる
        project_vec = square_vec * MVector3D(16, 9, 1)

        # グローバル座標位置
        grobal_vec = project_vec.unproject(model_view, projection_view, viewport_rect)

        return grobal_vec

    # プロジェクション座標正規位置算出
    def calc_project_vec(self, cf: VmdCameraFrame, global_vec: MVector3D):
        # モデル座標系
        model_view = self.create_model_view(cf)

        # プロジェクション座標系
        projection_view = self.create_projection_view(cf)

        # viewport
        viewport_rect = MRect(0, 0, 16, 9)

        # プロジェクション座標位置
        project_vec = global_vec.project(model_view, projection_view, viewport_rect)

        return project_vec

    # プロジェクション座標正規位置算出
    def calc_project_square_vec(self, cf: VmdCameraFrame, global_vec: MVector3D):
        # モデル座標系
        model_view = self.create_model_view(cf)

        # プロジェクション座標系
        projection_view = self.create_projection_view(cf)

        # viewport
        viewport_rect = MRect(0, 0, 16, 9)

        # プロジェクション座標位置
        project_vec = global_vec.project(model_view, projection_view, viewport_rect)

        # プロジェクション座標正規位置
        project_square_vec = MVector3D()
        project_square_vec.setX(project_vec.x() / 16)

        if cf.length <= 0:
            project_square_vec.setY((-project_vec.y() + 9) / 9)
        else:
            project_square_vec.setY(project_vec.y() / 9)
        
        project_square_vec.setZ(project_vec.z())

        return project_square_vec

    # プロジェクション座標系作成
    def create_projection_view(self, cf: VmdCameraFrame):
        mat = MMatrix4x4()
        mat.setToIdentity()
        # MMDの縦の視野角。
        # https://ch.nicovideo.jp/t-ebiing/blomaga/ar510610
        mat.perspective(cf.angle * 0.98, 16 / 9, 0.001, 50000)

        return mat

    def calc_camera_qq(self, cf: VmdCameraFrame):
        # カメラ角度
        camera_qq = MQuaternion.fromEulerAngles(-math.degrees(cf.euler.x()), math.degrees(cf.euler.y()), math.degrees(cf.euler.z()))
        camera_qq.setX(-camera_qq.x())
        camera_qq.setScalar(-camera_qq.scalar())

        return camera_qq

    # モデル座標系作成
    def create_model_view(self, cf: VmdCameraFrame):
        # モデル座標系（原点を見るため、単位行列）
        model_view = MMatrix4x4()
        model_view.setToIdentity()

        # カメラ角度
        camera_qq = self.calc_camera_qq(cf)

        # カメラの原点（グローバル座標）
        mat_origin = MMatrix4x4()
        mat_origin.setToIdentity()
        mat_origin.translate(cf.position)
        mat_origin.rotate(camera_qq)
        mat_origin.translate(MVector3D(0, 0, cf.length))
        camera_origin = mat_origin * MVector3D()

        mat_up = MMatrix4x4()
        mat_up.setToIdentity()
        mat_up.rotate(camera_qq)
        camera_up = mat_up * MVector3D(0, 1, 0)

        # カメラ座標系の行列
        # eye: カメラの原点（グローバル座標）
        # center: カメラの注視点（グローバル座標）
        # up: カメラの上方向ベクトル
        model_view.lookAt(camera_origin, cf.position, camera_up)

        return model_view

    # カメラ準備
    def prepare(self, data_set_idx: int):
        data_set = self.options.data_set_list[data_set_idx]

        # 比率準備
        org_total_height, org_face_length, org_heads, rep_total_height, rep_face_length, rep_heads, body_ratio, head_ratio = \
            self.prepare_ratio(data_set_idx, data_set.camera_org_model, data_set.rep_model)

        org_links = []
        org_link_target = {}
        rep_links = {}

        # 体幹系はループ外で定義する
        self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, ["頭頂実体", "頭"], ["頭頂実体", "頭", "首", "首根元", "上半身2", "上半身"])
        self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, ["左目", "頭"], ["左目"])
        self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, ["右目", "頭"], ["右目"])
        
        for direction in ["左", "右"]:
            self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, \
                              ["{0}手首".format(direction), "{0}手首".format(direction)], ["{0}手首".format(direction)])
            self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, \
                              ["{0}つま先実体".format(direction), "{0}足ＩＫ".format(direction)], ["{0}つま先実体".format(direction), "{0}足底実体".format(direction), "{0}足ＩＫ".format(direction)])
            self.prepare_link(data_set.camera_org_model, data_set.rep_model, data_set.camera_offset_y, org_links, org_link_target, rep_links, \
                              ["{0}足".format(direction), "下半身"], ["{0}足".format(direction)])

        self.camera_options[data_set_idx] = CameraOption(org_links, org_link_target, rep_links, org_total_height, org_face_length, org_heads, \
                                                         rep_total_height, rep_face_length, rep_heads, body_ratio, head_ratio)

    def prepare_ratio(self, data_set_idx: int, org_model: PmxModel, rep_model: PmxModel):
        data_set = self.options.data_set_list[data_set_idx]
        org_total_height, org_face_length, org_heads = self.calc_ratio(data_set_idx, org_model, "作成元", 0)
        rep_total_height, rep_face_length, rep_heads = self.calc_ratio(data_set_idx, rep_model, "変換先", data_set.camera_offset_y)

        # 全身比率
        body_ratio = rep_total_height / org_total_height

        # 顔の大きさ比率
        head_ratio = rep_face_length / org_face_length

        logger.info("【No.%s】作成元モデル 全長: %s, 頭身: %s, 顔の大きさ: %s", (data_set_idx + 1), round(org_total_height, 5), round(org_heads, 5), round(org_face_length, 5))
        logger.info("【No.%s】変換先モデル 全長: %s, 頭身: %s, 顔の大きさ: %s, Yオフセット: %s", (data_set_idx + 1), round(rep_total_height, 5), round(rep_heads, 5), round(rep_face_length, 5), data_set.camera_offset_y)

        return org_total_height, org_face_length, org_heads, rep_total_height, rep_face_length, rep_heads, body_ratio, head_ratio
        
    def calc_ratio(self, data_set_idx: int, model: PmxModel, model_type: str, camera_offset_y: float):
        if model.head_top_vertex.index < 0:
            logger.warning("【No.%s】%sモデルの頭頂頂点INDEXが見つからなかったため、頭ボーン＋上半身半分の位置で代用します。\n" \
                           + "全長Yオフセットで頭頂位置を調整すると、カメラの見切れ等が少なくなります。", (data_set_idx + 1), model_type)
        else:
            logger.info("【No.%s】%sモデルの頭頂頂点INDEX: %s (%s)", (data_set_idx + 1), model_type, model.head_top_vertex.index, \
                        model.head_top_vertex.position.to_log())
        
        face_length = 1
        if "頭" in model.bones:
            # 顔の大きさ
            face_length = model.bones["頭頂実体"].position.y() - model.bones["頭"].position.y()

            if face_length == 0:
                if "首" in model.bones:
                    # 頭がなくて首がある場合、首までの長さ
                    face_length = model.bones["頭頂実体"].position.y() - model.bones["首"].position.y()
                else:
                    # 首もなければ比率1
                    return 1, 1, 1

        # 全身の高さ
        total_height = model.bones["頭頂実体"].position.y()

        # オフセットを加算する
        total_height += camera_offset_y
        face_length += camera_offset_y
            
        # 顔の大きさ / 全身の高さ　で頭身算出
        return total_height, face_length, total_height / face_length

    def prepare_link(self, org_model: PmxModel, rep_model: PmxModel, camera_offset_y: float, org_links: list, org_link_target: dict, \
                     rep_links: dict, link_bone_name_list: list, target_bone_name_list: list):
        if (link_bone_name_list[0] in org_model.bones and link_bone_name_list[0] in rep_model.bones) or \
                (link_bone_name_list[1] in org_model.bones and link_bone_name_list[1] in rep_model.bones):
            # 元と先の両方に末端があればリンク作成
            org_link = org_model.create_link_2_top_one(*link_bone_name_list)

            # 先は、判定対象ボーンとそのボーンを生成するリンクのペアを登録する
            rep_target_bone_name_list = []
            for target_bone_name in target_bone_name_list:
                if target_bone_name in org_link.all().keys() and target_bone_name in rep_model.bones:
                    # 元リンクの中にあり、かつ先ボーンの中にある場合のみ登録
                    rep_link = rep_model.create_link_2_top_one(target_bone_name)

                    # 頭頂実体がある場合、Yオフセット加味
                    if "頭頂実体" == target_bone_name:
                        rep_link.get("頭頂実体").position.setY(float(rep_link.get("頭頂実体").position.y()) + float(camera_offset_y))

                    rep_links[target_bone_name] = rep_link
                    rep_target_bone_name_list.append(target_bone_name)

            if len(rep_target_bone_name_list) > 0:
                # 先に処理対象が１件でもある場合、リンク登録
                # リンクINDEXで参照するボーン名リストを保持する
                for bone_name in rep_target_bone_name_list:
                    org_link_target[bone_name] = len(org_links)
                org_links.append(org_link)
            else:
                # 処理対象がない場合、スルー
                pass

    # 処理対象データセットINDEX取得
    def get_target_set_idxs(self):
        target_data_set_idxs = []
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                continue
                
            target_data_set_idxs.append(data_set_idx)

        return target_data_set_idxs


# カメラオプション
class CameraOption():
    def __init__(self, org_links: list, org_link_target: dict, rep_links: dict, org_total_height: float, org_face_length: float, org_heads: float, \
                 rep_total_height: float, rep_face_length: float, rep_heads: float, body_ratio: float, head_ratio: float):
        super().__init__()

        self.org_links = org_links
        self.org_link_target = org_link_target
        self.rep_links = rep_links

        self.org_total_height = org_total_height
        self.org_face_length = org_face_length
        self.org_heads = org_heads
        self.rep_total_height = rep_total_height
        self.rep_face_length = rep_face_length
        self.rep_heads = rep_heads
        self.body_ratio = body_ratio
        self.head_ratio = head_ratio

