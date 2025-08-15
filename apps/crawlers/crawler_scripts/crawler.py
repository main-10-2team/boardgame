import os
import re
import time

import mechanicalsoup#type: ignore
import numpy as np
import pandas as pd#type: ignore

# --- 기존 크롤링 코드는 여기에 그대로 유지 ---
# (StatefulBrowser 설정, extract_genres 함수, 게임 ID 수집, 상세 정보 크롤링 루프)

# 블락 방지를 위해 time 모듈 추가
browser = mechanicalsoup.StatefulBrowser(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


# 헬퍼 함수: 게임 장르 (테마)를 추출합니다.
# /credits 페이지를 우선적으로 시도하고, 실패 시 메인 상세 페이지로 폴백합니다.
def extract_genres(browser_instance, game_id, detail_url):#type: ignore
    genres = []

    # 1. /credits 페이지에서 장르를 시도합니다.
    credits_url = f"https://www.boardlife.co.kr/game/{game_id}/credits"
    try:
        browser_instance.open(credits_url)
        # 사용자가 제공한 #game-main-content-box > div:nth-child(6) > div.flex-1 선택자 사용
        # 이 요소의 텍스트가 장르 목록을 줄바꿈으로 포함하고 있다고 가정합니다.
        genre_container_from_credits = browser_instance.page.select_one(
            "#game-main-content-box > div:nth-child(6) > div.flex-1"
        )

        if genre_container_from_credits:
            # 텍스트를 줄 단위로 분리합니다.
            lines = genre_container_from_credits.text.strip().split("\n")

            for line in lines:
                korean_text = line.strip()
                # 한글이 포함되어 있고 "더보기"가 아닌 실제 장르 텍스트만 추가
                if any("가" <= char <= "힣" for char in korean_text) and "더보기" not in korean_text:
                    if korean_text not in genres:  # 중복 방지
                        genres.append(korean_text)
            return genres  # 성공적으로 추출했으면 바로 반환

    except Exception as e:
        print(f"  Warning: Failed to crawl genres from {credits_url}: {e}. Falling back to main page for genres.")

    # 2. /credits 페이지에서 장르 추출에 실패했거나 없었다면, 메인 상세 페이지에서 장르를 시도합니다.
    # browser.page가 /credits 페이지로 변경되었을 수 있으므로, 다시 메인 상세 페이지를 엽니다.
    try:
        browser_instance.open(detail_url)
        # 메인 상세 페이지의 '테마' 섹션은 div.title-wrapper.credit.flex 구조를 가집니다.
        theme_section_wrapper = browser_instance.page.select_one("div.title-wrapper.credit.flex:-soup-contains('테마')")

        if theme_section_wrapper:
            # theme_section_wrapper 안에서 div.flex-1과 div.credits-row를 거쳐 모든 <a> 태그를 찾습니다.
            for link_tag in theme_section_wrapper.select("div.flex-1 div.credits-row a"):
                link_text = link_tag.get_text(strip=True)
                if link_text and "더보기" not in link_text and "/game/" not in link_tag.get("href", ""):
                    if link_text not in genres:  # 중복 방지
                        genres.append(link_text)

    except Exception as e:
        print(f"  Error: Failed to crawl genres from main page {detail_url} (fallback): {e}")

    return list(set(genres))  # 최종적으로 수집된 유니크한 장르 목록 반환


# 크롤링된 데이터를 저장할 리스트들
all_titles = []
all_game_details = []

# 랭킹 페이지네이션을 통해 모든 게임 ID를 수집합니다.
base_rank_url = "https://boardlife.co.kr/rank/all"
game_ids = []
seen_game_ids = set()

print("--- 랭킹 페이지에서 게임 ID 수집 시작 ---")
for page_num in range(1, 21):
    paginated_rank_url = f"{base_rank_url}/{page_num}"
    print(f"  > 랭킹 페이지 크롤링: {paginated_rank_url}")

    try:
        response = browser.open(paginated_rank_url, timeout=10)
        rank_rows = browser.page.select("div[id^='rank-row-']")

        if not rank_rows:
            print(f"  경고: {paginated_rank_url} 페이지에서 랭크 요소를 찾을 수 없습니다. 페이지네이션 종료.")
            break

        for rank_row in rank_rows:
            a_tag = rank_row.select_one("a[href*='/game/'][href*='/rate']")
            if a_tag and "href" in a_tag.attrs:
                match = re.search(r"/game/(\d+)/rate", a_tag["href"])
                if match:
                    game_id = match.group(1)
                    if game_id not in seen_game_ids:
                        seen_game_ids.add(game_id)
                        game_ids.append(game_id)

    except Exception as e:
        print(f"  오류: {paginated_rank_url} 접속 또는 ID 파싱 중 에러 발생: {e}")
        continue


# 각 게임 ID로 상세 페이지에 접속하여 타이틀, 이미지, 설명, 장르, 카테고리, 인원, 시간, 연령, 난이도 크롤링
for idx, game_id in enumerate(game_ids, start=1):
    detail_url = f"https://www.boardlife.co.kr/game/{game_id}"
    credits_url_for_info = f"https://www.boardlife.co.kr/game/{game_id}/credits"

    game_title = "제목을 찾을 수 없음"
    game_image_url = "이미지를 찾을 수 없음"
    game_description = "설명을 찾을 수 없음"
    game_categories = []
    game_players = "정보 없음"
    game_playtime = "정보 없음"
    game_age = "정보 없음"
    game_difficulty = "정보 없음"

    try:
        try:
            response = browser.open(credits_url_for_info, timeout=10)
            player_info_div = browser.page.select_one(
                "body > div.wrapper-center.content.game > div.wrapper.center.game > div > div.flex > main > section:nth-child(2) > div:nth-child(3) > div.flex-div.mt-2.mb-2.space.font-17 > dl:nth-child(1) > dd"
            )
            if player_info_div:
                game_players = player_info_div.get_text(strip=True)

            playtime_info_div = browser.page.select_one(
                "body > div.wrapper-center.content.game > div.wrapper.center.game > div > div.flex > main > section:nth-child(2) > div:nth-child(3) > div.flex-div.mt-2.mb-2.space.font-17 > dl:nth-child(2) > dd"
            )
            if playtime_info_div:
                game_playtime = playtime_info_div.get_text(strip=True)

            age_info_div = browser.page.select_one(
                "body > div.wrapper-center.content.game > div.wrapper.center.game > div > div.flex > main > section:nth-child(2) > div:nth-child(3) > div.flex-div.mt-2.mb-2.space.font-17 > dl:nth-child(3) > dd"
            )
            if age_info_div:
                game_age = age_info_div.get_text(strip=True)

            difficulty_info_div = browser.page.select_one("#game-weight")
            if difficulty_info_div:
                game_difficulty = difficulty_info_div.get_text(strip=True)

        except Exception as e:
            print(
                f"  Warning: Failed to crawl player/playtime/age/difficulty from {credits_url_for_info}: {e}. Continuing without this info."
            )
            game_players = "정보 없음"
            game_playtime = "정보 없음"
            game_age = "정보 없음"
            game_difficulty = "정보 없음"

        response = browser.open(detail_url, timeout=10)

        title_tag = browser.page.select_one("a#boardgame-title")
        game_title = title_tag.get_text(strip=True) if title_tag else "제목을 찾을 수 없음"

        og_image_tag = browser.page.select_one("meta[property='og:image']")
        if og_image_tag and "content" in og_image_tag.attrs:
            src_attribute = og_image_tag["content"]
            if src_attribute and not src_attribute.endswith(".svg") and "no-thumb" not in src_attribute:
                if not src_attribute.startswith("http://") and not src_attribute.startswith("https://"):
                    src_attribute = "https://www.boardlife.co.kr" + src_attribute
                game_image_url = src_attribute
            else:
                print(f"  Warning: {detail_url} - og:image 태그에서 유효한 이미지 URL을 찾을 수 없습니다.")
        else:
            main_image_container_div = browser.page.select_one("div.main-img div.a.game-thumb-link")
            if not main_image_container_div:
                main_image_container_div = browser.page.select_one("div.a.game-thumb-link")

            if main_image_container_div and "style" in main_image_container_div.attrs:
                style_attribute_value = main_image_container_div["style"]
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attribute_value)

                if match:
                    src_attribute = match.group(1)
                    if not src_attribute.endswith(".svg") and "no-thumb" not in src_attribute:
                        if not src_attribute.startswith("http://") and not src_attribute.startswith("https://"):
                            src_attribute = "https://www.boardlife.co.kr" + src_attribute
                        game_image_url = src_attribute
                else:
                    print(
                        f"  Warning: {detail_url} - 'div.main-img div.a.game-thumb-link' 태그에서 background-image URL을 찾을 수 없습니다."
                    )
            else:
                print(
                    f"  Warning: {detail_url} - Main image container div (og:image 대체)를 찾을 수 없거나 style 속성이 없습니다."
                )

        description_tag = browser.page.select_one(
            "#game-main-content-box > div.row-box.box-2 > div.row-box.flex-1 > div:nth-child(1) > div.content.description"
        )
        game_description = description_tag.get_text(strip=True) if description_tag else "설명을 찾을 수 없음"

        all_potential_info_sections = browser.page.select("div.row-box.info-box div.credits-box")
        category_found = False
        for credits_box in all_potential_info_sections:
            title_container = credits_box.select_one("div.title-info")

            if title_container:
                section_title = title_container.get_text(strip=True)

                if "카테고리" in section_title:
                    all_links_containers = credits_box.select("div.credits-row")

                    if all_links_containers:
                        for links_container in all_links_containers:
                            for link_tag in links_container.select("a"):
                                link_text = link_tag.get_text(strip=True)
                                link_href = link_tag.get("href", "")

                                if "더보기" not in link_text and "/game/" not in link_href:
                                    if link_text not in game_categories:
                                        game_categories.append(link_text)
                        category_found = True
                    break

        game_genres = extract_genres(browser, game_id, detail_url)#type: ignore

        print(
            f"{idx}위 ({game_id}): {game_title}, 이미지 URL: {game_image_url}, 설명: {game_description[:50]}..., 장르: {game_genres}, 카테고리: {game_categories}, 인원: {game_players}, 시간: {game_playtime}, 연령: {game_age}, 난이도: {game_difficulty}"
        )

        all_game_details.append(
            {
                "id": game_id,
                "title": game_title,
                "image_url": game_image_url,
                "description": game_description,
                "genres": game_genres,
                "categories": game_categories,
                "players": game_players,
                "playtime": game_playtime,
                "age": game_age,
                "difficulty": game_difficulty,
            }
        )
        all_titles.append(game_title)

    except Exception as e:
        print(f"  Error: {detail_url} 접속 또는 파싱 중 에러 발생: {e}")
        print(f"  {idx}위 ({game_id}): 오류 발생 - 이 게임의 정보는 수집되지 않았습니다.")


