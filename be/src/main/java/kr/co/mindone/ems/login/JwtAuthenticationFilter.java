package kr.co.mindone.ems.login;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenProvider tokenProvider;

    // LoginService를 직접 사용 (CustomUserDetailsService는 더 이상 사용하지 않음)
    @Autowired
    private LoginService loginService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        //System.out.println("JwtAuthenticationFilter invoked");
        try {
            // 요청 헤더에서 JWT 토큰 추출 ("Bearer " 접두어 제거)
            String jwt = getJwtFromRequest(request);
            //System.out.println("doFilterInternal jwt: "+jwt );
            if (StringUtils.hasText(jwt) && tokenProvider.validateToken(jwt)) {
                // JWT에서 사용자 ID(문자열) 추출
                String userId = tokenProvider.getUserIdFromJWT(jwt);
                //System.out.println("doFilterInternal userId: "+userId+" / "+jwt.length() );
                // LoginService를 통해 사용자 정보를 조회 (loadUserById 메서드를 이용)
                UserDetails userDetails = loginService.loadUserById(userId);
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                // SecurityContext에 인증 객체 등록
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (Exception ex) {
            // 필요에 따라 로깅하거나 예외 처리를 진행하세요.
            ex.printStackTrace();
        }
        filterChain.doFilter(request, response);
    }

    // Authorization 헤더에서 "Bearer " 접두어가 있는 JWT 토큰 추출
    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}


