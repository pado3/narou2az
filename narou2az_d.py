#!/usr/bin/env python3
# 「なろう」で《hoge》をルビ以外にも使っていると読書尚友でルビ扱いされる(ex. n4764du)。
# 文中の《》を全て≪≫へ変換した上で、ルビの部分を《》に戻すスクリプト。
# narou2az.pyにruby_d()関数を追加した。
import os
import re
import ssl
import sys
import time
from bs4 import BeautifulSoup
from urllib import request

# このファイルがあるディレクトリ
dir_base = os.path.dirname(os.path.abspath(__file__))

# Python3.4.3以上では証明書とホスト名の検証を行うのがデフォ。検証しないと指定する。
# （単にバージョンで分けて良いのか、環境依存が無いのかは不明）
if int('{}{}{}'.format(*sys.version_info[0:3])) >= 343:
    ssl._create_default_https_context = ssl._create_unverified_context


# 引数を入れるクラス
class ArgClass:
    def __init__(self, help, reset, text, noin, ncode):
        self.help = help
        self.reset = reset
        self.text = text
        self.noin = noin
        self.ncode = ncode


# 引数の個別チェック
def check_args(args):
    # 引数を入れるクラス
    p = ArgClass(False, False, False, False, "NOCODE")
    for i in range(len(args)-1):
        if "-r" in args[i+1]:   # --resetや-rstなどでも引っ掛ける
            p.reset = True
            print("取得済みファイルがあってもイチから取得し直します")
        elif "-t" in args[i+1]:  # --textや-txtなどでも引っ掛ける
            p.text = True
            print("青空文庫形式の注記は付けず、単なるテキストを取得します")
        elif "-n" in args[i+1]:   # --noinputなどでも引っ掛ける
            p.noin = True
            print("引数のNコードがおかしくても入力を促しません")
        else:
            # マッチしない文字列があるときは仮にNコードだとみなし、後でチェックする。
            p.ncode = args[i+1]
    if p.text is False:
        print("青空文庫形式の注記を付けます")
    return p


# 引数を取得し、helpが含まれていれば表示して終了、
# helpが無ければ引数個別チェックに回して、mainへ必要な引数を返す
def get_args():
    # Pythonスクリプトに渡されたコマンドライン引数のリスト。 argv[0] はスクリプトの名前
    args = sys.argv
    # helpがあったら表示して終了
    if "-h" in args or "--help" in args:
        print("「小説家になろう」の作品テキストを青空文庫形式にまとめます")
        print("usage :", args[0], " [-r] [-n] [-t] [-h] [Nコード]")
        print("\tNコード : 作品のNコード または 作品ページのURL")
        print("\t -r     : イチから取得し直す")
        print("\t -t     : 青空文庫形式の注記を付けず、単なるテキストを取得")
        print("\t -n     : 引数のNコードがおかしくても入力を促さない")
        sys.exit("\t -h     : この画面")
    # helpが無ければ引数チェックして返す
    return check_args(args)


# 本文スープと前章タイトルとテキストフラグから、
# サブタイと今章タイトルを返す
def get_subtitle(hon_soup, pre_chap, textF):
    # サブタイの文字列を初期化
    subt = ""
    # 章タイトルと節タイトルと連番を取得
    chap_t = hon_soup.find(class_="chapter_title")
    sect_t = hon_soup.find(class_="novel_subtitle")
    novel_n = hon_soup.select_one("#novel_no").text.strip().split("/")[0]
    # 章タイトルがある場合
    if chap_t:      # 前はchap_t is not Noneと書いていた
        # 前の章タイトルと違ったら今章タイトルを代入し章タイトルを付ける
        if chap_t.text != pre_chap:
            pre_chap = chap_t.text
            subt += chap_t.text
            if textF:
                subt += "\n"
            else:    # 青空文庫形式の注記
                subt += "［＃「" + chap_t.text + "」は中見出し］\n"
    # 節タイトルを付ける 2020/07/15 連番付与
    # 検索のため番号のあとにspを1つ付けたが、読書尚友では無視されてしまった
    sect = sect_t.text + " #" + novel_n + " "
    if textF:
        subt += sect + "\n"
    else:    # 青空文庫形式の注記
        subt += sect + "［＃「" + sect + "」は小見出し］\n"
    return subt, pre_chap


# Nコードから、
# 小説を保存するフォルダ名
def get_novel_dir(ncode):
    return os.path.normpath(os.path.join(dir_base, "{}".format(ncode)))


