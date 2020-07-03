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


# サンプル実行

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
