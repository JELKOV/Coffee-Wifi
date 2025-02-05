import random
import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request, render_template, abort, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from datetime import datetime
from flask_migrate import Migrate
from flasgger import Swagger
from flasgger.utils import swag_from

# ─────────────────────────────────────────────
# 📌 1. 환경 변수 설정 및 초기화
# ─────────────────────────────────────────────

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    print("⚠️ WARNING: 관리자 토큰(ADMIN_TOKEN)이 설정되지 않았습니다! 기본값이 사용됩니다.")
    ADMIN_TOKEN = "default-secret-token"  # 기본값 설정 (배포 시 제거 필요!)

# DOCS 비번
ADMIN_DOCS_PASSWORD = os.getenv("ADMIN_DOCS_PASSWORD")
if not ADMIN_DOCS_PASSWORD:
    print("⚠️ WARNING: SWAGGER 관리자 비번이 설정되지 않았습니다! 기본값이 사용됩니다.")
    ADMIN_DOCS_PASSWORD = "password"

# ─────────────────────────────────────────────
# 📌 2. Flask 애플리케이션 및 데이터베이스 설정
# ─────────────────────────────────────────────


app = Flask(__name__)
print("Database file path:", os.path.abspath("cafes.db"))

# DB 생성하기
class Base(DeclarativeBase):
    pass

# DB 연결하기
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "cafes.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_ECHO'] = True  # SQLAlchemy 쿼리 로그 활성화
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Flask-Migrate 설정 추가
migrate = Migrate(app, db)

# API SWAGGER 초기화
app.config["SWAGGER"] = {
    "title": "Cafe & Wifi API",
    "uiversion": 3
}

swagger_template = {
    "definitions": {
        "Cafe": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "name": {"type": "string", "example": "카페 A"},
                "map_url": {"type": "string", "example": "https://maps.example.com/a"},
                "img_url": {"type": "string", "example": "https://images.example.com/a.jpg"},
                "location": {"type": "string", "example": "서울 강남구"},
                "seats": {"type": "string", "example": "50석"},
                "amenities": {
                    "type": "object",
                    "properties": {
                        "has_toilet": {"type": "boolean", "example": True},
                        "has_wifi": {"type": "boolean", "example": True},
                        "has_sockets": {"type": "boolean", "example": False},
                        "can_take_calls": {"type": "boolean", "example": True}
                    }
                },
                "coffee_price": {"type": "string", "example": "₩4,500"}
            }
        },
        "UpdateRequest": {
            "type": "object",
            "properties": {
                "request_id": {"type": "integer", "example": 5},
                "cafe_id": {"type": "integer", "example": 1},
                "proposed_name": {"type": "string", "example": "새로운 카페 이름"},
                "proposed_location": {"type": "string", "example": "서울 종로구"},
                "proposed_coffee_price": {"type": "string", "example": "₩5,000"},
                "status": {"type": "string", "example": "pending"}
            }
        }
    }
}

swagger = Swagger(app, template=swagger_template)

# ─────────────────────────────────────────────
# 📌 3. 데이터 모델 정의 (Cafe, UpdateRequest)
# ─────────────────────────────────────────

# Cafe 테이블 정의하기
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, default=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, default=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, default=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, default=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

# 카페 수정 요청 테이블 정의하기
class UpdateRequest(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cafe_id: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_name: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_location: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_seats: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_map_url: Mapped[str] = mapped_column(String(500), nullable=True)
    proposed_img_url: Mapped[str] = mapped_column(String(500), nullable=True)
    proposed_has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=True)
    proposed_has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=True)
    proposed_has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=True)
    proposed_can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, approved, rejected
    created_at: Mapped[str] = mapped_column(String(250), nullable=False, default=datetime.utcnow().isoformat)

# 테이블 시작시
with app.app_context():
    db.create_all()

## 디버깅용
# with app.app_context():
#     cafes = Cafe.query.all()
#     print(cafes)

# ─────────────────────────────────────────────
# 📌 4. 유틸리티 함수 (카페 데이터 변환, 관리자 확인)
# ─────────────────────────────────────────────