print("\n--- Crawling complete ---")


print("--- DataFrame 생성 및 데이터 전처리 시작 ---")
df = pd.DataFrame(all_game_details)

# --- DataFrame 생성 및 데이터 전처리 시작 ---
print("--- DataFrame 생성 및 데이터 전처리 시작 ---")
df = pd.DataFrame(all_game_details)

# 크롤링된 데이터에 'players', 'playtime' 열이 없을 경우 오류를 방지하기 위해 빈 열을 먼저 추가
if "players" not in df.columns:
    df["players"] = None
if "playtime" not in df.columns:
    df["playtime"] = None


# 1. 'players' 열을 'min_players'와 'max_players'로 분리
def parse_players(players_str):#type: ignore
    if players_str and "정보" not in str(players_str):
        # 괄호 안의 내용을 제외한 부분에서 숫자(1자리 이상)를 찾습니다.
        # 예: "4(베스트:4인,추천:2인)" -> 괄호 밖의 "4"만 찾음
        clean_str = re.sub(r"\([^)]*\)", "", str(players_str))
        numbers = re.findall(r"\d+", clean_str)

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])

    return np.nan, np.nan


df[["min_players", "max_players"]] = df["players"].apply(lambda x: pd.Series(parse_players(x)))#type: ignore


# 2. 'playtime' 열을 'playtime_min_minutes'와 'playtime_max_minutes'로 분리
def parse_playtime(playtime_str):#type: ignore
    if playtime_str and "정보" not in str(playtime_str):
        clean_str = re.sub(r"[^\d~-]", "", str(playtime_str))
        if "~" in clean_str:
            parts = clean_str.split("~")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]), int(parts[1])
        elif "-" in clean_str:
            parts = clean_str.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]), int(parts[1])
        elif clean_str.isdigit():
            return int(clean_str), int(clean_str)

    return np.nan, np.nan


