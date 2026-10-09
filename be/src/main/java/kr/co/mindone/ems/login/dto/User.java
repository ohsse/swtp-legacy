package kr.co.mindone.ems.login.dto;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Setter
public class User {

    private String usrId;

    private String usrPw;

    private String usrNm;

    private String usrPn;

    private Integer usrAuth; // 필요한 경우 Boolean 또는 Enum 등으로 변경 가능

    private Integer usrTi;

    // 기본 생성자
    public User() {}


}


