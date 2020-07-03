# substitute_prototype

This software includes the work that is distributed in the Apache License 2.0.


# 基本設計

## 実体と仮想体

実装ではファイルとデータベース(mongoDB)を用いる。
ファイルが実体であり、データベース上の情報は高速化のための仮想体である。
データベースに入れる場合は一度ファイルに実体を置いてからファイルを内容（実体）を読み込みデータベースに入れるように実装している。

これによりデータベースが破棄されても、またデータベースを使用しなくても、ファイルから結果の構成を可能にすることが目的である。

## 構造を置くdirectory
ファイルは物質毎にbasedirで指定されるdirectoryに置かれる。
directoryとsubdirectoryは名前とidを持つ。

物質はfilesystem上でbasedirの下のsubdirectoryに保存される。
SCFなどを何度も行い、結果を別subdirectoryに保存するために異なるsubdirectoryが生成される。

basedir/{id1name} -> basedir/{id2name} -> basedir/{id3name}

と履歴は進む。（それぞれのid?nameはid?を持つ。）

## directory内のmetadata
basedir内のmetadataが現在使われているsubdirectoryの説明情報を持つ。
subdirectoryのmetadataはsubdirectoryの説明情報を持つ。

ユーザーはbasedirでdirectoryを指定すると、basedirのmetadataで指定される現在のsubdirectoryの位置を得て、そのsubdirectoryから構造などにアクセスする。

## basedirの要素
basedirは以下のファイルを必ず持つ。

* basedir/_uuid: uuid of basedir

idは上書きされない。

* basedir/metadata.json: metadata of basedir

metadata内にbasedirの現在のdirectory情報を持つ。

* basedir/{idname}: basedir subdirectory

最初のidname(idとは違う)は0と定義する。

## basedir/{id}の要素
basedir/{idname}は必ず以下のファイルを持つ。
* basedir/{idname}/_uuid: id of basedir/{idname}

idは上書きされない。

* basedir/{idname}/metadata.json: metadata of basedir/{idname}

basedir/{idname}のmetadata は現在の構造のソース構造のidを持つ。
ソース構造のidは別のbasedirのidのはずである。

## metadataの要素
basedir/{idname}のmetadata は
* 目的（purpose）
* その達成度（achievement）

を持つ。

### 目的purposeと達成度achievementの記述

以下に、目的毎にその達成度を記す。

#### "purpose"=="prototype"の場合

subdirectoryが
実験値や構造最適化などで何かにより最適化された構造を持つ事を示す。

以下の組み合わせを持つ。

{"purpose": "prototype", "achievement": "completed"}


#### "purpose"=="converged_ionic"の場合

subdirectory内の構造が構造最適化を行う事を示す。

##### 達成状態の定義
以下の達成状態"achievement"を持つ。

1. "achievement": "to_relax"

これから構造最適化を行うという状態を示す。構造ファイルのみを持つ。

{"purpose": "prototype", "achievement": "completed"}から
{"purpose": "converged_ionic", "achievement": "to_relax"}に
状態遷移する。

2. "achievement": "running"

構造最適化プログラムの入力を作成し、構造最適化プログラム実行している状態を示す。

3. "achievement": "executed"

構造最適化プログラムが終了した状態を示す。

4. "achievement", "completed"

構造最適化が完了した状態を示す。

##### 達成状態の遷移
1. -> 2. -> 3. -> (1.もしくは4.)に遷移する。


# サンプルの説明

purposeとachievementで検索を行い、対応する状態にある物質に対して操作を行っていく。そして状態を変更する。

順序手続き言語向けの実装をしていない。
多くの部分でtuple spaceなどの手順並列法を想定して実装しているが、
手順毎のフローチャートにも変換はできる。

## 初期構造作成過程

以下の過程でデータベースも用いる。

### 20_add_fake_data.py

なる物質を他のdirectoryからコピーして元素置換して物質を増やす。
テストデータ用に生成しているだけなので元素置換した物質は構造最適化されていない。
{"purpose”: “prototype", "achievement": "completed"}にし、データベース上にも置く。

### 30_generate_subs.py
{"purpose”: “prototype", "achievement": "completed"}の物質
の元素置換を行い、それぞれ別のbasedirに置く。そのsubdirectoryは
{"purpose": "converged_ionic", "achievement": "to_relax"}
とする。

## 構造最適化過程
以下で用いる「物質」はbasedirで指定されるdirectory下に実体がある。
{"purpose": "converged_ionic", "achievement":??? }を書き換えて状態を記述していく。
異なる目的を実行する場合はpurposeを変える。(subdirectoryも変える。)

