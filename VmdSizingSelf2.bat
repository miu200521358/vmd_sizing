@echo off
rem --- 
rem ---  vmdデータのトレースモデルを変換
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

rem ---  入力vmdファイルパス


rem set INPUT_VMD=vmd\カトラリーモーション(コロン式ミクV3_Re).vmd
rem set INPUT_VMD=vmd\ドーナツホール.vmd
rem set INPUT_VMD=vmd\egorock_miku.vmd
rem set INPUT_VMD="vmd\VIVA Funny Day.vmd"
rem set INPUT_VMD=vmd\animaru-1.vmd
rem set INPUT_VMD=vmd\ベノムモーション.vmd
rem set INPUT_VMD=vmd\初期カメラ.vmd
rem set INPUT_VMD=vmd\乱数初期立ち.vmd
rem set INPUT_VMD="vmd\ダンスモーション（調整ボーン_めんぼう式初音ミク）.vmd"
rem set INPUT_VMD="vmd\命に嫌われている。ダンス_香乃.vmd"
rem set INPUT_VMD="vmd\ダンスモーション（未調整_らいち式ピアスの少年）.vmd"
rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\ONE_OFF_MIND yurie\ONE_OFF_MIND.vmd"

rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\しゃち式 ヘタリアイギリスv1.032\ヘタリアイギリスv1.032.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\ISAO式ミク\I_ミクv4\Miku_V4_準標準.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\128_同田貫正国\同田貫正国しらき式 ver.1.04\同田貫真剣必殺.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかり青江ver1.2 azure式\にっかり青江(内番)ver1.2_160.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかり青江ver1.2 azure式\にっかり青江ver1.2.pmx"



rem set INPUT_VMD=vmd\lamb足ボーン長い人用.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\戦国BASARA\幸村 たぬき式 ver.1.24\真田幸村没第二衣装1.24.pmx"

rem set INPUT_VMD="vmd\VIVA Funny Day(ｘ0.9).vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\カルも式初音ミクver2.0\カルも式初音ミク.pmx"

rem set INPUT_VMD="vmd\2.歩き10L_(40f_前移動20)_全ての親.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\カルも式初音ミクver2.0\カルも式初音ミク.pmx"

rem set INPUT_VMD="vmd\100-end_男性A-歩き-直進→待機(要上半身2).vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\レイ・ヴィヴァルディ Ver GA1.0 CPUX4\Ray\Ray.pmx"

rem set INPUT_VMD="vmd\男踊り_多段.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\roco式日本_ver1.00b\roco式日本_ver1.00b_個人用.pmx"

rem set INPUT_VMD="vmd\おねがいダーリン_Tda式.vmd"
rem set INPUT_VMD="vmd\おねがいダーリン_Tda式_200f.vmd"
rem set INPUT_VMD="vmd\おねがいダーリン_Tda式_ハート.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="vmd\準標準ミク手合わせ.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\ドラマツルギー motion 配布用 moka\ドラマツルギー.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_2人\アンビリーバーズ_モーション ねたろう\アンビリーバーズ_ダンスモーション(初期位置_右).vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\003_三日月宗近\三日月宗近 わち式 （刀ミュインナーβ）\わち式三日月宗近（刀ミュインナーβ）.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_2人\アンビリーバーズ_モーション ねたろう\アンビリーバーズ_ダンスモーション(初期位置_左).vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\005_小狐丸\小狐丸 mono\小狐丸.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\運動\壁蹴りバク転モーション グレイ\壁蹴りバク転.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_3人\ライアーダンス配布用モーション moka\正面目線\miku.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="vmd\アディショナルメモリーモーション.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかり青江ver1.2 azure式\にっかり青江ver1.2.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\はたらきたくないでござるモーション 鈴木燐\はたらきたくないでござるモーション0906.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\神威がくぽ\YM式神威がくぽv13\神威がくぽv1_3.pmx"

rem set INPUT_VMD=vmd\musicx2.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\めんぼう式 初音ミク Ver1.11\めんぼう式 初音ミク ver1.11.pmx"

rem set INPUT_VMD=vmd\回転テスト.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="vmd\地球最後の告白をv106_あぴミク_腕捩り有.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"

