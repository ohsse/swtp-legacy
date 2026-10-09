/**
 * 실수를 받아 정수의 3번째 자리마다 ,를 찍고 반환 하는 함수
 * @param {Float} number
 * @returns
 */
export function addCommaNumber(number) {
  // 문자열인 경우 숫자로 변환, 타입 변환 후 NaN인 경우 0으로 처리
  const parsedNumber = parseFloat(number);
  if (isNaN(parsedNumber)) {
    return 0;
  }

  // 0인 경우 0을 반환
  if (parsedNumber === 0) {
    return 0;
  }

  // 소수점 아래 2자리까지 반올림하여 표기
  const roundedNumber = Math.round(parsedNumber * 100) / 100;

  // 3자리마다 콤마 추가
  const parts = roundedNumber.toString().split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  return parts.join(".");
}