### 40_fakevasprun.py
動作確認用に
{"purpose": "converged_ionic", "achievement": "to_relax"}
となっている物質に対して、vaspの入力を作成し、仮想的に実行する。
仮想的というのはsubdirectoryのmetadataで
{"purpose": "converged_ionic", "achievement": "running"}
にするという意味である。

### 50_fakevaspresult.py
{"purpose": "converged_ionic", "achievement": "running"}
となっている物質に対して、
仮想的に
{"purpose": "converged_ionic", "achievement": "executed"}
にする。
また、ランダムに結果（converged_ionicが達成されたかどうか）
をファイルに書いておく。

### 60_retieve_vaspresult.py
{"purpose": "converged_ionic", "achievement": "executed"}
と成っている物質に対して、
converged_ionicが達成されたら "achievement": "completed"}とし、
達成されていなかったら"achievement": "to_relax"とする。

"achievement": "to_relax"の物質が残っていたら再度40_fakevasprun.pyから実行する。

## DB表示と削除

### 90_show_db.py

databaseの中身の表示。

### 95_remove_collection.py

collectionの削除。


# 実行例
## 20_add_fake_data.py
```
$ python 20_add_fake_data.py
initial database size 71
subsitute elements [['Fe', 'Cu']]
3 directories are created.
subsitute elements [['Ni', 'Cu']]
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/cif.py:1099: UserWarning: Issues encountered while parsing CIF: Some fractional co-ordinates rounded to ideal values to avoid issues with finite precision.
  warnings.warn("Issues encountered while parsing CIF: %s" % "\n".join(self.warnings))
7 directories are created.
subsitute elements [['Cu', 'Co']]
5 directories are created.
subsitute elements [['Zn', 'Cu']]
6 directories are created.
subsitute elements [['Gd', 'Y']]
19 directories are created.
subsitute elements [['Yb', 'Y']]
34 directories are created.
total 74 directories are created.
final database size 145
```

## 30_generate_subs.py
```
$ python 30_generate_subs.py
substitute elements [['Cu', 'Fe']]
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Fe
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-542437_Gd2Zn17,Zn_Cu,Cu_Fe
...
new_basedir /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1261_EuZn,Zn_Cu,Cu_Co
database size 220
75 data to relax
```
## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Fe
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-542437_Gd2Zn17,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-657_YbZn2,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Yb_Y,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-580354_CeNi3,Ni_Cu,Cu_Fe
...
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581942_CeCu6,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1261_EuZn,Zn_Cu,Cu_Co
75 running
```
## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 58, False: 17}) True if converged
75 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
75 data processed.
Counter({'completed': 58, 'to_relax': 17})
```

## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-22311_EuNi5,Ni_Cu,Cu_Fe
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-614455_GdCu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Gd_Y,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1703_YbZn,Zn_Cu,Cu_Fe
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Yb_Y,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581734_Gd2Fe17,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-22311_EuNi5,Ni_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-20089_GdFe2,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1607_YbCu5,Yb_Y,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-2645_YbNi5,Ni_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1665_YbFe2,Fe_Cu,Cu_Ni
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-21305_GdNi5,Ni_Cu,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-567538_YbCu2,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-1703_YbZn,Zn_Cu,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Cu_Co
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-581942_CeCu6,Cu_Co
17 running
```

## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 15, False: 2}) True if converged
17 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
17 data processed.
Counter({'completed': 15, 'to_relax': 2})
```

## 40_fakevasprun.py
```
$ python 40_fakevasprun.py
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-20089_GdFe2,Fe_Cu,Cu_Ni
/home/kino/anaconda3/lib/python3.7/site-packages/pymatgen/io/vasp/sets.py:418: BadInputSetWarning: Relaxation of likely metal with ISMEAR < 1 detected. Please see VASP recommendations on ISMEAR for metals.
  "ISMEAR for metals.", BadInputSetWarning)
run /home/kino/tmp/substitute_prototype/Calc/MGI/mp-636253_GdCu5,Cu_Co
2 running
```

## 50_fakevaspresult.py
```
$ python 50_fakevaspresult.py
Counter({True: 2}) True if converged
2 executed
```

## 60_retieve_vaspresult.py
```
$ python 60_retieve_vaspresult.py
2 data processed.
Counter({'completed': 2})
```

## 90_show_collection.py
```
$ python 90_show_collection.py
[['all', 220], ['to_relax', 0], ['running', 0], ['executed', 0], ['completed', 220]]
```