# # 관리자 SWAGGER 문서 보호 (선택사항)
# @app.before_request
# def protect_admin_docs():
#     """Swagger에서 관리자 API 문서 보호"""
#     if request.path.startswith("/apidocs"):  # "/apidocs" 경로 보호
#         auth = request.authorization
#         print("Request Path:", request.path)
#         print("Auth:", auth)
#
#         if not auth or auth.password != ADMIN_DOCS_PASSWORD:
#             return Response(
#                 "관리자 인증이 필요합니다.\n",
#                 401,
#                 {"WWW-Authenticate": 'Basic realm="Login Required"'}
#             )

def cafe_to_dict(cafe):
    return {
        'id': cafe.id,
        'name': cafe.name,
        'map_url': cafe.map_url,
        'img_url': cafe.img_url,
        'location': cafe.location,
        'seats': cafe.seats,
        "amenities": {
            "has_toilet": cafe.has_toilet,
            "has_wifi": cafe.has_wifi,
            "has_sockets": cafe.has_sockets,
            "can_take_calls": cafe.can_take_calls
        },
        "coffee_price": cafe.coffee_price
    }

#  관리자 페이지 접근 권한 확인 함수
def is_admin():
    auth_header = request.headers.get('Authorization')
    cookie_token = request.cookies.get('admin_token')

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1].strip()
        if token == ADMIN_TOKEN:
            return True

    if cookie_token == ADMIN_TOKEN:
        return True

    return False

# 403 Forbidden 예외 처리 (JSON 응답 또는 로그인 페이지로 리디렉트)
def require_admin():
    if not is_admin():
        if request.accept_mimetypes.accept_json:
            abort(403, description="관리자 권한이 없습니다.")
        return redirect(url_for("login_page"))

# ─────────────────────────────────────────────
# 📌 5. 페이지 렌더링 관련 라우트
# ─────────────────────────────────────────────

# [GET] 홈페이지(index.html) 제공
@app.route("/")
def home():
    return render_template("index.html")
# [GET] 카페 추가 페이지
@app.route("/add")
def add_cafe_page():
    return render_template("add.html")
# [GET] 커피 가격 업데이트 페이지
@app.route("/update")
def update_cafe_page():
    return render_template("update.html")

# [GET] 관리자 페이지 이동하기
@app.route("/admin")
def admin_page():
    if not is_admin():
        return redirect(url_for("login_page"))
    return render_template("admin.html")

# 관리자 로그인 페이지 (로그인 후 자동 리디렉트)
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        token = request.form.get("token")
        if token == ADMIN_TOKEN:
            response = redirect(url_for("admin_page"))
            response.set_cookie("admin_token", token, httponly=True, secure=True, samesite="Strict", max_age=3600)
            return response
        return render_template("login.html", error="❌ 잘못된 관리자 토큰!")

    return render_template("login.html")

# 관리자 삭제를 위한 카페 확인페이지 이동
@app.route("/admin/cafes/delete")
def admin_cafes_page():
    if not is_admin():
        return redirect(url_for("login_page"))  # 관리자 권한 없으면 로그인 페이지로 리디렉트
    return render_template("admin_cafes.html")

# [GET] 카페 상세 페이지
@app.route('/cafe/<int:cafe_id>')
def cafe_detail_page(cafe_id):
    return render_template('cafe_detail.html', cafe_id=cafe_id)

# ─────────────────────────────────────────────
# 📌 6. 카페 API (조회, 추가, 검색, 삭제)
# ─────────────────────────────────────────────

# [GET] 모든 카페 조회 API
@app.route("/cafes", methods=["GET"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "모든 카페 조회",
    "description": "데이터베이스에서 모든 카페 정보를 가져옵니다.",
    "responses": {
        200: {
            "description": "카페 리스트 반환",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/Cafe"
                }
            }
        },
        404: {
            "description": "카페가 없음",
            "examples": {
                "application/json": {"error": "No cafes found"}
            }
        }
    }
})
def get_all_cafes():
    cafes = Cafe.query.all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": "No cafes found"}), 404