# Nコードから、
# 保存するフォルダがなければ作成
def set_novel_dir(ncode):
    novel_dir = get_novel_dir(ncode)
    if not os.path.exists(novel_dir):
        os.mkdir(novel_dir)
    return


# Nコードから、
# すでに保存している部分番号のsetを取得
def get_existing_set(ncode):
    novel_dir = get_novel_dir(ncode)
    # matchさせる部分ファイル名のパターン。数値部分を()で括るのはgroup化の準備。
    re_part = re.compile(r"{}-([0-9]+).txt".format(ncode))
    # ifでマッチするファイルに絞って評価しないと、intがNoneを返してtracebackする
    # 1行に書いていたら107文字でflake8に叱られた
    existing_parts = {int(re_part.match(fn).group(1))
                      for fn in os.listdir(novel_dir)
                      if re_part.match(fn)}
    # 動作としては次の2行と同じ。下の方が分かりやすいがradonによる循環的複雑度CCは3→4に悪化
    # list_parts = [fn for fn in os.listdir(novel_dir) if re_part.match(fn)]
    # existing_parts = set(int(re_part.match(fn).group(1)) for fn in list_parts)
    return existing_parts


# 作品情報ページのスープとテキストフラグから、
# 表紙にするテキストを取得
def get_hyoshi(info_soup, textF):
    # 著者名は全てにテキスト形式で付ける
    hyoshi = "作　"
    # table id="noveltable1"の2つ目のtrのtdエレメントが著者名
    # 1行に書いていたら83文字でflake8に叱られた。
    hyoshi += (info_soup.select_one("#noveltable1")
               .select("tr")[1].select_one("td").text) + "\n"
    # タイトル取得 h1タグはタイトルのみ
    title = info_soup.select_one("h1").text
    # あらすじ取得 table id="noveltable1"のclass="ex"の2つ目のテキスト
    # (=1つ目のtrのtdだが、著者名とは違う取り方をしてみた)
    synop = info_soup.select_one("#noveltable1").select(".ex")[1].text
    if textF:
        # textFがTrueならテキスト形式でタイトルだけ
        hyoshi += title + "\n"
    else:
        # 青空文庫形式の注記とあらすじ
        hyoshi += "［＃ページの左右中央］\n"
        hyoshi += title + "［＃「" + title + "」は大見出し］\n［＃改ページ］\n"
        hyoshi += "あらすじ［＃「あらすじ」は中見出し］\n" + synop + "\n［＃改ページ］\n"
    return hyoshi


# Nコードと思しき文字列とテキストフラグと無入力フラグから、
# Nコードと作品情報ページをチェックし、開ければncodeと話数と表紙を取得、不具合あれば終了
def get_info(ncode, textF, noinF):
    # Nコードのパターン。rで前置することをPythonのraw文字列記法と言い推奨されている
    re_ncode = re.compile(r"(n[0-9]{4}[a-z]{2})", re.IGNORECASE)    # 大文字で来てもOK
    # 入力ミスかブランクか仕様変更で、入力文字列にNコードとマッチするものがないとき
    if not re_ncode.search(ncode):
        # 無入力フラグが立っていなければ、入力してもらう
        if not noinF:
            ncode = input("【ここに「なろう」のURLかNコードをコピーしてペッタン】")
    # Nコードを再確認する
    nsearch = re_ncode.search(ncode)
    if nsearch:    # Nコードと同じフォーマットの文字列が見つかったとき(is not None)
        ncode = nsearch.group(1)
        print("Nコードは【{}】です".format(ncode))
    else:    # 入力してもらっても見つからなかったとき
        sys.exit("Nコードが見つかりませんでした: {}".format(ncode))
    ncode = ncode.lower()    # re.searchは正規表現に従って小文字を返すが念のため
    # 作品情報ページのチェック  ＃ 1行に書いていたら84文字でflake8に叱られた。
    url =\
        "https://ncode.syosetu.com/novelview/infotop/ncode/{}/".format(ncode)
    # ヘッダを付ける
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/122.0.0.0 Safari/537.36"}
    # サイトが開けないことがあるのでtryが必要
    try:
        # res = request.urlopen(url)
        req = request.Request(url, headers=headers)
        res = request.urlopen(req)
    # ここに落ちるのは、そのNコードの作品が無いか、サイトがメンテなどで落ちているとき
    except Exception:
        sys.exit("作品情報ページが開けませんでした: {}".format(url))
    # いよいよ作品情報を取得
    soup = BeautifulSoup(res, "html.parser")
    res.close()
    # 全話数を取得
    # 全話数が1000を超えると「全1,001部分」とカンマが入るのを除去する（ここで他には入らない）
    pre_info = soup.select_one("#pre_info").text.replace(',', '')
    try:
        # 2024/03/14 リニューアル、「部分」→「エピソード」
        # num_parts = int(re.search(r"全([0-9]+)部分", pre_info).group(1))
        num_parts = int(re.search(r"全([0-9]+)エピソード", pre_info).group(1))
    # ここに落ちるのは、単話作品のとき
    except Exception:
        sys.exit("ごめんなさい、単話作品は取得できません。")
    print("全話数：", num_parts, flush=True)
    # 表紙を取得
    hyoshi = get_hyoshi(soup, textF)
    return ncode, num_parts, hyoshi