df[["playtime_min_minutes", "playtime_max_minutes"]] = df["playtime"].apply(lambda x: pd.Series(parse_playtime(x)))#type: ignore


# 3. 'age' 열을 정수형으로 변환
def parse_age(age_str):#type: ignore
    if age_str and "정보" not in str(age_str):
        age_str = str(age_str)
        clean_str = re.sub(r"[^\d+]", "", age_str)  # 숫자와 '+'만 남김
        if clean_str.endswith("+"):
            return int(clean_str[:-1])
        elif clean_str.isdigit():
            return int(clean_str)
    return np.nan


df["age"] = df["age"].apply(parse_age)


# 4. 'difficulty' 열을 실수형으로 변환
def parse_difficulty(difficulty_str):#type: ignore
    if difficulty_str and "정보" not in str(difficulty_str):
        try:
            return float(str(difficulty_str))
        except ValueError:
            return np.nan
    return np.nan


df["difficulty"] = df["difficulty"].apply(parse_difficulty)

# 5. 불필요한 기존 열 제거 및 열 순서 재정렬
df.drop(columns=["players", "playtime"], inplace=True, errors="ignore")
df = df.rename(columns={"id": "game_id", "image_url": "thumbnail_url"})

# Django 모델 필드에 맞게 최종 열 순서 조정 (필요시)
df = df[
    [
        "game_id",
        "title",
        "age",
        "thumbnail_url",
        "description",
        "min_players",
        "max_players",
        "playtime_min_minutes",
        "playtime_max_minutes",
        "difficulty",
        "genres",
        "categories",
    ]
]

print("--- 데이터 전처리 완료 ---")
print(df.head())
print(f"\n총 {len(df)}개의 데이터가 DataFrame에 저장되었습니다.")

file_name = "boardgame_data.csv"
try:
    # 'data' 폴더가 없으면 생성
    if not os.path.exists("data"):
        os.makedirs("data")

    file_path = os.path.join("data", file_name)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"\n성공적으로 '{file_path}'에 파일을 저장했습니다. 🎉")
except Exception as e:
    print(f"\nCSV 파일 저장 중 오류 발생: {e}")
