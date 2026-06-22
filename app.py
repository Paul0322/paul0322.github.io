from datetime import datetime, timezone, timedelta
import os
import re
import sys
import webbrowser

from bs4 import BeautifulSoup
from dateutil import parser
from flask import Flask, jsonify, render_template, request
import requests


if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
    app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"))
else:
    app = Flask(__name__)


TAIPEI_TZ = timezone(timedelta(hours=8))
PBP_CACHE = {}

MLB_TEAMS = {
    "nyy": "紐約洋基", "new york yankees": "紐約洋基", "yankees": "紐約洋基",
    "bos": "波士頓紅襪", "boston red sox": "波士頓紅襪", "red sox": "波士頓紅襪",
    "tb": "坦帕灣光芒", "tbr": "坦帕灣光芒", "tampa bay rays": "坦帕灣光芒", "rays": "坦帕灣光芒",
    "bal": "巴爾打摩金鶯", "baltimore orioles": "巴爾的摩金鶯", "orioles": "巴爾的摩金鶯",
    "tor": "多倫多藍鳥", "toronto blue jays": "多倫多藍鳥", "blue jays": "多倫多藍鳥",
    "cle": "克里夫蘭守護者", "cleveland guardians": "克里夫蘭守護者", "guardians": "克里夫蘭守護者",
    "cws": "芝加哥白襪", "chw": "芝加哥白襪", "chicago white sox": "芝加哥白襪", "white sox": "芝加哥白襪",
    "det": "底特律老虎", "detroit tigers": "底特律老虎", "tigers": "底特律老虎",
    "kc": "堪薩斯市皇家", "kcr": "堪薩斯市皇家", "kansas city royals": "堪薩斯市皇家", "royals": "堪薩斯市皇家",
    "min": "明尼蘇達雙城", "minnesota twins": "明尼蘇達雙城", "twins": "明尼蘇達雙城",
    "hou": "休士頓太空人", "houston astros": "休士頓太空人", "astros": "休士頓太空人",
    "laa": "洛杉磯天使", "ana": "洛杉磯天使", "los angeles angels": "洛杉磯天使", "angels": "洛杉磯天使",
    "oak": "奧克蘭運動家", "ath": "奧克蘭運動家", "oakland athletics": "奧克蘭運動家", "athletics": "奧克蘭運動家",
    "sea": "西雅圖水手", "seattle mariners": "西雅圖水手", "mariners": "西雅圖水手",
    "tex": "德州遊騎兵", "texas rangers": "德州遊騎兵", "rangers": "德州遊騎兵",
    "atl": "亞特蘭大勇士", "atlanta braves": "亞特蘭大勇士", "braves": "亞特蘭大勇士",
    "nym": "紐約大都會", "new york mets": "紐約大都會", "mets": "紐約大都會",
    "phi": "費城費城人", "philadelphia phillies": "費城費城人", "phillies": "費城費城人",
    "mia": "邁阿密馬林魚", "miami marlins": "邁阿密馬林魚", "marlins": "邁阿密馬林魚",
    "wsh": "華盛頓國民", "was": "華盛頓國民", "washington nationals": "華盛頓國民", "nationals": "華盛頓國民",
    "chc": "芝加哥小熊", "chicago cubs": "芝加哥小熊", "cubs": "芝加哥小熊",
    "cin": "辛辛那提紅人", "cincinnati reds": "辛辛那提紅人", "reds": "辛辛那提紅人",
    "mil": "密爾瓦基釀酒人", "milwaukee brewers": "密爾瓦基釀酒人", "brewers": "密爾瓦基釀酒人",
    "pit": "匹茲堡海盜", "pittsburgh pirates": "匹茲堡海盜", "pirates": "匹茲堡海盜",
    "stl": "聖路易紅雀", "st. louis cardinals": "聖路易紅雀", "cardinals": "聖路易紅雀",
    "lad": "洛杉磯道奇", "los angeles dodgers": "洛杉磯道奇", "dodgers": "洛杉磯道奇",
    "ari": "亞利桑那響尾蛇", "arizona diamondbacks": "亞利桑那響尾蛇", "diamondbacks": "亞利桑那響尾蛇",
    "col": "科羅拉多洛磯", "colorado rockies": "科羅拉多洛磯", "rockies": "科羅拉多洛磯",
    "sd": "聖地牙哥教士", "sdp": "聖地牙哥教士", "san diego padres": "聖地牙哥教士", "padres": "聖地牙哥教士",
    "sf": "舊金山巨人", "sfg": "舊金山巨人", "san francisco giants": "舊金山巨人", "giants": "舊金山巨人",
}

NPB_TEAMS = {
    "阪神": "阪神虎",
    "タイガース": "阪神虎",
    "Tigers": "阪神虎",
    "DeNA": "橫濱DeNA灣星",
    "横浜DeNA": "橫濱DeNA灣星",
    "ベイスターズ": "橫濱DeNA灣星",
    "BayStars": "橫濱DeNA灣星",
    "巨人": "讀賣巨人",
    "読売": "讀賣巨人",
    "ジャイアンツ": "讀賣巨人",
    "Giants": "讀賣巨人",
    "中日": "中日龍",
    "ドラゴンズ": "中日龍",
    "Dragons": "中日龍",
    "広島": "廣島鯉魚",
    "広島東洋": "廣島鯉魚",
    "カープ": "廣島鯉魚",
    "Carp": "廣島鯉魚",
    "ヤクルト": "養樂多燕子",
    "東京ヤクルト": "養樂多燕子",
    "スワローズ": "養樂多燕子",
    "Swallows": "養樂多燕子",
    "ソフトバンク": "軟銀鷹",
    "福岡ソフトバンク": "軟銀鷹",
    "ホークス": "軟銀鷹",
    "Hawks": "軟銀鷹",
    "日本ハム": "日本火腿鬥士",
    "北海道日本ハム": "日本火腿鬥士",
    "ファイターズ": "日本火腿鬥士",
    "Fighters": "日本火腿鬥士",
    "オリックス": "歐力士猛牛",
    "バファローズ": "歐力士猛牛",
    "Buffaloes": "歐力士猛牛",
    "ロッテ": "羅德海洋",
    "千葉ロッテ": "羅德海洋",
    "マリーンズ": "羅德海洋",
    "Marines": "羅德海洋",
    "楽天": "樂天金鷲",
    "東北楽天": "樂天金鷲",
    "イーグルス": "樂天金鷲",
    "Eagles": "樂天金鷲",
    "西武": "西武獅",
    "埼玉西武": "西武獅",
    "ライオンズ": "西武獅",
    "Lions": "西武獅",
}

KBO_TEAMS = {
    "LG": "LG雙子",
    "한화": "韓華鷹",
    "SSG": "SSG登陸者",
    "삼성": "三星獅",
    "NC": "NC恐龍",
    "KT": "KT巫師",
    "kt": "KT巫師",
    "롯데": "樂天巨人",
    "KIA": "起亞虎",
    "두산": "斗山熊",
    "키움": "培證英雄",
}


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def to_int(value, default=0):
    value = clean_text(str(value))
    return int(value) if value.isdigit() else default


def team_zh(name, league):
    name = clean_text(name)
    table = NPB_TEAMS if league == "NPB" else KBO_TEAMS if league == "KBO" else MLB_TEAMS
    if league == "MLB":
        key = name.lower()
        return table.get(key, table.get(key.replace(".", ""), name))
    for key, value in table.items():
        if key in name:
            return value
    return name


def mlb_team_zh(team):
    for field in ("fileCode", "abbreviation", "teamName", "name", "shortName"):
        translated = team_zh(team