# Nコードとリセットフラグと全話数から、
# 取得する部分番号のsetを取得
def get_fetch_set(ncode, resetF, num_parts):
    # すでに保存している部分番号のsetを取得。
    existing_parts = get_existing_set(ncode)
    # resetFがTrueならすべての部分を取得する
    if resetF:
        fetch_parts = list(range(1, num_parts+1))
    else:
        # 全話のsetから保存済みのsetを抜くと取得するsetが残る
        fetch_parts = set(range(1, num_parts+1)) - existing_parts
        # set後に演算をしているので念のためsort
        fetch_parts = sorted(fetch_parts)
    return fetch_parts


# Nコードから、
# 章タイトルのファイル名を取得
def get_pretxt(ncode):
    novel_dir = get_novel_dir(ncode)
    # フォルダ内の名前は決め打ち
    return os.path.join(novel_dir, "prechap.txt")


# Nコードとリセットフラグから、
# 章タイトルは、その章の最初のテキストだけに付ける。前回のが保管されていたら利用
def get_prechap(ncode, resetF):
    pretxt = get_pretxt(ncode)
    if resetF:
        # リセットの場合、前のファイルがあったら消しておく
        if os.path.exists(pretxt):
            os.remove(pretxt)
    # 章タイトルの初期化
    pre_chap = ""
    if os.path.exists(pretxt):
        # 前のがあれば読み込んで返す
        f = open(pretxt, 'r', encoding="utf-8")
        pre_chap = f.readline()
        f.close()
    return pre_chap


# Nコードとパート番号と表紙と前章タイトルとテキストフラグから、
# 本文と今章タイトルpre_chapを返す
def get_honbun(ncode, part, pre_chap, textF):
    # 進捗表示、改行せず、バッファさせない
    print("{:d}, ".format(part), end="", flush=True)
    # 本文ページのURL
    url = "https://ncode.syosetu.com/{}/{:d}/".format(ncode, part)
    # ヘッダを付ける
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/122.0.0.0 Safari/537.36"}
    # res = request.urlopen(url)
    req = request.Request(url, headers=headers)
    res = request.urlopen(req)
    # ルビ変換に関わらず処理が統一できるように、パースする前にテキスト化
    htm = res.read().decode("utf-8")
    # textFがFalseなら青空文庫形式のルビを仕込む
    if not textF:    # 1行に書いていたら130文字でflake8に一番叱られた。ここを直すのは簡単。
        htm = htm.replace("<ruby><rb>", "<ruby>｜<rb>")
        htm = htm.replace("<rp>(</rp>", "<rp>《</rp>")
        htm = htm.replace("<rp>)</rp>", "<rp>》</rp>")
        # 一部で半角カッコの代わりに全角カッコが使われていたのに対応 ex. n7856ev/66/
        htm = htm.replace("<rp>（</rp>", "<rp>《</rp>")
        htm = htm.replace("<rp>）</rp>", "<rp>》</rp>")
    soup = BeautifulSoup(htm, "html.parser")
    res.close()
    # サブタイトルを取得
    subt = get_subtitle(soup, pre_chap, textF)
    honbun = subt[0]
    pre_chap = subt[1]
    # 本文はテキストとして取得。ルビは先に変換してある
    honbun += soup.select_one("#novel_honbun").text
    if textF:
        honbun += "\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n"
    else:
        honbun += "\n［＃改ページ］\n"
    return honbun, pre_chap


# Nコードとパート番号と表紙と本文テキストと前章タイトルから、
# パートファイルと章タイトルを保存
def save_part(ncode, part, honbun, pre_chap):
    novel_dir = get_novel_dir(ncode)
    pretxt = get_pretxt(ncode)
    # パートファイル名
    ptxt = os.path.join(novel_dir, "{}-{:03}.txt".format(ncode, part))
    # パートファイル保存
    with open(ptxt, "w", encoding="utf-8") as f:
        f.write(honbun)
    # 章タイトル保存
    f = open(pretxt, 'w', encoding="utf-8")
    f.write(pre_chap)
    f.close()


