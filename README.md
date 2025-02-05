# ☕ Cafe & Wifi API

## 📌 프로젝트 개요
**Cafe & Wifi API**는 사용자들이 카페 정보를 공유하고 검색할 수 있는 API 기반의 웹 애플리케이션입니다.
이 프로젝트는 Flask를 기반으로 개발되었으며, Swagger 문서를 포함하여 RESTful API로 제공됩니다.

## 🚀 주요 기능
### ✅ 1. 카페 정보 관리
- 모든 카페 목록 조회 (`GET /cafes`)
- 새로운 카페 추가 (`POST /cafes`)
- 특정 지역의 카페 검색 (`GET /cafes/location/{location}`)
- 랜덤 카페 추천 (`GET /cafes/random`)
- 카페 상세 정보 조회 (`GET /cafes/{cafe_id}`)
- 카페 정보 수정 요청 (`POST /cafes/{cafe_id}/update-request`)

### 🔒 2. 관리자 기능
- 모든 카페 목록 조회 (`GET /admin/cafes`)
- 카페 삭제 (`DELETE /cafes/{cafe_id}`)
- 카페 수정 요청 목록 조회 (`GET /admin/update-requests`)
- 카페 수정 요청 승인/거부 (`PATCH /admin/update-requests/{request_id}`)
- 카페 수정 요청 삭제 (`DELETE /admin/update-requests/{request_id}`)

## 🛠 기술 스택
- **백엔드**: Flask, Flask-SQLAlchemy, Flask-Migrate
- **데이터베이스**: SQLite
- **API 문서화**: Flasgger (Swagger UI)
- **프론트엔드**: HTML, CSS, JavaScript (Vanilla JS)


## 📂 프로젝트 구조
```
CAFE-WIFI-API/
│-- static/                 # 정적 파일 (CSS, JS)
│-- migrations/             # SQLite DB DATA 이관
│-- templates/              # HTML 템플릿
│-- instance/               # SQLite 데이터베이스
│-- .env                    # 환경 변수 설정 파일
│-- main.py                  # Flask 메인 애플리케이션
│-- requirements.txt        # 프로젝트 종속성 패키지 목록
│-- README.md               # 프로젝트 설명
```

## 📖 API 문서
Swagger를 통해 API 문서를 제공합니다. API 문서는 `/apidocs` 경로에서 확인할 수 있습니다.

## 🔐 관리자 API 보호
관리자 API는 인증이 필요하며, `/admin` 관련 API 접근 시 관리자 토큰이 필요합니다.

## 🛠 프로젝트 설정 및 실행 방법
### 1️⃣ 설치 및 실행
```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 패키지 설치
pip install -r requirements.txt

# Flask 앱 실행
flask run
```

### 2️⃣ 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성하고 아래 내용을 추가하세요.
```env
ADMIN_TOKEN=your_admin_token
ADMIN_DOCS_PASSWORD=your_docs_password
```

### 3️⃣ 데이터베이스 마이그레이션
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 🎨 프론트엔드 UI
### ✅ 기본 페이지
- **홈 (`/`)**: 카페 목록 및 검색 기능 제공
- **카페 추가 (`/add`)**: 새로운 카페 등록 폼
- **정보 수정 요청 (`/update`)**: 카페 정보 수정 요청 폼
- **관리자 로그인 (`/login`)**: 관리자 인증 페이지

### ✅ 관리자 페이지 (`/admin`)
- **카페 목록 관리**
- **수정 요청 승인/거부**

## 📝 개발 로그
1. **카페 CRUD API 개발**
2. **Swagger 문서 작성 및 보호 기능 추가**
3. **관리자 전용 API 보호 (인증 시스템 구현)**
4. **프론트엔드 UI 개선 (CSS 스타일링)**
5. **카페 검색 기능 개선 (검색 실패 시 처리 로직 추가)**

## 🎯 향후 개선 사항
- 📌 **유저 인증 시스템 추가** (JWT 기반 로그인)
- 📌 **Docker 배포 자동화**
- 📌 **PostgreSQL 또는 MySQL로 DB 변경**
- 📌 **React 프론트엔드 연동**

## 📬 문의
- 이 프로젝트에 대한 문의는 개발자 **JELKOV**에게 부탁드립니다.
- [GITHUB 주소](https://github.com/JELKOV?tab=repositories)

