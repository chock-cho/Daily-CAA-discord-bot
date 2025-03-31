import json

import os

import requests
import json
from openai import OpenAI
import random
from datetime import datetime, timedelta

# 환경 변수
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
CAT_API_KEY = os.getenv("CAT_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# 요일 매핑
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

def generate_fortune_and_score():
    prompt = (
        "넌 하루에 한번씩 사람들에게 화이팅을 전해주는 행운의 상냥한 고양이, '복냥이'야. 오늘 하루에 대한 긍정적인 운세를 한국어로 한 문장으로 귀엽게 만들어줘. 끝에는 냐옹~ 🐱을 붙여줘."
        "그리고 오늘의 운세 점수를 0에서 100 사이 숫자 하나 랜덤으로 제공해줘. "
        "JSON 형식으로 아래처럼 응답해줘:\n"
        '{\n  "fortune": "운세 텍스트",\n  "score": 87\n}'
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100
    )
    reply = response.choices[0].message.content.strip()
    try:
        data = json.loads(reply)
        return data["fortune"], data["score"]
    except:
        return "오늘은 좋은 일이 있을 거예요. 기대해보세요!", 75

def get_korean_date():
    korea_time = datetime.utcnow() + timedelta(hours=9)
    weekday = WEEKDAY_KOR[korea_time.weekday()]
    return korea_time.strftime(f"%Y.%m.%d({weekday})")

def send_to_discord(image_url, breed_name, fortune, score):
    today_str = get_korean_date()

    message = {
        "content": f"🐈 **Daily CAA** 🐈 \n (Cute Animal Attack 라는 뜻) \n\n **{today_str} , \n 오늘의 랜덤 품종 복냥이🐱가 찾아왔어요!**",
        "embeds": [
            {
                "title": f"오늘의 고양이 품종: {breed_name}",
                "image": {"url": image_url},
                "description": (
                    f"💫 **오늘의 운세**\n{fortune}\n\n"
                    f"🎯 **오늘의 점수:** {score}점 / 100점"
                )
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    res= requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(message), headers=headers)
    print(f"📡 Discord 응답 코드: {res.status_code}")
    print(f"📨 Discord 응답 내용: {res.text}")

def lambda_handler(event, context):
    breed_id, breed_name = get_random_breed_id_and_name()
    cat_image_url = get_cat_image_by_breed(breed_id)
    fortune, score = generate_fortune_and_score()
    send_to_discord(cat_image_url, breed_name, fortune, score)

    return {
        'statusCode': 200,
        'body': json.dumps("랜덤 품종 고양이 + 운세 + 점수 + 날짜 전송 완료 🐈✨")
    }
