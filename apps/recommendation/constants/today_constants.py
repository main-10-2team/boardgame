QUESTIONS_DATA = {
    1: {
        "key": "categories",
        "text": "1. 오늘은 어떤 게임이 끌리시나요?",
        "type": "multi-select",
        "options": [
            {"id": 1, "label": "상상력을 자극하는 두뇌 퍼즐 같은 느낌", "value": "추상게임"},
            {"id": 2, "label": "치열한 전략과 전술로 승부 보는 느낌", "value": "전략게임"},
            {"id": 3, "label": "수집하고 조합하며 덱을 꾸리는 재미", "value": "컬렉터블 게임"},
            {"id": 4, "label": "가볍게 배우고 모두가 함께 웃는 느낌", "value": "가족게임"},
            {"id": 5, "label": "아이와 함께 쉽게 시작하는 따뜻한 느낌", "value": "어린이게임"},
            {"id": 6, "label": "친구들과 모여 시끌벅적 즐기는 느낌", "value": "파티게임"},
            {"id": 7, "label": "이야기에 몰입하며 세계관을 탐험하는 느낌", "value": "테마게임"},
            {"id": 8, "label": "지휘관이 되어 전장을 읽는 밀도 높은 느낌", "value": "워게임"},
            {"id": 9, "label": "아무거나 좋아요 / 잘 모르겠어요", "value": "상관없음"},
        ],
    },
    2: {
        "key": "players_range",
        "text": "2. 몇 명이서 플레이하시나요?",
        "type": "single-select",
        "options": [
            {"id": 1, "label": "혼자 (1명)", "min": 1, "max": 1},
            {"id": 2, "label": "둘 (2명)", "min": 2, "max": 2},
            {"id": 3, "label": "3–4명", "min": 3, "max": 4},
            {"id": 4, "label": "5–6명", "min": 5, "max": 6},
            {"id": 5, "label": "7명 이상", "min": 7, "max": 100},
        ],
    },
    3: {
        "key": "playtime_range",
        "text": "3. 원하시는 플레이타임을 골라주세요",
        "type": "single-select",
        "options": [
            {"id": 1, "label": "20분 이내", "min": 0, "max": 20},
            {"id": 2, "label": "20–40분", "min": 20, "max": 40},
            {"id": 3, "label": "40–60분", "min": 40, "max": 60},
            {"id": 4, "label": "60–80분", "min": 60, "max": 80},
            {"id": 5, "label": "80분 이상", "min": 80, "max": 999},
        ],
    },
    4: {
        "key": "age_group",
        "text": "4. 플레이어 나이를 알려주세요",
        "type": "single-select",
        "options": [
            {"id": 1, "label": "7–9세", "min": 7, "max": 9},
            {"id": 2, "label": "10–12세", "min": 10, "max": 12},
            {"id": 3, "label": "13–17세", "min": 13, "max": 17},
            {"id": 4, "label": "18세 이상", "min": 18, "max": 200},
        ],
    },
    5: {
        "key": "difficulty_range",
        "text": "5. 원하는 난이도를 골라주세요",
        "type": "single-select",
        "options": [
            {"id": 1, "label": "입문 (쉬움)", "min": 1, "max": 2},
            {"id": 2, "label": "초보 (중간)", "min": 2, "max": 4},
            {"id": 3, "label": "고수 (어려움)", "min": 4, "max": 5},
        ],
    },
}
