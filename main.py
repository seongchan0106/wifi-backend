from dotenv import load_dotenv  # .env 파일에 저장된 환경변수를 불러오기 위한 함수
from fastapi import FastAPI, Query  # FastAPI 서버 생성과 쿼리 파라미터 처리를 위한 모듈
from fastapi.middleware.cors import CORSMiddleware  # CORS 설정용 미들웨어
import os  # 환경변수 사용
from sqlalchemy import create_engine, text  # 데이터베이스 연결 및 SQL 텍스트 처리
import pandas as pd  # SQL 결과를 DataFrame으로 다루기 위한 라이브러리

load_dotenv()  # .env 파일의 환경변수를 현재 실행 환경에 로드

app = FastAPI()  # FastAPI 애플리케이션 생성

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")  # 프론트엔드 주소를 환경변수에서 읽고, 없으면 기본값 사용
DATABASE_URL = os.getenv("DATABASE_URL")  # 데이터베이스 연결 주소를 환경변수에서 읽기

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,  # 환경변수에 등록된 프론트엔드 주소 허용
        "http://localhost:5173",  # 로컬 개발용 주소 허용
        "http://127.0.0.1:5173",  # 로컬 개발용 주소 허용
    ],
    allow_credentials=True,  # 쿠키/인증정보 포함 요청 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

engine = create_engine(DATABASE_URL)  # 데이터베이스 연결 엔진 생성

@app.get("/")  # 루트 경로 GET 요청 처리
def home():
    return {"message": "FastAPI 서버 실행 중"}  # 서버 동작 확인용 응답

@app.get("/sido")  # 시도 목록 조회 API
def get_sido():
    sql = """
    SELECT DISTINCT sido
    FROM public_wifi
    WHERE sido IS NOT NULL AND sido <> ''
    ORDER BY sido
    """
    df = pd.read_sql(sql, engine)  # SQL 실행 결과를 DataFrame으로 읽기
    return df["sido"].tolist()  # 시도 컬럼만 리스트로 변환하여 반환

@app.get("/sigungu")  # 시군구 목록 조회 API
def get_sigungu(sido: str = Query(...)):
    sql = text("""
    SELECT DISTINCT sigungu
    FROM public_wifi
    WHERE sido = :sido
      AND sigungu IS NOT NULL
      AND sigungu <> ''
    ORDER BY sigungu
    """)
    df = pd.read_sql(sql, engine, params={"sido": sido})  # 선택한 시도에 해당하는 시군구 목록 조회
    return df["sigungu"].tolist()  # 시군구 컬럼만 리스트로 변환하여 반환

@app.get("/wifi/search")  # 와이파이 검색 API
def search_wifi(
    sido: str = Query(default=""),  # 시도 검색 조건
    sigungu: str = Query(default=""),  # 시군구 검색 조건
    keyword: str = Query(default="")  # 키워드 검색 조건
):
    sql = """
    SELECT *
    FROM public_wifi
    WHERE 1=1
    """
    params = {}  # SQL 파라미터 저장용 딕셔너리

    if sido:  # 시도가 입력되었으면
        sql += " AND sido = :sido"  # 시도 조건 추가
        params["sido"] = sido  # 파라미터에 시도 값 저장

    if sigungu:  # 시군구가 입력되었으면
        sql += " AND sigungu = :sigungu"  # 시군구 조건 추가
        params["sigungu"] = sigungu  # 파라미터에 시군구 값 저장

    if keyword:  # 키워드가 입력되었으면
        sql += """
        AND (
            place_name LIKE :keyword
            OR road_address LIKE :keyword
            OR wifi_ssid LIKE :keyword
        )
        """
        params["keyword"] = f"%{keyword}%"  # 부분 검색을 위한 LIKE 패턴 생성

    df = pd.read_sql(text(sql), engine, params=params)  # 완성된 SQL과 파라미터로 데이터 조회
    return df.to_dict(orient="records")  # 결과를 JSON 형태로 반환