# [GET] 랜덤 카페 조회 API
@app.route("/cafes/random", methods=["GET"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "랜덤 카페 조회",
    "description": "데이터베이스에서 무작위로 하나의 카페 정보를 반환합니다.",
    "responses": {
        200: {
            "description": "랜덤 카페 정보 반환",
            "schema": {"$ref": "#/definitions/Cafe"},
            "examples": {
                "application/json": {
                    "id": 1,
                    "name": "랜덤 카페",
                    "map_url": "https://maps.example.com/random",
                    "img_url": "https://images.example.com/random.jpg",
                    "location": "서울 강남구",
                    "seats": "40석",
                    "amenities": {
                        "has_toilet": True,
                        "has_wifi": True,
                        "has_sockets": False,
                        "can_take_calls": True
                    },
                    "coffee_price": "₩4,500"
                }
            }
        },
        404: {
            "description": "카페 없음",
            "examples": {
                "application/json": {"error": "No cafes found"}
            }
        }
    }
})
def get_random_cafe():
    cafes = Cafe.query.all()
    if not cafes:  # 빈 리스트일 경우 바로 404 반환
        return jsonify({"error": "No cafes found"}), 404

    random_cafe = random.choice(cafes)
    return jsonify(cafe_to_dict(random_cafe)), 200


# [GET] 개별 카페 정보 조회 API
@app.route("/cafes/<int:cafe_id>", methods=["GET"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "카페 상세 조회",
    "description": "특정 카페의 상세 정보를 조회합니다.",
    "parameters": [
        {
            "name": "cafe_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "조회할 카페의 ID"
        }
    ],
    "responses": {
        200: {
            "description": "카페 정보 반환",
            "schema": {"$ref": "#/definitions/Cafe"}
        },
        404: {
            "description": "카페를 찾을 수 없음",
            "examples": {
                "application/json": {"error": "Cafe not found"}
            }
        }
    }
})
def get_cafe_by_id(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return jsonify({"error": "Cafe not found"}), 404
    return jsonify(cafe_to_dict(cafe)), 200

# [GET] 위치 기반 카페 검색 API
@app.route("/cafes/location/<string:location>", methods=["GET"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "위치 기반 카페 검색",
    "description": "입력한 위치(지역명)를 포함하는 모든 카페 목록을 반환합니다.",
    "parameters": [
        {
            "name": "location",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "검색할 위치(지역명)"
        }
    ],
    "responses": {
        200: {
            "description": "위치 기반 카페 리스트 반환",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/Cafe"
                }
            },
            "examples": {
                "application/json": [
                    {
                        "id": 2,
                        "name": "강남 카페",
                        "map_url": "https://maps.example.com/gangnam",
                        "img_url": "https://images.example.com/gangnam.jpg",
                        "location": "서울 강남구",
                        "seats": "50석",
                        "amenities": {
                            "has_toilet": True,
                            "has_wifi": True,
                            "has_sockets": True,
                            "can_take_calls": False
                        },
                        "coffee_price": "₩5,000"
                    },
                    {
                        "id": 3,
                        "name": "역삼 카페",
                        "map_url": "https://maps.example.com/yeoksam",
                        "img_url": "https://images.example.com/yeoksam.jpg",
                        "location": "서울 강남구 역삼동",
                        "seats": "30석",
                        "amenities": {
                            "has_toilet": False,
                            "has_wifi": True,
                            "has_sockets": True,
                            "can_take_calls": True
                        },
                        "coffee_price": "₩4,800"
                    }
                ]
            }
        },
        404: {
            "description": "검색된 카페 없음",
            "examples": {
                "application/json": {"error": "No cafes found at location '강북구'"}
            }
        }
    }
})
def search_cafes_by_location(location):
    cafes = Cafe.query.filter(Cafe.location.ilike(f"%{location}%")).all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": f"No cafes found at location '{location}'"}), 404