rem set INPUT_VMD=vmd\地球最後の告白をv106_あぴミク_962-1000.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\カガリビト あっきー\カガリビト.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\kurokuma式スウェーデン軍服2種ver.2.71\ヘタリア・スウェーデンVer.2.71\スウェーデンver.2.71.pmx"

rem set INPUT_VMD=C:\MMD\vmd_sizing\vmd\test_Tda.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"


rem set INPUT_VMD="vmd\よっしゃあ漢唄\よっしゃあ男歌.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\実人物\ネイキッド・スネークver0.60 やまばと\ネイキッド・スネーク ver0.60.pmx"

rem set INPUT_VMD="vmd\●onmyway.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\Fate\あげぱん式岡田以蔵 Ver1.2\04_スーツ\岡田以蔵（シャツ）.pmx"


rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\武〇士モーション mika\武〇士モーション.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\進撃の巨人\エルヴィンver.2.4-a1dou3\エルヴィン-2.4[シャツ].pmx"


rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\アンノウン・マザーグース ゲッツ／kemo\Unknown_あにまさ式ミクALL.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD=vmd\おねがいダーリン_Lat式_0-200f.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Lat式ミクVer2.31\Lat式ミクVer2.31_Normal_準標準.pmx"


rem set INPUT_VMD=vmd\おねがいダーリン_Tda式_200f.vmd
rem set INPUT_VMD="vmd\おねがいダーリン_Tda式.vmd"
rem set INPUT_VMD="vmd\おねがいダーリン_Tda式_886-965.vmd"
rem set INPUT_VMD="vmd\おねがいダーリン_Tda式_ハート.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="vmd\アンノウンマザーグース【フィンガータットモーション】1.00.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\112_膝丸\膝丸mkmk009b 刀剣乱舞\膝丸mkmk009b\膝丸内番mkmk009b.pmx"

rem set INPUT_VMD=vmd/炭坑節モーション.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\重音テト\Tda式重音テトチャイナ\tda式重音テトチャイナver2.pmx"

rem set INPUT_VMD=vmd/炭坑節モーション_0-880_2.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\重音テト\Tda式重音テトチャイナ\tda式重音テトチャイナver2.pmx"

rem set INPUT_VMD=vmd\shakeit_rin_0-100.vmd
rem set INPUT_VMD=vmd\shakeit_rin_556-691.vmd
rem set INPUT_VMD=vmd\shakeit_rin.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\鏡音リン\鏡音リンAppendXS mqdl\rinApXS.pmx"

rem set INPUT_VMD=vmd\初期姿勢.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD=vmd\腕曲げ_お願い.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"

rem set INPUT_VMD=vmd\戰刃之習モーションver1.01.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\025_一期一振\一期一振 ひわこ式 ver.2.0\一期一振(ひわこ式) ver.2.0.pmx"

rem set INPUT_VMD=vmd\egorock_miku.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\ISAO式ミク\I_ミクv4\Miku_V4_準標準.pmx"

rem set INPUT_VMD=vmd\髭切手合わせ.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"

rem set INPUT_VMD=vmd\桃源恋歌_ノーマルTda式用.vmd
rem set INPUT_VMD=vmd\桃源恋歌_0-500f.vmd
rem set INPUT_VMD=vmd\桃源恋歌_2164-2227.vmd
rem set INPUT_VMD=vmd\桃源恋歌_2036-2353f.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\運動\レン(メルブラ) グレイ\モーション結合20190625.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"

rem set INPUT_VMD=vmd\にんじゃりばんばんMiku（修正版）.vmd
rem set INPUT_VMD=vmd\にんじゃりばんばん冒頭.vmd
rem set INPUT_VMD=vmd\にんじゃりばんばん0-800f.vmd
rem set INPUT_VMD=vmd\にんじゃりばんばん3166-3213f.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD="vmd\Love Me If You Can.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\025_一期一振\一期一振 ひわこ式 ver.2.0\一期一振(ひわこ式) ver.2.0.pmx"

rem set INPUT_VMD=vmd\ベノムモーション.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"


rem set INPUT_VMD=vmd\nekomimi_mikuv2.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD=vmd\クラブマジェスティ.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\戦国BASARA\幸村 たぬき式 ver.1.24\真田幸村没第二衣装1.24.pmx"

rem set INPUT_VMD=vmd\どういうことなの_モーション.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\秋良式ロマーノver.2.1\ロマーノver.2.1.pmx"

