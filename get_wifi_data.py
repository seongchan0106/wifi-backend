import os  # 운영체제 환경변수 사용
import requests  # API 요청용 라이브러리
import pandas as pd  # 데이터프레임 처리용 라이브러리
from sqlalchemy import create_engine  # 데이터베이스 연결 엔진 생성

SERVICE_KEY = os.getenv("SERVICE_KEY")  # 환경변수에서 공공데이터 API 인증키 불러오기
DATABASE_URL = os.getenv("DATABASE_URL")  # 환경변수에서 DB 연결 주소 불러오기

url = "https://apis.data.go.kr/1741000/free_wifi_info/info"  # 공공 와이파이 API 주소

all_items = []  # 전체 페이지에서 수집한 데이터를 저장할 리스트
page = 1  # 시작 페이지 번호
num_of_rows = 100  # 한 페이지당 요청할 데이터 개수

while True:  # 데이터가 끝날 때까지 반복 수집
    params = {
        "serviceKey": SERVICE_KEY,  # API 인증키
        "pageNo": str(page),  # 현재 페이지 번호
        "numOfRows": str(num_of_rows),  # 한 페이지당 데이터 개수
        "type": "json"  # 응답 형식을 json으로 지정
    }

    response = requests.get(url, params=params, timeout=30)  # API 요청 보내기

    print(f"\n[{page}페이지]")  # 현재 페이지 출력
    print("status_code:", response.status_code)  # 응답 상태코드 출력
    print("response sample:", response.text[:300])  # 응답 본문 일부 출력

    try:
        data = response.json()  # 응답을 JSON 형태로 변환
    except Exception:
        print("JSON 변환 실패")  # JSON 변환 실패 메시지
        print("실제 응답:", response.text[:1000])  # 실제 응답 일부 출력
        break  # 반복 종료

    body = data.get("response", {}).get("body", {})  # 응답 내부 body 추출
    items = body.get("items", {}).get("item", [])  # 실제 데이터 목록 추출

    if not items:  # 더 이상 데이터가 없으면
        print(f"{page}페이지에서 데이터 없음. 수집 종료")  # 수집 종료 메시지
        break  # 반복 종료

    all_items.extend(items)  # 현재 페이지 데이터를 전체 리스트에 추가
    print(f"{page}페이지 수집 완료 / 현재 누적 {len(all_items)}건")  # 누적 개수 출력

    page += 1  # 다음 페이지로 이동

df = pd.DataFrame(all_items)  # 수집된 전체 데이터를 데이터프레임으로 변환

if df.empty:  # 데이터프레임이 비어 있으면
    print("수집된 데이터가 없습니다.")  # 안내 메시지 출력
    exit()  # 프로그램 종료

print("원본 컬럼 목록:", df.columns.tolist())  # 원본 컬럼명 확인

wifi_df = df[
    [
        "INSTL_CTPV_NM",  # 시도명 컬럼
        "INSTL_SGG_NM",  # 시군구명 컬럼
        "INSTL_PLC_NM",  # 설치 장소명 컬럼
        "LCTN_ROAD_NM_ADDR",  # 도로명 주소 컬럼
        "WGS84_LAT",  # 위도 컬럼
        "WGS84_LOT",  # 경도 컬럼
        "WIFI_SSID"  # 와이파이 SSID 컬럼
    ]
].copy()  # 필요한 컬럼만 복사해서 새 데이터프레임 생성

wifi_df.columns = [
    "sido",  # 시도
    "sigungu",  # 시군구
    "place_name",  # 장소명
    "road_address",  # 도로명 주소
    "lat",  # 위도
    "lng",  # 경도
    "wifi_ssid"  # 와이파이 이름
]

wifi_df["lat"] = pd.to_numeric(wifi_df["lat"], errors="coerce")  # 위도를 숫자형으로 변환, 실패 시 NaN 처리
wifi_df["lng"] = pd.to_numeric(wifi_df["lng"], errors="coerce")  # 경도를 숫자형으로 변환, 실패 시 NaN 처리

wifi_df = wifi_df.dropna(subset=["lat", "lng"])  # 위도 또는 경도가 없는 행 제거

print("최종 데이터 개수:", len(wifi_df))  # 최종 남은 데이터 개수 출력

wifi_df.to_csv("wifi_data.csv", index=False, encoding="utf-8-sig")  # CSV 파일로 저장
print("CSV 저장 완료")  # 저장 완료 메시지

engine = create_engine(DATABASE_URL)  # DB 연결 엔진 생성

wifi_df.to_sql(
    name="public_wifi",  # 저장할 테이블 이름
    con=engine,  # DB 연결 엔진
    if_exists="replace",  # 테이블이 이미 있으면 덮어쓰기
    index=False  # 인덱스는 저장하지 않음
)

print("MySQL 적재 완료")  # DB 저장 완료 메시지