# Nコードから、
# まとめファイル保存
def save_matome(ncode):
    # すでに保存している部分番号（ここでは最新までの全ファイル）のsetを取得。
    existing_parts = get_existing_set(ncode)
    # まとめファイル名を付ける
    novel_dir = get_novel_dir(ncode)
    matometxt = os.path.join(novel_dir, "{}.txt".format(ncode))
    matomebak = os.path.join(novel_dir, "{}.bak".format(ncode))
    # WindowsのAnacondaで、既にあるファイルへの上書きリネームができなかったので、あれば先に消す
    if os.path.exists(matomebak):
        os.remove(matomebak)
    if os.path.exists(matometxt):
        os.rename(matometxt, matomebak)
    with open(matometxt, 'w', encoding="utf-8") as savefile:
        # set順に読み込んで保存
        for part in existing_parts:
            ptxt = os.path.join(novel_dir, "{}-{:03}.txt".format(ncode, part))
            # WindowsのAnacondaでデフォのSJISでないというエラーが出たため指定
            savefile.write(
                open(ptxt, "r", encoding="utf-8").read())
            # 書き終わる前に次のを書き始めないように、念のためflushする
            savefile.flush()


# 読書尚友向けのruby処理。元々は1行ずつ処理していたが、honbun一括のstrでも処理できる
def ruby_d(line):
    # 読書尚友で化ける元になる'《》'は全て'≪≫'へ置換
    line = line.replace('《', '≪').replace('》', '≫')
    # ルビ開始文字があれば≪≫を探索し《》へ置換
    if '｜' in line:
        # ルビ開始文字の位置リスト
        pos = [c.start() for c in re.finditer('｜', line)]
        # line末尾位置を追加
        pos.append(len(line))
        # lineの頭から「｜地≪フリ≫」を「｜地《フリ》」に1つずつ置換する
        for i in range(len(pos)-1):
            # ルビ開始文字が複数の場合、それらの間に対象があるかチェックして置換
            braL = line[pos[i]:pos[i+1]].find('≪')     # L side bracket
            braR = line[pos[i]:pos[i+1]].find('≫')     # R side bracket
            if 0 < braL and braL < braR:
                # いったんリストにしてから戻す
                # cf. https://qiita.com/tamago324/items/ea39fb541ef9f2cada7f
                line_list = list(line)
                line_list[pos[i] + braL] = '《'
                line_list[pos[i] + braR] = '》'
                line = "".join(line_list)
    return line


# main
def main():
    # 引数を取得しhelpなら終了。
    # 無入力とテキストとリセットのフラグと、Nコードと思しき文字列を取得
    args = get_args()
    resetF = args.reset
    textF = args.text
    # 作品情報チェック、開ければNコード[0]と全話数[1]と表紙[2]を取得、不具合あれば終了
    info = get_info(args.ncode, textF, args.noin)
    ncode = info[0]
    # 小説を保存するフォルダがなければ作成
    set_novel_dir(ncode)
    # 取得する部分番号のsetを取得する。info[1]が全話数
    fetch_parts = get_fetch_set(ncode, resetF, info[1])
    # 前章タイトルを格納したファイルがあれば読み込む。
    pre_chap = get_prechap(ncode, resetF)
    # ここから本文取得、改行しない
    print("取得中： ", end="")
    for part in fetch_parts:
        # アクセスに1秒あける
        time.sleep(1)
        # 本文テキストの初期化
        honbun = ""
        # 第一話にはinfo[2]の表紙を付ける。
        if part == 1:
            honbun = info[2]
        # 本文を読み込み、pre_chapを上書きする
        hon = get_honbun(ncode, part, pre_chap, textF)
        honbun += hon[0]
        pre_chap = hon[1]   # 章をまたいでファイルが飛んでいたら失敗するが、まずない
        # 読書尚友でのルビ化け対策で、ルビでない《》を≪≫に置換する
        honbun = ruby_d(honbun)
        # パートファイルと章タイトルファイルを保存
        save_part(ncode, part, honbun, pre_chap)
    print("ファイル取得完了, 一括ファイル作成中")
    # まとめファイル保存
    save_matome(ncode)
    print("一括ファイル作成完了！")


if __name__ == "__main__":
    main()
