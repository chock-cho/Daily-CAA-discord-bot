import json

import os

import requests
import json
from openai import OpenAI
import random
from datetime import datetime, timedelta

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CAT_API_KEY = os.getenv("CAT_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

WEEKDAY_KOR = ['월', '화', '수', '목', '금', '토', '일']

def get_random_breed_id_and_name():
    headers = {"x-api-key": CAT_API_KEY}
    response = requests.get("https://api.thecatapi.com/v1/breeds", headers=headers)
    response.raise_for_status()
    breeds = response.json()

    # 고양이 품종 무작위 선택
    breed = random.choice(breeds)
    return breed['id'], breed['name']

def get_cat_image_by_breed(breed_id):
    headers = {"x-api-key": CAT_API_KEY}
    params = {
        "limit": 1,
        "breed_ids": breed_id,
        "order": "RAND"
    }
    response = requests.get("https://api.thecatapi.com/v1/images/search", headers=headers, params=params)
    response.raise_for_status()
    return response.json()[0]['url']

def generate_fortunes():
    prompt = (
        "넌 하루에 한 번 사람들에게 귀여운 운세를 전해주는 고양이 '복냥이'야. "
        "업무/공부운, 연애운, 건강운, 금전운 네 가지 카테고리별로 각각 한국어 한 문장 운세를 만들어줘. "
        "각 운세는 귀엽고 긍정적이며 사람들에게 희망을 주는 내용이어야 해. "
        "각 카테고리마다 '행운의 아이템'도 함께 알려줘. "
        "반드시 JSON 형식으로만 출력하고, 들여쓰기 없이 한 줄로 응답해. 예시 형식은:\n"
        '{"업무운":{"fortune":"텍스트","lucky_item":"아이템"},"연애운":{"fortune":"텍스트","lucky_item":"아이템"},"건강운":{"fortune":"텍스트","lucky_item":"아이템"},"금전운":{"fortune":"텍스트","lucky_item":"아이템"}}'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()
        print("GPT 응답:", reply)

        parsed = json.loads(reply)
        base_score = random.randint(65, 85)

        fallback = {
            "업무운": {"fortune": "업무가 착착 진행될 거예요, 냐옹~ 🐱", "lucky_item": "노란 볼펜"},
            "연애운": {"fortune": "마음이 통하는 순간이 올 거예요, 냐옹~ 🐱", "lucky_item": "편지"},
            "건강운": {"fortune": "스트레칭이 복이 되는 하루예요, 냐옹~ 🐱", "lucky_item": "요가 매트"},
            "금전운": {"fortune": "작은 소비가 기쁨이 될 거예요, 냐옹~ 🐱", "lucky_item": "동전 지갑"},
        }

        result = {}
        for category in ["업무운", "연애운", "건강운", "금전운"]:
            item = parsed.get(category)
            if isinstance(item, dict) and "fortune" in item and "lucky_item" in item:
                result[category] = {
                    "fortune": item["fortune"],
                    "lucky_item": item["lucky_item"]
                }
            else:
                result[category] = {
                    "fortune": fallback[category]["fortune"],
                    "lucky_item": fallback[category]["lucky_item"]
                }

        # 점수는 마지막에 따로 부여
        for category in result:
            result[category]["score"] = max(50, min(100, base_score + random.randint(-10, 10)))

        return result

    except Exception as e:
        print("GPT 응답 파싱 실패:", e)
        base_score = random.randint(65, 85)
        fallback = {
            "업무운": {"fortune": "업무가 착착 진행될 거예요, 냐옹~ 🐱", "lucky_item": "노란 볼펜"},
            "연애운": {"fortune": "마음이 통하는 순간이 올 거예요, 냐옹~ 🐱", "lucky_item": "편지"},
            "건강운": {"fortune": "스트레칭이 복이 되는 하루예요, 냐옹~ 🐱", "lucky_item": "요가 매트"},
            "금전운": {"fortune": "작은 소비가 기쁨이 될 거예요, 냐옹~ 🐱", "lucky_item": "동전 지갑"},
        }
        return {
            category: {
                "fortune": fallback[category]["fortune"],
                "lucky_item": fallback[category]["lucky_item"],
                "score": max(50, min(100, base_score + random.randint(-10, 10)))
            }
            for category in fallback
        }

def get_korean_date():
    korea_time = datetime.utcnow() + timedelta(hours=9)
    weekday = WEEKDAY_KOR[korea_time.weekday()]
    return korea_time.strftime(f"%Y.%m.%d({weekday})")

def get_emotional_message(score):
    if score >= 80:
        return "✨ 오늘 하루, 복냥이처럼 팔자 좋게 누워있어도 될 만큼 운이 좋아요! 🍀\n"
    elif score >= 50:
        return "😽 무난하지만 노력하면 더 좋아질 하루예요! 복냥이가 응원할게요, 냐옹~ 🐾\n"
    else:
        return "🌧️ 조금은 조심스러운 하루! 그래도 복냥이가 곁에 있으니 괜찮아요, 냐옹~ 🐱\n"

def send_to_discord(image_url, breed_name, fortunes):
    today_str = get_korean_date()

    total_score = sum(data["score"] for data in fortunes.values()) // len(fortunes)

    emotional_message = get_emotional_message(total_score)

    fortune_text = "\n\n".join([
        f"**{category}**\n"
        f"{data['fortune']}\n"
        f"🎯 점수: {data['score']}점 / 100점\n"
        f"🎁 행운의 아이템: {data['lucky_item']}"
        for category, data in fortunes.items()
    ])

    message = {
        "content": (
            f"🐈 **Daily CAA** (Cute Animal Attack) 🐈\n\n"
            f"**{today_str}**\n"
            f"오늘의 랜덤 품종 복냥이🐱가 찾아왔어요!\n\n"
            f"🌟 **총운 평균 점수: {total_score}점 / 100점** 🌟\n"
            f"{emotional_message}"
        ),
        "embeds": [
            {
                "title": f"✨ 오늘의 고양이 품종: {breed_name} ✨",
                "image": {"url": image_url},
                "description": fortune_text
            }
        ]
    }

    headers = {'Content-Type': 'application/json'}
    res = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(message), headers=headers)
    print(f"📡 Discord 응답 코드: {res.status_code}")
    print(f"📨 Discord 응답 내용: {res.text}")


def lambda_handler(event, context):
    breed_id, breed_name = get_random_breed_id_and_name()
    cat_image_url = get_cat_image_by_breed(breed_id)
    fortunes = generate_fortunes()
    send_to_discord(cat_image_url, breed_name, fortunes)

    return {
        'statusCode': 200,
        'body': json.dumps("랜덤 품종 고양이 + 카테고리별 운세 + 점수 + 행운아이템 전송 완료 🐈✨")
    }
