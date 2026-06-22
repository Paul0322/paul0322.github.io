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
    "bal": "巴爾的摩金鶯", "baltimore orioles": "巴爾的摩金鶯", "orioles": "巴爾的摩金鶯",
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
        translated = team_zh(team.get(field, ""), "MLB")
        if translated and translated != team.get(field, ""):
            return translated
    return clean_text(team.get("name") or team.get("teamName") or "")


def status_label(status):
    if status in ("Live", "In Progress"):
        return "比賽中"
    if status in ("Final", "Game Over", "Completed Early"):
        return "已結束"
    return "未開賽"


def empty_matchup():
    return {
        "Hitter": "-",
        "Pitcher": "-",
        "HitterCard": {"avg": ".---", "hr": "0", "rbi": "0", "today": "-"},
        "PitcherCard": {
            "era": "-.--", "wl": "-", "innings": "0.0", "pitches": 0,
            "strikes": 0, "balls": 0, "hits": 0, "walks": 0, "strikeouts": 0,
        },
    }


def game_payload(league, game_id, away, home, away_runs=0, home_runs=0, status="未開賽",
                 game_time="", innings=None, venue="", away_hits=0, home_hits=0,
                 away_errors=0, home_errors=0, current_inning=1, is_top=True,
                 balls=0, strikes=0, outs=0, runners=None):
    runners = runners or {}
    return {
        "league": league,
        "GameID": game_id,
        "AwayTeam": away,
        "HomeTeam": home,
        "AwayTeamRuns": away_runs,
        "AwayTeamHits": away_hits,
        "AwayTeamErrors": away_errors,
        "HomeTeamRuns": home_runs,
        "HomeTeamHits": home_hits,
        "HomeTeamErrors": home_errors,
        "Status": status,
        "CurrentInning": current_inning,
        "IsTopInning": is_top,
        "Innings": innings or [],
        "Balls": balls,
        "Strikes": strikes,
        "Outs": outs,
        "RunnerOnFirst": bool(runners.get("first")),
        "RunnerOnSecond": bool(runners.get("second")),
        "RunnerOnThird": bool(runners.get("third")),
        "GameTime": game_time,
        "Venue": venue,
        "Matchup": empty_matchup(),
    }


def fetch_mlb(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        dt = datetime.now(TAIPEI_TZ)

    start = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        "https://statsapi.mlb.com/api/v1/schedule/games/"
        f"?sportId=1&startDate={start}&endDate={end}&hydrate=linescore"
    )

    try:
        data = requests.get(url, timeout=10).json()
    except Exception as exc:
        print(f"[MLB] {exc}")
        return []

    games = []
    for date_node in data.get("dates", []):
        for game in date_node.get("games", []):
            try:
                game_id = str(game.get("gamePk"))
                utc = parser.isoparse(game.get("gameDate", "")).astimezone(timezone.utc)
                tw = utc.astimezone(TAIPEI_TZ)
                if tw.strftime("%Y-%m-%d") != date_str:
                    continue

                teams = game.get("teams", {})
                away_team = teams.get("away", {}).get("team", {})
                home_team = teams.get("home", {}).get("team", {})
                away = mlb_team_zh(away_team)
                home = mlb_team_zh(home_team)

                linescore = game.get("linescore", {})
                score_teams = linescore.get("teams", {})
                away_score = score_teams.get("away", {})
                home_score = score_teams.get("home", {})
                offense = linescore.get("offense", {})
                innings = [
                    {
                        "num": item.get("num", idx + 1),
                        "away": item.get("away", {}).get("runs"),
                        "home": item.get("home", {}).get("runs"),
                    }
                    for idx, item in enumerate(linescore.get("innings", []))
                ]

                abstract = game.get("status", {}).get("abstractGameState", "Preview")
                label = status_label(abstract)
                ar = away_score.get("runs", 0) or 0
                hr = home_score.get("runs", 0) or 0
                if label == "已結束":
                    PBP_CACHE[game_id] = [{"Description": f"終場：{away} {ar} - {hr} {home}"}]
                elif label == "未開賽":
                    PBP_CACHE[game_id] = [{"Description": "比賽尚未開始"}]

                games.append(game_payload(
                    "MLB", game_id, away, home, ar, hr, label,
                    tw.strftime("%Y-%m-%d %H:%M"), innings,
                    game.get("venue", {}).get("name", ""),
                    away_score.get("hits", 0) or 0, home_score.get("hits", 0) or 0,
                    away_score.get("errors", 0) or 0, home_score.get("errors", 0) or 0,
                    linescore.get("currentInning", 1), linescore.get("isTopInning", True),
                    linescore.get("balls", 0), linescore.get("strikes", 0), linescore.get("outs", 0),
                    {"first": "first" in offense, "second": "second" in offense, "third": "third" in offense},
                ))
            except Exception as exc:
                print(f"[MLB Game] {exc}")
    return games