# [POST] 새로운 카페 추가 API
@app.route("/cafes", methods=["POST"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "새로운 카페 추가",
    "description": "새로운 카페 정보를 추가합니다.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "새로운 카페"},
                    "map_url": {"type": "string", "example": "https://maps.example.com/newcafe"},
                    "img_url": {"type": "string", "example": "https://images.example.com/newcafe.jpg"},
                    "location": {"type": "string", "example": "서울 마포구"},
                    "seats": {"type": "string", "example": "30석"},
                    "has_toilet": {"type": "boolean", "example": True},
                    "has_wifi": {"type": "boolean", "example": True},
                    "has_sockets": {"type": "boolean", "example": False},
                    "can_take_calls": {"type": "boolean", "example": True},
                    "coffee_price": {"type": "string", "example": "₩4,500"}
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "카페 추가 성공",
            "examples": {
                "application/json": {"success": "Successfully added new cafe"}
            }
        },
        400: {
            "description": "카페 중복 오류",
            "examples": {
                "application/json": {"error": "A cafe with this name already exists at this location"}
            }
        },
        500: {
            "description": "서버 오류",
            "examples": {
                "application/json": {"error": "Internal Server Error"}
            }
        }
    }
})
def add_cafe():
    try:
        data = request.get_json()  # JSON 데이터 받기
        # 같은 이름의 카페가 같은 위치에 있는지 확인
        existing_cafe = Cafe.query.filter_by(name=data["name"], location=data["location"]).first()
        if existing_cafe:
            return jsonify({"error": "A cafe with this name already exists at this location"}), 400

        new_cafe = Cafe(
            name=data["name"],
            map_url=data["map_url"],
            img_url=data["img_url"],
            location=data["location"],
            has_sockets=bool(data.get("has_sockets", False)),
            has_wifi=bool(data.get("has_wifi", False)),
            has_toilet=bool(data.get("has_toilet", False)),
            can_take_calls=bool(data.get("can_take_calls", False)),
            seats=data.get("seats", "Unknown"),
            coffee_price=data.get("coffee_price", "Unknown")
        )
        db.session.add(new_cafe)
        db.session.commit()
        return jsonify({"success": "Successfully added new cafe"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# [PATCH] 카페 업데이트 API
@app.route("/cafes/<int:cafe_id>/update-request", methods=["POST"])
@swag_from({
    "tags": ["Cafes"],
    "summary": "카페 정보 수정 요청",
    "description": "사용자가 카페 정보 수정 요청을 보낼 수 있습니다. (관리자 승인 필요)",
    "parameters": [
        {
            "name": "cafe_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "수정 요청할 카페의 ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "새로운 카페 이름"},
                    "location": {"type": "string", "example": "서울 종로구"},
                    "coffee_price": {"type": "string", "example": "₩5,000"},
                    "seats": {"type": "string", "example": "40석"},
                    "map_url": {"type": "string", "example": "https://maps.example.com/newcafe"},
                    "img_url": {"type": "string", "example": "https://images.example.com/newcafe.jpg"},
                    "has_toilet": {"type": "boolean", "example": True},
                    "has_wifi": {"type": "boolean", "example": True},
                    "has_sockets": {"type": "boolean", "example": False},
                    "can_take_calls": {"type": "boolean", "example": True}
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "수정 요청 성공",
            "examples": {
                "application/json": {"success": "Cafe update request submitted. Awaiting approval."}
            }
        },
        404: {
            "description": "카페 없음",
            "examples": {
                "application/json": {"error": "Cafe not found"}
            }
        }
    }
})
def request_cafe_update(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return jsonify({"error": "Cafe not found"}), 404

    data = request.get_json()
    new_request = UpdateRequest(
        cafe_id=cafe_id,
        proposed_name=data.get("name"),
        proposed_location=data.get("location"),
        proposed_coffee_price=data.get("coffee_price"),
        proposed_seats=data.get("seats"),
        proposed_map_url=data.get("map_url"),
        proposed_img_url=data.get("img_url"),
        proposed_has_toilet=data.get("has_toilet"),
        proposed_has_wifi=data.get("has_wifi"),
        proposed_has_sockets=data.get("has_sockets"),
        proposed_can_take_calls=data.get("can_take_calls"),
    )
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"success": "Cafe update request submitted. Awaiting approval."}), 201

# ─────────────────────────────────────────────
# 📌 7. 관리자 API (카페 수정 요청 관리, 승인, 거부, 삭제)
# ─────────────────────────────────────────────

