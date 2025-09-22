import requests
import json

'''
내용 꾸미기 문구
# : 큰 글씨 만들기
* 글자 * : 굵은 글씨 만들기
> : 파란색 블록 생성
[내용](링크) : 글씨에 하이퍼링크 삽입
'''

API_URL = "https://agit.in/webhook/f378693d-0205-4422-8740-59a47e8345c8"     # 직접 발급

# 아지트 글쓰기 ( 내용 )
def AgitPost(agit_txt):
    api_key = API_URL
    headers = {
        "Content-Type": "application/json",
    }
    # text : 내용 입력 ( 참조는 "@LADP" 을 사용하면 자동으로 설정됩니다. )
    payload = {
        "text": agit_txt,
    }
    response = requests.post(api_key, headers=headers, json=payload)
    # 바이트를 문자열로 변환하고 JSON으로 파싱
    data = json.loads(response.content.decode('utf-8'))
    # 'id' 값을 이용하면 해당 글의 댓글을 작성할 수있습니다.
    id_value = data['id']

    return id_value

# 아지트 댓글 ( 내용, 원글 ID )
def AgitPost_comment(agit_txt, id_value):
    api_key = API_URL
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "parent_id": id_value,
        "text": agit_txt
    }

    response = requests.post(api_key, headers=headers, json=payload)

# 아지트 스케쥴 작성 [제목, 내용, 색상, 시작날짜, 종료날짜]
# 시간은 숫자 형식 필요
# 시작시간 = int(start_date.timestamp())
# 종료시간 = int(end_dtea_object.timestamp())
def Agit_schedule(agit_list):
    api_key = API_URL
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "schedule": {
            # 제목
            "title": f"{agit_list[0]}",
            # 종일 체크
            "is_allday": False,
            # 색상 선택 : agit HTML 참고
            "color": f"{agit_list[2]}",
            # 시작 시간
            "starts_at": int(agit_list[3]),
            # 종료 시간
            "ends_at": int(agit_list[4])
        },
        "text": f"{agit_list[1]}"
    }

    response = requests.post(api_key, headers=headers, json=payload)

    # 바이트를 문자열로 변환하고 JSON으로 파싱
    data = json.loads(response.content.decode('utf-8'))

    # 'id' 값을 추출
    id_value = data['id']

    return id_value