def fetch_npb(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        dt = datetime.now(TAIPEI_TZ)

    url = f"https://npb.jp/games/{dt.year}/schedule_{dt.month:02d}_detail.html"
    target_id = f"date{dt.month:02d}{dt.day:02d}"

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except Exception as exc:
        print(f"[NPB] {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    games = []
    for row in soup.select(f"tr#{target_id}"):
        try:
            team1 = row.select_one(".team1")
            team2 = row.select_one(".team2")
            if not team1 or not team2:
                continue

            link = row.select_one("td a[href*='/scores/']")
            game_id = link["href"].strip("/").replace("/", "_") if link else f"npb_{date_str}_{len(games)}"
            score1 = row.select_one(".score1")
            score2 = row.select_one(".score2")
            place = clean_text(row.select_one(".place").get_text(" ", strip=True)) if row.select_one(".place") else ""
            time_text = clean_text(row.select_one(".time").get_text(" ", strip=True)) if row.select_one(".time") else ""
            away = team_zh(team1.get_text(" ", strip=True), "NPB")
            home = team_zh(team2.get_text(" ", strip=True), "NPB")
            ar = to_int(score1.get_text(strip=True)) if score1 else 0
            hr = to_int(score2.get_text(strip=True)) if score2 else 0
            status = "已結束" if score1 and score2 else "未開賽"
            game_time = f"{date_str} {time_text}".strip()

            PBP_CACHE[game_id] = [{"Description": f"{place} {time_text}".strip() or "NPB官方賽程"}]
            games.append(game_payload("NPB", game_id, away, home, ar, hr, status, game_time, venue=place))
        except Exception as exc:
            print(f"[NPB Game] {exc}")
    return games


def fetch_kbo(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        dt = datetime.now(TAIPEI_TZ)

    url = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"
    payload = {
        "leId": "1",
        "srIdList": "0,9,6",
        "seasonId": str(dt.year),
        "gameMonth": f"{dt.month:02d}",
        "teamId": "",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.koreabaseball.com/Schedule/Schedule.aspx?leaguegubun=KBO",
    }

    try:
        data = requests.post(url, data=payload, headers=headers, timeout=10).json()
    except Exception as exc:
        print(f"[KBO] {exc}")
        return []

    target = f"{dt.month:02d}.{dt.day:02d}"
    current_day = ""
    games = []
    for row_obj in data.get("rows", []):
        cells = row_obj.get("row", [])
        if not cells:
            continue

        if cells[0].get("Class") == "day":
            current_day = clean_text(BeautifulSoup(cells[0].get("Text", ""), "html.parser").get_text(" ", strip=True))
            cells = cells[1:]
        if not current_day.startswith(target) or len(cells) < 2:
            continue

        try:
            time_html = cells[0].get("Text", "")
            play_html = cells[1].get("Text", "")
            relay_html = cells[2].get("Text", "") if len(cells) > 2 else ""
            venue_html = cells[6].get("Text", "") if len(cells) > 6 else ""

            time_text = clean_text(BeautifulSoup(time_html, "html.parser").get_text(" ", strip=True))
            play = BeautifulSoup(play_html, "html.parser")
            spans = [clean_text(span.get_text(" ", strip=True)) for span in play.find_all("span")]
            teams = [item for item in spans if item and item.lower() != "vs" and not item.isdigit()]
            scores = [to_int(item) for item in spans if item.isdigit()]
            if len(teams) < 2:
                continue

            away = team_zh(teams[0], "KBO")
            home = team_zh(teams[-1], "KBO")
            ar = scores[0] if len(scores) >= 2 else 0
            hr = scores[1] if len(scores) >= 2 else 0
            status = "已結束" if len(scores) >= 2 else "未開賽"
            relay = BeautifulSoup(relay_html, "html.parser").select_one("a[href]")
            href = relay["href"] if relay else ""
            match = re.search(r"gameId=([^&]+)", href)
            game_id = match.group(1) if match else f"kbo_{date_str}_{len(games)}"
            venue = clean_text(BeautifulSoup(venue_html, "html.parser").get_text(" ", strip=True))

            PBP_CACHE[game_id] = [{"Description": f"{venue} {time_text}".strip() or "KBO官方賽程"}]
            games.append(game_payload("KBO", game_id, away, home, ar, hr, status, f"{date_str} {time_text}", venue=venue))
        except Exception as exc:
            print(f"[KBO Game] {exc}")
    return games


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/games")
def get_games():
    league = request.args.get("league", "MLB").upper()
    date_str = request.args.get("date", datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d"))

    if league == "MLB":
        games = fetch_mlb(date_str)
    elif league == "NPB":
        games = fetch_npb(date_str)
    elif league == "KBO":
        games = fetch_kbo(date_str)
    else:
        games = []

    order = {"比賽中": 0, "未開賽": 1, "已結束": 2}
    games.sort(key=lambda game: order.get(game["Status"], 9))
    return jsonify({"games": games, "date": date_str, "league": league})


@app.route("/api/playbyplay/<game_id>")
def play_by_play(game_id):
    return jsonify(PBP_CACHE.get(game_id, [{"Description": "暫無即時文字紀錄"}]))



if __name__ == "__main__":
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)