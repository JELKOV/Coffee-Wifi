document.addEventListener("DOMContentLoaded", function () {
    fetchCafes(); // ✅ 초기 페이지 로드 시 전체 목록 가져오기
    document.getElementById("random-cafe-btn").addEventListener("click", fetchRandomCafe);
    document.getElementById("search-form").addEventListener("submit", searchCafes);
});

// 📌 [GET] 모든 카페 목록 가져오기 (초기 로딩용)
async function fetchCafes() {
    try {
        const response = await fetch("/cafes");
        if (!response.ok) throw new Error("카페 목록을 불러오는 중 오류 발생");

        const cafes = await response.json();
        const cafeList = document.getElementById("cafe-list");

        // ✅ 기존 리스트 초기화 후 새로운 데이터 추가
        cafeList.innerHTML = generateCafeCards(cafes);
    } catch (error) {
        document.getElementById("cafe-list").innerHTML = `<p style="color: red;">${error.message}</p>`;
    }
}

// 📌 [GET] 특정 지역 카페 검색 (검색 실행 시 전체 리스트를 지우고 검색 결과만 표시)
async function searchCafes(event) {
    event.preventDefault(); // 기본 폼 제출 동작 방지

    const location = document.getElementById("search-input").value.trim();
    if (!location) {
        alert("검색할 지역을 입력하세요!");
        return;
    }

    try {
        const response = await fetch(`/cafes/location/${encodeURIComponent(location.toLowerCase())}`);

        if (response.status === 404) {  // 서버에서 404 반환 시 직접 처리
            document.getElementById("cafe-list").innerHTML = `<p style="color: gray;">검색 결과가 없습니다.</p>`;
            return;
        }

        if (!response.ok) throw new Error("검색 요청 실패");

        const cafes = await response.json();
        const cafeList = document.getElementById("cafe-list");

        // ✅ 기존 리스트 초기화 후 검색된 결과만 표시
        cafeList.innerHTML = "";

        if (!cafes || cafes.length === 0) { // 응답 데이터가 빈 배열일 경우
            cafeList.innerHTML = `<p style="color: gray;">검색 결과가 없습니다.</p>`;
            return;
        }

        // ✅ 검색 결과를 동일한 카드 UI로 추가
        cafeList.innerHTML = generateCafeCards(cafes);

    } catch (error) {
        document.getElementById("cafe-list").innerHTML = `<p style="color: red;">검색 중 오류 발생: ${error.message}</p>`;
    }
}

// 📌 [GET] 랜덤 카페 추천 (버튼이 사라진 문제 해결)
async function fetchRandomCafe() {
    try {
        const response = await fetch("/cafes/random");
        if (!response.ok) throw new Error("랜덤 카페를 불러올 수 없습니다.");

        const cafe = await response.json();
        alert(`🎲 추천 카페: ${cafe.name} - ${cafe.location}`);
    } catch (error) {
        alert(`⚠️ 오류 발생: ${error.message}`);
    }
}

// ✅ 🔧 공통 UI 생성 함수 (검색 & 전체 리스트에 동일한 카드 적용)
function generateCafeCards(cafes) {
    return cafes.map(cafe => `
        <div class="cafe-card">
            <h3><a href="/cafe/${cafe.id}">${cafe.name}</a></h3>
            <a href="/cafe/${cafe.id}"><img src="${cafe.img_url}" alt="${cafe.name}" width="100%"></a>
            <p>📍 위치: ${cafe.location}</p>
            <p>💰 커피 가격: ${cafe.coffee_price ? cafe.coffee_price : "정보 없음"}</p>
            <a href="${cafe.map_url}" target="_blank">📍 지도 보기</a>
        </div>
    `).join("");
}