rem set INPUT_VMD=vmd\リバーシブル・キャンペーン_さとく式鶯丸(トレス元モデル).vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"

rem set INPUT_VMD=vmd\アンビバレンツ配布用(髭切008c).vmd
rem set INPUT_VMD=vmd\アンビバレンツ配布用(髭切008c)_3260-3933f.vmd
rem set INPUT_VMD=vmd\アンビバレンツ配布用(髭切008c)_6115-6369f.vmd
rem set INPUT_VMD=vmd\アンビバレンツ配布用(髭切008c)_6597-6728.vmd
rem set INPUT_VMD=vmd\アンビバレンツ配布用(髭切008c)_0000-0300f.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"


rem set INPUT_VMD=vmd\腕キーなし.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\ライアーダンスteto_2930-3100f.vmd
rem set INPUT_VMD=C:\MMD\vmd_sizing\vmd\ライアーダンスteto_4767-4906f.vmd
rem set INPUT_VMD=vmd\ライアーダンスteto.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\重音テト\Tda式改変テト・えんじぇぅccvセットVer1.01 coa\Tda式改変テト・えんじぇぅccv ver.1.01\Tda式改変テト・えんじぇうccv Ver1.01.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\重音テト\Tda式重音テトTypeS\Tda式重音テトTypeS.pmx"

rem set INPUT_VMD=vmd\青江用バレリーコ.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかり青江ver1.0 帽子屋式\帽子屋式にっかり青江_親指0追加.pmx"

rem set INPUT_VMD=vmd\ミク用バレリーコ.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD=vmd\ユニバースコロン式.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\コロン式  初音ミクV3_Re_rev.1.2\コロン式  初音ミクV3_Re_rev.1.2(スパッツ)_準標準.pmx"

rem set INPUT_VMD=vmd\kinoko_right.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\らぶ式ちびミク・ネル White （おたもん改変版）\らぶ式ちびミク_White\らぶ式ちびミク_Wv3_準標準.pmx"

rem set INPUT_VMD=vmd\純情スカート.vmd
rem set INPUT_VMD=vmd\純情スカート_0000-0501.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\乱躁滅裂ガール_Tda式-お市パート.vmd
rem set INPUT_VMD=vmd\乱躁滅裂ガール_Tda式-ももてぃんこパート.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\にんじゃりばんばん_ヒカル.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\GUMI\ままま式GUMI β\GUMIβ版修正準標準.pmx"

rem set INPUT_VMD=vmd\デフォルト鶯丸.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準2B対応_20190708_手先なし.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミクV4X_Ver1.00\Tda式初音ミクV4X_Ver1.00.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_2人\淋しい熱帯魚モーション bataki\淋しい熱帯魚さちこ.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\運動\MikuMikuDanceでラジオ体操第一(ミク歌ver) current\radio1_miku.vmd"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"

rem set INPUT_VMD=vmd\リバーシブル・キャンペーン_さとく式鶯丸(トレス元モデル).vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"

rem set INPUT_VMD=vmd\毒占欲_さとく式鶯丸.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"

rem set INPUT_VMD=vmd\連続前宙.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\Vtuber\ミライ アカリ_v1.0\MiraiAkari_v1.0.pmx"

rem set INPUT_VMD=vmd\loki_miku_konafuki2.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\ISAO式ミク\I_ミクv4\Miku_V4_準標準.pmx"

rem set INPUT_VMD=vmd\ダンシング・ヒーロー_センター.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\響喜乱舞.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\ぬこんモーション20190716.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\踊るマネキンVer.2 ささかや\踊る中性マネキン_青.pmx"

rem set INPUT_VMD=vmd\ぬこんモーション20190717_4.vmd
rem set INPUT_VMD=vmd\ぬこんモーション20190717_4_末尾短.vmd
rem set INPUT_VMD=vmd\ぬこんモーション20190717_4_末尾四分割.vmd
rem set INPUT_VMD=vmd\ぬこんモーション20190717_4_2.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

rem set INPUT_VMD=vmd\ドラマツルギー_moka_S字.vmd
rem set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"

set INPUT_VMD=vmd\鶴丸テスト20190731.vmd
set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx"
















rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\091_和泉守兼定\和泉守兼定 わか式 ver.2.0\わか式和泉守兼定(内番)ver.2.0.pmx"
rem set REPLACE_MODEL_PMX=D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\Tda式初音ミク・アペンドVer1.00\Tda式初音ミク・アペンド_Ver1.00.pmx
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\ISAO式ミク\I_ミクv4チャイナ\Miku_V4_黒チャイナ.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\roco式フランス_ver1.02\roco式フランス_CD_ver1.02.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\mkmk式　ヘタリア・ドイツ（mkmk)014(046)ζ\ドイツ（mkmk)014(046)ζ\ドイツ軍服 mkmk 031　ヘタリア\ドイツ軍服   mkmk031　ヘタリア.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\061_愛染国俊\愛染国俊 ぽんず式 ver1.00\ぽんず式愛染国俊ver1.00.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\059_蛍丸\蛍丸 roco式 ver1.03\roco式蛍丸_ver1.03_刀なし.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\045_乱藤四郎\乱藤四郎  茶しゅ式 β\乱藤四郎.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\045_乱藤四郎\乱藤四郎 茶しゅ式 極\極乱.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\039_前田藤四郎\前田藤四郎 酢烏賊式 v1.35\前田藤四郎_通常.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\035_後藤藤四郎\後藤藤四郎 ユタカ式 ver1.3\通常中傷内番真剣\後藤藤四郎1.3(155).pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\047_五虎退\五虎退 りっつ式 v1.42\五虎退.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\009_岩融\岩融 mkmk式 刀ミュ 002\岩融【刀ミュ】mkmk002\岩融【刀ミュ3】mkmk002 刀剣乱舞.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90_Tスタンス.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\055_鶯丸\鶯丸 さとく式 ver0.90\さとく式鶯丸ver0.90_ひじ曲がり.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\027_鯰尾藤四郎\鯰尾藤四郎 かやちょ式 ver1.12\かやちょ式鯰尾藤四郎ver1.12.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\041_秋田藤四郎\秋田藤四郎 すいか式 v1.0\すいか式秋田藤四郎v1.0.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\041_秋田藤四郎\秋田藤四郎 酢烏賊式 v1.6\秋田藤四郎.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ドラクエ\竜酸式グレイグ配布用ver1.09β2\竜酸式グレイグ.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ドラクエ\【MMD】マルティナVer.0.58\★マルティナver.0.58.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ドラクエ\ドワ爺重武装\マジェ鎧ドワ爺.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\Fate\静謐のハサン つみだんご\静謐のハサン.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\059_蛍丸\蛍丸 内番 mqdl\蛍丸.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\043_博多藤四郎\博多藤四郎 すいか式 v1.32\博多藤四郎v1.32.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\013_大典太光世\通常光世_ver0.24 倭\oden_0_24.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\アンジェリーク\オスカー(Ver.1.2) すぐる式\すぐる式オスカー.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかり青江ver1.2 azure式\にっかり青江ver1.2.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\アイマリン\アイマリンちゃん Vol.03 ver1.0\アイマリンちゃんVol.03_準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\アイマリン\アイマリンちゃん Vol.03 ver1.0\アイマリンちゃんVol.03_準標準_Aスタンス.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ジョジョ\ジョナサンver1.1\ジョナサン・ジョースター_準ボーン.pmx"


rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\mkmk式　APヘタリア・ハンガリーmkmk４種017B\ハンガリーmkmk４種017B\ハンガリー　エプロンドレス　016\ハンガリー　エプロンドレス準mkmk017.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\QM式ヘタリア・ハンガリーver.1.02\QM式ハンガリーver.1.02.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\045_乱藤四郎\乱藤四郎 水色式 β\乱藤四郎(通常).pmx"

set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヒプマイ\菓島式ヒプマイデフォルメ12ver.1.01\菓島式デフォルメ飴村乱数\菓島式デフォルメ飴村乱数ver.1.00.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\重音テト\Tda式重音テトチャイナ\tda式重音テトチャイナver2.pmx"


rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\118_へし切長谷部\はせべ 浮石糖式 0.22\浮石糖式はせべ0.22.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\019_にっかり青江\にっかりあおえ nano 正\nanoにっかり青江-正装.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\【刀犬】源氏mkmk002b\髭切【刀犬】mkmk002a刀犬男士\髭切刀犬男士mkmk002a.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\【刀犬】源氏mkmk002b\膝丸【刀犬】mkmk002刀犬男士\膝丸刀犬男士mkmk002.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\128_同田貫正国\同田貫正国しらき式 ver.1.04\同田貫真剣必殺.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\095_山姥切国広\ねん風山姥切ズ_v05 Zinia\158\ねん風山姥切長義内番（大）.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\095_山姥切国広\ねん風山姥切ズ_v05 Zinia\96\ねん風山姥切国広極（大）.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\095_山姥切国広\ねん風山姥切ズ_v05 Zinia\158\ねん風山姥切長義内番（大）.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\095_山姥切国広\ねん風山姥切ズ_v05 Zinia\158\ねん風山姥切長義内番（中）.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\【刀犬】源氏mkmk002b\髭切【刀犬】mkmk002a刀犬男士\髭切刀犬男士小mkmk002a.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\【刀犬】源氏mkmk002b\髭切【刀犬】mkmk002a刀犬男士\髭切刀犬男士mkmk002a.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\152_静形薙刀\静形薙刀みずごろー式0.52\静形薙刀ごろ式0.52.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\140_巴形薙刀\巴形薙刀 みずごろー式 Ver.0.87\巴形薙刀みずごろー式0.87.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\ボロミア ビルボ\ボロミア準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ドラゴンボール\孫悟空ver3,02 かろた\悟空道着\悟空道着160530.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ロボット\タイムマジーン ナエティマス\タイムマジーン.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\meme式 ヘタリア_オーストリア_ver1.03\オーストリア（5巻表紙）ver 1.03.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\013_大典太光世\大典太光世 Msk式 ver1.0\Msk式大典太光世_ver1.0.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\生き物\ニワトリセット Herring\白ニワトリ.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\しゃち式 ヘタリアイギリスv1.032\ヘタリアイギリスv1.032.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04_半角カナ.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04_半角19文字.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ロボット\絶対無敵セットver1.53 お湯\地球防衛組\ゴッドライジンオー.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\カイト準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\鏡音リン_準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\Fate\hoge式源頼光ver1.00\hoge式源頼光ver1.00.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\艦隊これくしょん\やどかり睦月型_rev20170829 less\菊月.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\艦隊これくしょん\やどかり睦月型_rev20170829 less\皐月.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\2B（ヨルハ二号B型） Ver04.07 taka96\na_2b_0407.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\eve_v100_pmx\eve_準標準.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\生き物\踊る猫ver1.02 トローチ\灰白ねこ.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\鏡音リン.pmd"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\初音ミクVer2 準標準2B対応_20190708.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b.pmx"
rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切mkmk(Se)009b_ひじ曲がり.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\011_今剣\今剣 ゆるん式 ver0124\ライブ衣装\今剣インナー.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\007_石切丸\石切丸 帽子屋式 ver1.4（みほとせ衣装）\帽子屋式石切丸（みほとせ第三）.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\東京喰種\東京喰種_米林才子_しもべ式配布用_ver0.5.3\東京喰種_米林才子.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\艦隊これくしょん\prinzeugen 鼈(すっぽん)\prinzeugen.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\ヘタリア\秋良式ロマーノver.2.1\ロマーノver.2.1.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\あぴミク01_Ver.1.04 アレン・ベルル\Appearance Miku_01_Ver.1.04.pmx"

rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\089_歌仙兼定\ねん風 るのじ式 歌仙兼定1.01\るのじ式ねん風歌仙兼定1.01.pmx"

rem set REPLACE_MODEL_PMX=%MODEL_PMX%




rem set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\オリジナル\踊るマネキンVer.2 ささかや\踊る中性マネキン_赤.pmx"

set INPUT_VMD="D:\MMD\MikuMikuDance_v926x64\UserFile\Motion\ダンス_1人\愛言葉III なつき\nac_aikotoba3_pick.vmd"
set MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\らぶ式ミク\らぶ式ミク_準標準.pmx"
rem set REPLACE_MODEL_PMX=D:\MMD\MikuMikuDance_v926x64\UserFile\Model\刀剣乱舞\107_髭切\髭切mkmk009c 刀剣乱舞\髭切mkmk009c\髭切上着無mkmk009b.pmx
set REPLACE_MODEL_PMX="D:\MMD\MikuMikuDance_v926x64\UserFile\Model\VOCALOID\初音ミク\らぶ式ミク\らぶ式ミク_準標準.pmx"


