# narou2az
Make Aozora-bunko format text from syosetu.com (Syosetsuka ni narou)

「小説家になろう」にアップされている作品を、ひとつの青空文庫形式テキストファイルにまとめます。Python3とBeautifulSoup4が必要です。
改変などはご自由に。ご利用は自己責任で。

【2023/05/24】 update: 1000話を超える作品への対応(ex. n8920ex)

【2024/03/09】 update: リクエストヘッダの付加

【2024/03/15】 update: リニューアルに伴い作品情報ページの話数が「部分」から「エピソード」に変わったことへ対応

【2024/03/21】 update: 3/15のアップデートでのtypoを修正

【2024/03/21】 append: 「読書尚友」で読むときにルビ表示が乱れることの対策を追加(narou2az_d.py, ruby_chk.py, ruby_conv.py)

【2024/04/25】 update: ルビ仕様の変更へ対応(narou2az.py, narou2az_d.py)

【2024/09/19】 update: 章・節タイトル、連番、本文のタグ仕様変更に対応(narou2az.py, narou2az_d.py)

【2025/01/02】 update: 本文から前書き・後書きを取り除いた(narou2az.py, narou2az_d.py)

<hr>
開発経過と内容については次のブログ記事を参照下さい。なお、こちらのリポジトリでの初期バージョンは2021/05/03の大文字NCODE対応時です。

2020/03/07 「小説家になろう」のテキストに、青空文庫形式の注記を付けて読む https://pado.tea-nifty.com/top/2020/03/post-f681c6.html 

2020/03/12 「なろう一括取得から青空文庫形式」の改良版 https://pado.tea-nifty.com/top/2020/03/post-411779.html 

2020/03/16 Pythonリファクタリング初体験(*1) https://pado.tea-nifty.com/top/2020/03/post-b8e3d3.html 

2020/07/15 「なろう一括取得から青空文庫形式」の小見出しに連番を付与(*1) https://pado.tea-nifty.com/top/2020/07/post-a9677f.html 

2021/05/03 「なろう一括取得から青空文庫形式」の大文字NCODE対応(*1) https://pado.tea-nifty.com/top/2021/05/post-d496bf.html 

2021/05/03 「なろう一括取得から青空文庫形式」のバージョン管理をGitHubに移します（2021/06/17追記） https://pado.tea-nifty.com/top/2021/05/post-18da7d.html 

2024/03/21 「なろう」から取得した青空文庫形式ファイルと「読書尚友」の相性対策 https://pado.tea-nifty.com/top/2024/03/post-fdf665.html

*1 : その時点での旧版も掲載しています