# [GET] 모든 카페 목록 조회 API (관리자 전용 / 실제 배포시 공개할 필요가 없음)
@app.route("/admin/cafes", methods=["GET"])
@swag_from({
    "tags": ["Admin"],
    "summary": "모든 카페 목록 조회 (관리자 전용)",
    "description": "관리자 권한을 가진 사용자가 모든 카페를 조회할 수 있습니다.",
    "security": [{"BearerAuth": []}],
    "responses": {
        200: {
            "description": "카페 리스트 반환",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/Cafe"
                }
            }
        },
        403: {
            "description": "관리자 권한 없음"
        }
    }
})
def get_cafe_list():
    if not is_admin():
        abort(403, description="관리자 권한이 없습니다.")

    cafes = Cafe.query.all()
    return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200

# [DELETE] 카페 삭제 API (관련된 수정 요청도 삭제 /실제 배포시 공개할 필요가 없음)
@app.route("/cafes/<int:cafe_id>", methods=["DELETE"])
@swag_from({
    "tags": ["Admin"],
    "summary": "카페 삭제 (관리자 전용)",
    "description": "관리자가 특정 카페를 삭제할 수 있습니다. 해당 카페와 관련된 수정 요청도 함께 삭제됩니다.",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "cafe_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "삭제할 카페의 ID"
        }
    ],
    "responses": {
        200: {
            "description": "카페 삭제 성공",
            "examples": {
                "application/json": {"success": "Successfully removed cafe and related update requests."}
            }
        },
        403: {
            "description": "관리자 권한 없음",
            "examples": {
                "application/json": {"error": "관리자 권한이 없습니다."}
            }
        },
        404: {
            "description": "카페를 찾을 수 없음",
            "examples": {
                "application/json": {"error": "Cafe not found"}
            }
        }
    }
})
def remove_cafe(cafe_id):
    if not is_admin():
        abort(403, description="관리자 권한이 없습니다.")

    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return jsonify({"error": "Cafe not found"}), 404

    # 📌 해당 카페의 모든 수정 요청도 삭제
    UpdateRequest.query.filter_by(cafe_id=cafe_id).delete()

    db.session.delete(cafe)
    db.session.commit()

    return jsonify({"success": "Successfully removed cafe and related update requests."}), 200

# 관리자 승인 / 거부 기능 API (승인된 데이터 반환: 실제 배포시 공개할 필요가 없음)
@app.route("/admin/update-requests/<int:request_id>", methods=["PATCH"])
@swag_from({
    "tags": ["Admin"],
    "summary": "카페 수정 요청 승인/거부",
    "description": "관리자가 카페 수정 요청을 승인하거나 거부할 수 있습니다.",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "request_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "승인 또는 거부할 수정 요청 ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["approve", "reject"],
                        "description": "'approve' 또는 'reject' 값을 전달해야 합니다."
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "처리 완료"
        },
        403: {
            "description": "관리자 권한 없음"
        },
        404: {
            "description": "수정 요청을 찾을 수 없음"
        }
    }
})
def process_update_request(request_id):
    if not is_admin():
        abort(403, description="관리자 권한이 없습니다.")

    update_request = UpdateRequest.query.get(request_id)
    if not update_request:
        return jsonify({"error": "Request not found"}), 404

    data = request.get_json()
    action = data.get("action")  # "approve" 또는 "reject"

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action"}), 400

    updated_cafe = None  # 승인된 경우 반환할 카페 데이터

    if action == "approve":
        cafe = Cafe.query.get(update_request.cafe_id)
        if cafe:
            if update_request.proposed_name:
                cafe.name = update_request.proposed_name
            if update_request.proposed_location:
                cafe.location = update_request.proposed_location
            if update_request.proposed_coffee_price:
                cafe.coffee_price = update_request.proposed_coffee_price
            if update_request.proposed_seats:
                cafe.seats = update_request.proposed_seats
            if update_request.proposed_map_url:
                cafe.map_url = update_request.proposed_map_url
            if update_request.proposed_img_url:
                cafe.img_url = update_request.proposed_img_url
            if update_request.proposed_has_toilet is not None:
                cafe.has_toilet = update_request.proposed_has_toilet
            if update_request.proposed_has_wifi is not None:
                cafe.has_wifi = update_request.proposed_has_wifi
            if update_request.proposed_has_sockets is not None:
                cafe.has_sockets = update_request.proposed_has_sockets
            if update_request.proposed_can_take_calls is not None:
                cafe.can_take_calls = update_request.proposed_can_take_calls
            db.session.commit()
            updated_cafe = cafe_to_dict(cafe)

    update_request.status = "approved" if action == "approve" else "rejected"
    db.session.delete(update_request)
    db.session.commit()

    if action == "approve":
        return jsonify({"success": "Cafe update approved", "updated_cafe": updated_cafe}), 200
    else:
        return jsonify({"success": "Cafe update request rejected"}), 200


