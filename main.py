import random
import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request, render_template, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from datetime import datetime
from flask_migrate import Migrate

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
@app.route("/admin/cafes")
def admin_cafes_page():
    if not is_admin():
        return redirect(url_for("login_page"))  # 관리자 권한 없으면 로그인 페이지로 리디렉트
    return render_template("admin_cafes.html")

# ─────────────────────────────────────────────
# 📌 6. 카페 API (조회, 추가, 검색, 삭제)
# ─────────────────────────────────────────────

# [GET] 모든 카페 조회
@app.route("/cafes", methods=["GET"])
def get_all_cafes():
    cafes = Cafe.query.all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": "No cafes found"}), 404

# [GET] 랜덤 카페 반환
@app.route("/cafes/random", methods=["GET"])
def get_random_cafe():
    cafes = Cafe.query.all()
    if not cafes:  # 빈 리스트일 경우 바로 404 반환
        return jsonify({"error": "No cafes found"}), 404

    random_cafe = random.choice(cafes)
    return jsonify(cafe_to_dict(random_cafe)), 200

# [GET] 위치 기반 카페 검색
@app.route("/cafes/location/<string:location>", methods=["GET"])
def search_cafes_by_location(location):
    cafes = Cafe.query.filter(Cafe.location.ilike(f"%{location}%")).all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": f"No cafes found at location '{location}'"}), 404

# [POST] 새로운 카페 추가 (JSON 데이터 받아 처리)
@app.route("/cafes", methods=["POST"])
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

# [PATCH] 카페 업데이트
@app.route("/cafes/<int:cafe_id>/update-request", methods=["POST"])
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

# [GET] 모든 카페 목록 조회 (관리자 전용)
@app.route("/admin/cafes", methods=["GET"])
def get_cafe_list():
    if not is_admin():
        abort(403, description="관리자 권한이 없습니다.")

    cafes = Cafe.query.all()
    return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200

# [DELETE] 카페 삭제 (관련된 수정 요청도 삭제)
@app.route("/cafes/<int:cafe_id>", methods=["DELETE"])
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

# 관리자 승인 / 거부 기능 (승인된 데이터 반환)
@app.route("/admin/update-requests/<int:request_id>", methods=["PATCH"])
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


# 관리자 수정 요청 목록 조회 (변경된 요청 목록 반환)
@app.route("/admin/update-requests", methods=["GET"])
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

# 관리자 수정 요청 삭제 기능 추가
@app.route("/admin/update-requests/<int:request_id>", methods=["DELETE"])
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