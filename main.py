import random
import os

from flask import Flask, jsonify, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from datetime import datetime

app = Flask(__name__)

print("Database file path:", os.path.abspath("cafes.db"))

# CREATE DB
class Base(DeclarativeBase):
    pass

# Connect to Database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "cafes.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_ECHO'] = True  # SQLAlchemy 쿼리 로그 활성화
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
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

# 📌 카페 수정 요청 테이블
class UpdateRequest(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cafe_id: Mapped[int] = mapped_column(Integer, nullable=False)
    proposed_name: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_location: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)
    proposed_seats: Mapped[str] = mapped_column(String(250), nullable=True)
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

# 📌 ✅ [GET] 홈페이지(index.html) 제공
@app.route("/")
def home():
    return render_template("index.html")

# 📌 [GET] 카페 추가 페이지
@app.route("/add")
def add_cafe_page():
    return render_template("add.html")  # add.html 렌더링

# 📌 [GET] 커피 가격 업데이트 페이지
@app.route("/update")
def update_cafe_page():
    return render_template("update.html")  # update.html 렌더링

# 📌 [GET] 모든 카페 조회
@app.route("/cafes", methods=["GET"])
def get_all_cafes():
    cafes = Cafe.query.all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": "No cafes found"}), 404

# 📌 [GET] 랜덤 카페 반환
@app.route("/cafes/random", methods=["GET"])
def get_random_cafe():
    cafes = Cafe.query.all()
    if not cafes:  # 빈 리스트일 경우 바로 404 반환
        return jsonify({"error": "No cafes found"}), 404

    random_cafe = random.choice(cafes)
    return jsonify(cafe_to_dict(random_cafe)), 200

# 📌 [GET] 위치 기반 카페 검색
@app.route("/cafes/location/<string:location>", methods=["GET"])
def search_cafes_by_location(location):
    # cafes = Cafe.query.filter_by(location=location).all()
    cafes = Cafe.query.filter(Cafe.location.ilike(f"%{location}%")).all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": f"No cafes found at location '{location}'"}), 404

# 📌 [POST] 새로운 카페 추가 (JSON 데이터 받아 처리)
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

# 📌 [PATCH] 카페 업데이트
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
        proposed_has_toilet=data.get("has_toilet"),
        proposed_has_wifi=data.get("has_wifi"),
        proposed_has_sockets=data.get("has_sockets"),
        proposed_can_take_calls=data.get("can_take_calls"),
    )
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"success": "Cafe update request submitted. Awaiting approval."}), 201

# 📌 [DELETE] 카페 삭제 (API Key 필요)
@app.route("/cafes/<int:cafe_id>", methods=["DELETE"])
def remove_cafe(cafe_id):
    # API 키를 Authorization 헤더에서 받음
    api_key = request.headers.get("Authorization")

    # 올바른 키가 아니면 403 Forbidden
    if api_key != "Bearer TopSecretAPIKey":
        abort(403, description="Invalid API key")

    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return jsonify({"error": "Cafe not found"}), 404

    db.session.delete(cafe)
    db.session.commit()
    return jsonify({"success": "Successfully removed cafe"}), 200

# 관리자용 수정 요청 승인 거절 라우터
@app.route("/admin/update-requests", methods=["GET"])
def get_update_requests():
    api_key = request.headers.get("Authorization")
    if api_key != "Bearer TopSecretAdminKey":
        abort(403, description="Invalid API key")

    requests = UpdateRequest.query.all()
    return jsonify([{
        "request_id": req.id,
        "cafe_id": req.cafe_id,
        "proposed_name": req.proposed_name,
        "proposed_location": req.proposed_location,
        "proposed_coffee_price": req.proposed_coffee_price,
        "proposed_seats": req.proposed_seats,
        "proposed_has_toilet": req.proposed_has_toilet,
        "proposed_has_wifi": req.proposed_has_wifi,
        "proposed_has_sockets": req.proposed_has_sockets,
        "proposed_can_take_calls": req.proposed_can_take_calls,
        "status": req.status,
        "created_at": req.created_at
    } for req in requests]), 200

# 관리자용 승인/거부
@app.route("/admin/update-requests/<int:request_id>", methods=["PATCH"])
def process_update_request(request_id):
    api_key = request.headers.get("Authorization")
    if api_key != "Bearer TopSecretAdminKey":
        abort(403, description="Invalid API key")

    update_request = UpdateRequest.query.get(request_id)
    if not update_request:
        return jsonify({"error": "Request not found"}), 404

    data = request.get_json()
    action = data.get("action")  # "approve" 또는 "reject"

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action"}), 400

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
            if update_request.proposed_has_toilet is not None:
                cafe.has_toilet = update_request.proposed_has_toilet
            if update_request.proposed_has_wifi is not None:
                cafe.has_wifi = update_request.proposed_has_wifi
            if update_request.proposed_has_sockets is not None:
                cafe.has_sockets = update_request.proposed_has_sockets
            if update_request.proposed_can_take_calls is not None:
                cafe.can_take_calls = update_request.proposed_can_take_calls
            db.session.commit()

    update_request.status = "approved" if action == "approve" else "rejected"
    db.session.delete(update_request)
    db.session.commit()

    return jsonify({"success": f"Cafe update request {action}d successfully."}), 200


if __name__ == '__main__':
    app.run(debug=True)