SETLOCAL enabledelayedexpansion
rem set TEST_PARAM_X=1,0,1-,1.75,1.75-
rem set TEST_PARAM_Y=1.75,1.75-,1,0,1-
rem set TEST_PARAM_Z=0,1-,1.75,1.75-,1
set TEST_PARAM_X=1,0,1-
set TEST_PARAM_Y=1-,1,0
set TEST_PARAM_Z=0,1-,1

for %%x in (%TEST_PARAM_X%) do (
    for %%y in (%TEST_PARAM_Y%) do (
        for %%z in (%TEST_PARAM_Z%) do (
            
            set NOW_TEST_X=%%x
            set NOW_TEST_Y=%%y
            set NOW_TEST_Z=%%z
            echo NOW_TEST_X !NOW_TEST_X!
            echo NOW_TEST_Y !NOW_TEST_Y!
            echo NOW_TEST_Z !NOW_TEST_Z!
            
            set TEST_PARAM=!NOW_TEST_X!,!NOW_TEST_Y!,!NOW_TEST_Z!
            echo TEST_PARAM !TEST_PARAM!
            set OUTPUT_PATH="E:\MMD\vmd_sizing\vmd\input_slope23\slope30_!TEST_PARAM!.vmd"
                            
rem ---  python 実行
python src/main.py --vmd_path %INPUT_VMD%  --trace_pmx_path "%MODEL_PMX%"  --replace_pmx_path "%REPLACE_MODEL_PMX%"  --output_path "!OUTPUT_PATH!"  --test_param "!TEST_PARAM!"  --avoidance 0  --avoidance_finger 0  --hand_ik 0  --hand_distance 1.7  --floor_hand 0  --floor_hand_up 1  --floor_hand_down 1  --hand_floor_distance 1.8  --leg_floor_distance 1.5  --finger_ik 0  --finger_distance 1.4  --vmd_choice_values ""  --rep_choice_values ""  --rep_rate_values ""  --camera_vmd_path ""  --camera_pmx_path ""  --camera_y_offset 0  --verbose 2
        )
    )
)

rem set TEST_PARAM_X=x,x-,y,y-,z,z-
rem set TEST_PARAM_Y=y,y-,z,z-,x,x-
rem set TEST_PARAM_Z=z,z-,x,x-,y,y-
rem 
rem for %%x in (%TEST_PARAM_X%) do (
rem     for %%y in (%TEST_PARAM_Y%) do (
rem         for %%z in (%TEST_PARAM_Z%) do (
rem             
rem             set NOW_TEST_X=%%x
rem             set NOW_TEST_Y=%%y
rem             set NOW_TEST_Z=%%z
rem             echo NOW_TEST_X !NOW_TEST_X!
rem             echo NOW_TEST_Y !NOW_TEST_Y!
rem             echo NOW_TEST_Z !NOW_TEST_Z!
rem             
rem             if !NOW_TEST_X! neq !NOW_TEST_Y! (
rem                 if !NOW_TEST_Y! neq !NOW_TEST_Z! (
rem                     set TEST_PARAM=!NOW_TEST_X!,!NOW_TEST_Y!,!NOW_TEST_Z!
rem                     echo TEST_PARAM !TEST_PARAM!
rem                     set OUTPUT_PATH="E:\MMD\vmd_sizing\vmd\input_slope23\slope28_!TEST_PARAM!.vmd"
rem                     
rem rem ---  python 実行
rem python src/main.py --vmd_path %INPUT_VMD%  --trace_pmx_path "%MODEL_PMX%"  --replace_pmx_path "%REPLACE_MODEL_PMX%"  --output_path "!OUTPUT_PATH!"  --test_param "!TEST_PARAM!"  --avoidance 0  --avoidance_finger 0  --hand_ik 0  --hand_distance 1.7  --floor_hand 0  --floor_hand_up 1  --floor_hand_down 1  --hand_floor_distance 1.8  --leg_floor_distance 1.5  --finger_ik 0  --finger_distance 1.4  --vmd_choice_values ""  --rep_choice_values ""  --rep_rate_values ""  --camera_vmd_path ""  --camera_pmx_path ""  --camera_y_offset 0  --verbose 2
rem                 )
rem             )
rem         )
rem     )
rem )




