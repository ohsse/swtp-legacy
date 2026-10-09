/**
 * 태그정보에 검색쪽에 사용되는 문자열 replace 함수
 * @param {@event } inputElement 
 */
export function replace(inputElement) {
    const replaceKeyword = /[!@#$%^&*+=[\]{};:'"|<.>?~`]/g;
    const value = inputElement.value;
    const newValue = value.replace(replaceKeyword, "");
    inputElement.value = newValue;
}

export function notNumReplace(inputElement) {
    const replacePattern = /[^0-9]+/g; // 0 이상의 정수가 아닌 모든 문자를 대체
    const value = inputElement.value;
    const newValue = value.replace(replacePattern, "");
    inputElement.value = newValue;
}