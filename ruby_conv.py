#!/usr/bin/env python3
'''
「なろう」で《hoge》をルビ以外にも使っていると読書尚友でルビ扱いされる(ex. n4764du)。
既に取得したファイル中の《》を全て≪≫へ変換した上で、ルビの部分を《》に戻すスクリプト。

ruby_conv.py
    r1.0 2024/03/19 作成
    by @pado3@mstdn.jp
    usage: ./ruby_conv.py infile outfile
'''
import os
import re
import sys


# 入出力ファイルのチェック。出力ファイル名がおかしければ直す。内容には踏み込まない。
def filechk(infile, outfile):
    # 入力ファイルが無ければエラー
    if not os.path.exists(infile):
        sys.exit('入力ファイルが見つかりません')
    # 入力ファイルの拡張子
    ext_in = os.path.splitext(infile)[1]
    # 出力ファイルの拡張子を確認・修正する
    root_out = os.path.splitext(outfile)[0]
    ext_out = os.path.splitext(outfile)[1]
    if ext_out != ext_in:
        mes = '出力の拡張子{0}が入力の{1}と違ったので{1}に変更しました'
        print(mes.format(ext_out, ext_in))
        outfile = root_out + ext_in
    # 出力ファイルが被れば.bakにする、既に.bakがあれば消してしまう
    if os.path.exists(outfile):
        bakfile = root_out + '.bak'
        try:
            os.remove(bakfile)
            print('出力ファイルの.bakがあったのを削除しました')
        except Exception:
            pass
        os.rename(outfile, bakfile)
        print('出力ファイル名が被ったので前のを.bakにしました')
    print('ファイルチェック完了')
    return outfile


# 読書尚友向けのruby処理
def ruby_d(line):
    # 読書尚友で化ける元になる'《》'は全て'≪≫'へ置換
    line = line.replace('《', '≪').replace('》', '≫')
    # ルビ開始文字があれば≪≫を探索し《》へ置換
    if '｜' in line:
        print('R', end='')
        # print('in: {}, '.format(line), end='')
        # ルビ開始文字の位置リスト
        pos = [c.start() for c in re.finditer('｜', line)]
        # print('位置： {}'.format(pos))
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
        # print('out: {}, '.format(line), end='')
    else:
        print('_', end='')
    return line


# main
def demo(infile, outfile):
    # ファイルチェック。出力ファイル名がおかしければ直す。
    outfile = filechk(infile, outfile)
    # ファイルを読み込む
    with open(infile) as f:
        inlines = f.readlines()
    # 1行ずつ処理（こうすることで複数行にまたぐようなトラブルを排除）
    outs = ''   # 結果テキスト
    for line in inlines:
        outs += ruby_d(line)
    print()
    # ファイルを書き込む
    with open(outfile, 'w', encoding="utf-8") as f:
        f.write(outs)
    print("終了！")


# お約束
if __name__ == '__main__':
    # Pythonスクリプトに渡されたコマンドライン引数のリスト。
    # args[0] はスクリプトの名前, len(args)がpython3に渡される引数の数
    args = sys.argv
    if len(args) != 3:
        print('usage: ./ruby.py infile outfile ({})'.format(len(args)))
    else:
        infile = args[1]
        outfile = args[2]
        print('infile: {}, outfile: {}'.format(infile, outfile))
        demo(infile, outfile)
