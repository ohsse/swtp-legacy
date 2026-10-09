const getStartDate = (state) => {
    let str = state.userInfo.reservationStartDt;
    let startTime = new Date(
        str.slice(0, 4),
        Number(str.slice(4, 6)) - 1,
        str.slice(6, 8),
        str.slice(8, 10),
        str.slice(10, 12)
    );

    let day = startTime.getDay();
    let dayStr = '';
    if (day === 0) dayStr = '일요일';
    if (day === 1) dayStr = '월요일';
    if (day === 2) dayStr = '화요일';
    if (day === 3) dayStr = '수요일';
    if (day === 4) dayStr = '목요일';
    if (day === 5) dayStr = '금요일';
    if (day === 6) dayStr = '토요일';

    let returnStr =
        startTime.getFullYear() +
        '년 ' +
        (startTime.getMonth() + 1) +
        '월 ' +
        startTime.getDate() +
        '일 ' +
        dayStr +
        ' ' +
        startTime.getHours() +
        '시' +
        (startTime.getMinutes() === 0
            ? ''
            : ' ' + startTime.getMinutes() + '분');
    return returnStr;
};

export { getStartDate };
