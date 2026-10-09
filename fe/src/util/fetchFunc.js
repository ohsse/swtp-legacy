/**
 * API 요청을 보내는 범용 fetch 함수
 * @param {string} url - 요청을 보낼 URL
 * @param {object} [data=null] - 요청 본문에 포함할 데이터 (POST, PUT 등)
 * @param {string} [method=''] - HTTP 메소드 ('GET', 'POST', 'PUT', 'DELETE' 등)
 * @returns {Promise<any>} - fetch 요청의 JSON 응답
 */
export async function fetchFunc(url, data = null, method = "") {
  const chkUrl = url.split("/").pop(); // URL 마지막 부분 추출
  const token = localStorage.getItem("token"); // localStorage에서 토큰 가져오기

  // method가 명시적으로 주어지면 해당 값을 사용, 아니면 기존 방식으로 결정
  const httpMethod = method || (data ? "POST" : "GET");

  let options = {
    method: httpMethod,
    headers: {
      "Content-Type": "application/json",
    },
  };

  // 특정 URL인 'rstSavingTargetSum'이고 토큰이 있을 때만 Authorization 헤더 추가
  if (chkUrl === "rstSavingTargetSum" && token) {
    options.headers["Authorization"] = `Bearer ${token}`;
  }

  // data가 있으면 요청 본문에 JSON 형태로 추가
  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const res = await fetch(url, options);

    // 응답 상태가 정상이 아닐 경우 에러 처리
    if (!res.ok) {
      // 본문의 message 를 먼저 살린다. 서버(epa)는 실패 시에도 JSON 으로
      // {code, message, data} 를 주는데(epa/app/utils/response.py 의 api_error),
      // 여기서 본문을 안 읽으면 "관망해석 엔진이 사용 중입니다" 같은 안내가 전부
      // "HTTP error! status: 503" 으로 뭉개진다.
      // 반환 형태({error, message})는 그대로라 기존 호출부는 영향받지 않는다.
      let serverMessage = "";
      try {
        const errBody = await res.json();
        serverMessage = errBody?.message || "";
      } catch {
        // JSON 이 아닌 응답(프록시 오류 페이지 등)이면 상태코드만 쓴다.
      }
      throw new Error(serverMessage || `HTTP error! status: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error("Fetch API Error:", error);
    // 에러 발생 시 일관된 에러 객체를 반환하거나, null을 반환하여
    // 호출한 쪽에서 에러를 처리할 수 있도록 함
    return { error: true, message: error.message };
  }
}
