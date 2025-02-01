import random
import os

import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean

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
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

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

# 홈 화면구성
@app.route("/")
def home():
    return render_template("index.html")

# 카페 검색 페이지
@app.route("/search")
def search_page():
    location = request.args.get("location")
    return render_template("search.html", location=location)


# 카페 추가 페이지
@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    if request.method == "POST":
        response = requests.post(url, data=request.form)
        return redirect(url_for("home"))
    return render_template("add.html")

# 카페 정보 수정페이지
@app.route("/update/<int:cafe_id>", methods=["GET", "POST"])
def update_price(cafe_id):
    if request.method == "POST":
        response = requests.patch(url, data=request.form)
        return redirect(url_for("home"))
    return render_template("update.html", cafe_id=cafe_id)

# HTTP GET - Read Record
@app.route("/random", methods=["GET"])
def get_random_cafe():
    ## 데이터 베이스에서 모든 데이터를 가져온다
    cafes = Cafe.query.all()
    ## 디버깅용
    print(cafes)
    ## 데이터가 존재하는 경우에만 임의의 카페를 가져온다.
    if cafes:
        random_cafe = random.choice(cafes)
        print(random_cafe)
        return jsonify(cafe_to_dict(random_cafe)), 200
    return jsonify({"error": "No cafes found"}), 400

@app.route("/all", methods=["GET"])
def get_all_cafes():
    cafes = Cafe.query.all()
    if cafes:
        return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
    return jsonify({"error": "No cafes found"}), 400

@app.route("/search", methods=["GET"])
def search_cafes_by_location():
    # URL 매개변수로 전달된 'location' 값 가져오기
    location = request.args.get("location")
    print(location)
    # 데이터베이스에서 location이 일치하는 모든 카페 찾기
    if location:
        cafes = Cafe.query.filter_by(location=location).all()
        if cafes:
            return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
        if cafes:
            return jsonify([cafe_to_dict(cafe) for cafe in cafes]), 200
        else:
            return jsonify({"error": f"No cafes found at location '{location}'"}), 404
    return jsonify({"error": "Location parameter is required"}), 400

# HTTP POST - Create Record
@app.route("/add", methods=['POST'])
def add_cafe():
    try:
        # 요청 데이터를 통해 새로운 카페 객체 생성
        new_cafe = Cafe(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            img_url=request.form.get("img_url"),
            location=request.form.get("location"),
            has_sockets=bool(int(request.form.get("has_sockets", 0))),  # 기본값 0
            has_wifi=bool(int(request.form.get("has_wifi", 0))),        # 기본값 0
            has_toilet=bool(int(request.form.get("has_toilet", 0))),    # 기본값 0
            can_take_calls=bool(int(request.form.get("can_take_calls", 0))),  # 기본값 0
            seats=request.form.get("seats", "Unknown"),  # 기본값 "Unknown"
            coffee_price=request.form.get("coffee_price", "Unknown")  # 기본값 "Unknown"
        )

        # 데이터베이스에 새 카페 추가
        db.session.add(new_cafe)
        db.session.commit()

        # 성공 메시지 반환
        return jsonify(response={"success": "Successfully added new cafe"}), 200

    except Exception as e:
        # 에러가 발생한 경우
        db.session.rollback()  # 데이터베이스 롤백
        return jsonify(response={"error": str(e)}), 500


# HTTP PUT/PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_cafe_price(cafe_id):
    # 새 가격 가져오기
    new_price = request.form.get("coffee_price")

    # coffee_price 값이 없으면 에러 반환
    if not new_price:
        return jsonify(response={"error": "No coffee price found in the request"}), 400

    try:
        # 데이터베이스에서 해당 카페 찾기
        cafe = Cafe.query.get(cafe_id)

        # 카페가 없으면 404 반환
        if not cafe:
            return jsonify(response={"error": "Cafe not found"}), 404

        # 커피 가격 업데이트
        cafe.coffee_price = new_price
        db.session.commit()  # 변경 사항 저장

        # 성공 메시지 반환
        return jsonify(response={"success": "Successfully updated coffee price"}), 200

    except Exception as e:
        # 예외 발생 시 롤백
        db.session.rollback()
        return jsonify(response={"error": str(e)}), 500

# HTTP DELETE - Delete Record
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def remove_cafe(cafe_id):
    # 요청에서 API_KEY 가져오기
    api_key = request.args.get("api-key")

    # API 키 검증
    if api_key != "TopSecretAPIKey":
        return jsonify(response={"error": "Invalid API key"}), 403

    try:
        # 데이터베이스에서 해당 카페 찾기
        cafe = Cafe.query.get(cafe_id)
        # 카페가 존재하지 않는 경우
        if not cafe:
            return jsonify(response={"error": "Cafe not found"}), 404
        # 카페 삭제
        db.session.delete(cafe)
        db.session.commit()
        # 성공메세지 반환
        return jsonify(response={"success": "Successfully removed cafe"}), 200
    except Exception as e:
        # 예외 발생시 롤백
        db.session.rollback()
        return jsonify(response={"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