# 관리자 수정 요청 목록 조회 API (변경된 요청 목록 반환)
@app.route("/admin/update-requests", methods=["GET"])
@swag_from({
    "tags": ["Admin"],
    "summary": "카페 수정 요청 목록 조회",
    "description": "관리자가 현재 대기 중인 카페 수정 요청을 확인할 수 있습니다.",
    "security": [{"BearerAuth": []}],
    "responses": {
        200: {
            "description": "수정 요청 목록 반환",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "integer"},
                        "cafe_id": {"type": "integer"},
                        "proposed_name": {"type": "string"},
                        "proposed_location": {"type": "string"},
                        "proposed_coffee_price": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            }
        },
        403: {
            "description": "관리자 권한 없음"
        }
    }
})
def get_update_requests():
    if not is_admin():
        abort(403, description="관리자 권한이 없습니다.")

    requests = UpdateRequest.query.all()

    if not requests:
        return jsonify([]), 200

    results = []
    for req in requests:
        cafe = Cafe.query.get(req.cafe_id)
        if not cafe:
            continue

        results.append({
            "request_id": req.id,
            "cafe_id": req.cafe_id,
            "original_name": cafe.name,
            "proposed_name": req.proposed_name,
            "original_location": cafe.location,
            "proposed_location": req.proposed_location,
            "original_coffee_price": cafe.coffee_price,
            "proposed_coffee_price": req.proposed_coffee_price,
            "original_seats": cafe.seats,
            "proposed_seats": req.proposed_seats,
            "original_map_url": cafe.map_url,
            "proposed_map_url": req.proposed_map_url,
            "original_img_url": cafe.img_url,
            "proposed_img_url": req.proposed_img_url,
            "original_has_toilet": cafe.has_toilet,
            "proposed_has_toilet": req.proposed_has_toilet,
            "original_has_wifi": cafe.has_wifi,
            "proposed_has_wifi": req.proposed_has_wifi,
            "original_has_sockets": cafe.has_sockets,
            "proposed_has_sockets": req.proposed_has_sockets,
            "original_can_take_calls": cafe.can_take_calls,
            "proposed_can_take_calls": req.proposed_can_take_calls,
            "status": req.status,
            "created_at": req.created_at
        })

    return jsonify(results), 200

# 관리자 수정 요청 삭제 기능 추가 API
@app.route("/admin/update-requests/<int:request_id>", methods=["DELETE"])
@swag_from({
    "tags": ["Admin"],
    "summary": "카페 수정 요청 삭제",
    "description": "관리자가 특정 카페의 수정 요청을 삭제할 수 있습니다.",
    "security": [{"BearerAuth": []}],
    "parameters": [
        {
            "name": "request_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "삭제할 수정 요청의 ID"
        }
    ],
    "responses": {
        200: {
            "description": "수정 요청 삭제 성공",
            "examples": {
                "application/json": {"success": "수정 요청이 삭제되었습니다."}
            }
        },
        403: {
            "description": "관리자 권한 없음"
        },
        404: {
            "description": "수정 요청을 찾을 수 없음"
        }
    }
})
def delete_update_request(request_id):
    if not is_admin():
        abort(403, description="❌ 관리자 권한이 없습니다.")

    update_request = UpdateRequest.query.get(request_id)
    if not update_request:
        return jsonify({"error": "해당 수정 요청을 찾을 수 없습니다."}), 404

    db.session.delete(update_request)
    db.session.commit()

    return jsonify({"success": "수정 요청이 삭제되었습니다."}), 200

if __name__ == '__main__':
    app.run(debug=True)