package kr.co.mindone.ems.login.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class LoginRequest {
    private String username;
    private String password;
    private String tkn;

    // Getter, Setter, 기본 생성자
    public LoginRequest() {
    }

}