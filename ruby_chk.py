#!/usr/bin/env python3
'''
「なろう」で《hoge》をルビ以外にも使っていると読書尚友でルビ扱いされる(ex. n4764du)。
ルビ以外に使っている《》を検出して、該当行をコンソール出力するスクリプト。

ruby_chk.py
    r1.0 2024/03/21 作成
    by @pado3@mstdn.jp
    usage: ./ruby_chk.py infile
'''
import os
import sys


# 入力ファイルのチェック
def filechk(infile):
    # 入力ファイルが無ければエラー
    if not os.path.exists(infile):
        sys.exit('入力ファイルが見つかりません')
    print('ファイルチェック完了')


# rubyチェック
def ruby_chk(i, line):
    # 《があればルビ開始文字を確認
    if '《' in line:
        # ルビ開始文字無ければ作中で文字化けする可能性がある
        if '｜' not in line:
            print('{}行目: {}'.format(i, line))


# main
def demo(infile):
    # ファイルチェック
    filechk(infile)
    # ファイルを読み込む
    with open(infile) as f:
        inlines = f.readlines()
    # 1行ずつ処理（こうすることで複数行にまたぐようなトラブルを排除）
    for i, line in enumerate(inlines):
        ruby_chk(i, line)
    print("終了！")


# お約束
if __name__ == '__main__':
    # Pythonスクリプトに渡されたコマンドライン引数のリスト。
    # args[0] はスクリプトの名前, len(args)がpython3に渡される引数の数
    args = sys.argv
    if len(args) != 2:
        print('usage: ./ruby_chk.py infile ({})'.format(len(args)))
    else:
        infile = args[1]
        print('infile: {}'.format(infile), end='')
        demo(infile)
