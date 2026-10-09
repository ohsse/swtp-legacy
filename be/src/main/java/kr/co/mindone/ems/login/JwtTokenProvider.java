package kr.co.mindone.ems.login;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import kr.co.mindone.ems.login.dto.User;
import kr.co.mindone.ems.login.dto.UserPrincipal;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import java.security.Key;
import java.util.Date;

@Component
public class JwtTokenProvider {

    // 최소 64자 이상의 문자열: 64 bytes = 512 bits (HS512 요구사항 충족)
    private final String JWT_SECRET = "local-dev-only-secret-change-me-0123456789-local-dev-only-secret";
    // 토큰 유효시간 (예: 1시간)
    //public final long JWT_EXPIRATION_MS = 3600000; //60분
    public final long JWT_EXPIRATION_MS = 31536000000L; // 1년

    @Autowired
    public LoginService loginService;

    // JWT_SECRET을 기반으로 Key 객체를 한 번만 생성하여 재사용
    private final Key key = Keys.hmacShaKeyFor(JWT_SECRET.getBytes());

    public String generateToken(Authentication authentication) {
        UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();

        User user = loginService.findUserById(userPrincipal.getId());
        long JWT_EXPIRATION = 3600000; //기본 30분
        if(user.getUsrAuth() == 0 )
        {
            JWT_EXPIRATION = JWT_EXPIRATION_MS;
        }
        else {
            JWT_EXPIRATION = user.getUsrTi() * 60 * 1000L;
        }


        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + JWT_EXPIRATION);



        return Jwts.builder()
                .setSubject(userPrincipal.getId())
                .claim("user_auth", userPrincipal.getAuthorities())
                .claim("usrNm", userPrincipal.getUsrNm())
                .claim("usrPn", userPrincipal.getUsrPn())
                .claim("usrTi", userPrincipal.getUsrTi())
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(key, SignatureAlgorithm.HS512)
                .compact();
    }

    // JWT 토큰에서 사용자 ID(문자열)를 추출
    public String getUserIdFromJWT(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.getSubject();
    }

    public Claims getClaimsFromJWT(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(key) // 이미 JwtTokenProvider 내부에서 재사용되는 Key 객체
                .build()
                .parseClaimsJws(token)
                .getBody();
    }


    // JWT 토큰 유효성 검증
    public boolean validateToken(String authToken) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(authToken);
            return true;
        } catch (JwtException | IllegalArgumentException ex) {
            // 필요에 따라 로깅 처리
            System.err.println("Invalid JWT token: " + ex.getMessage());
        }
        return false;
    }

    // 토큰 만료일 반환
    public Date getExpirationDateFromJWT(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.getExpiration();
    }
}
