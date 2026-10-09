package kr.co.mindone.ems.login;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import kr.co.mindone.ems.config.response.ResponseObject;
import kr.co.mindone.ems.login.dto.JwtAuthenticationResponse;
import kr.co.mindone.ems.login.dto.LoginRequest;
import kr.co.mindone.ems.login.dto.User;
import kr.co.mindone.ems.login.dto.UserPrincipal;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.*;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@RestController
@RequestMapping("/login")
public class LoginController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired LoginService loginService;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    @GetMapping("/checkTkn")
    public ResponseEntity<?> authenticateByToken(@RequestParam HashMap<String, String> map) {
        try {
            // 1. 클라이언트로부터 tkn 값 받아오기
            String receivedToken = map.get("tkn");
            HashMap<String, Object> tknItem = new HashMap<>();
            tknItem.put("old_tkn",receivedToken);

            // 2. DB에서 토큰 정보를 조회하여 사용자 정보를 가져옴
            HashMap<String, Object> lgUser = loginService.getUserTokenOnly(receivedToken);

            // lgUser가 null이면 토큰 페이로드에서 사용자 정보를 가져옴
            if (lgUser == null) {
                Map<String, Object> tknMap = tokenMap(receivedToken);
                if (tknMap != null) {
                    // 토큰 페이로드의 'sub'를 이용해 DB에서 User 객체를 찾음
                    User user = loginService.findUserById(tknMap.get("sub").toString());
                    if (user == null) {
                        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                                .body("유효하지 않은 토큰입니다.");
                    }

                    // 권한 정보 추출
                    List<GrantedAuthority> authorities = new ArrayList<>();
                    String roles = user.getUsrAuth().toString();
                    authorities.add(new SimpleGrantedAuthority(roles));

                    // User 객체의 정보로 UserPrincipal 생성 (NullPointerException 수정)
                    UserPrincipal userPrincipal = new UserPrincipal(
                            user.getUsrId(),
                            user.getUsrNm(),
                            user.getUsrPw(),
                            authorities,
                            user.getUsrNm(),
                            user.getUsrPn(),
                            user.getUsrTi()
                    );

                    // Authentication 객체 생성 및 SecurityContext에 등록
                    Authentication authentication = new UsernamePasswordAuthenticationToken(
                            userPrincipal, null, userPrincipal.getAuthorities()
                    );
                    SecurityContextHolder.getContext().setAuthentication(authentication);

                    // 새로운 JWT 토큰 생성
                    String newJwt = tokenProvider.generateToken(authentication);
                    return ResponseEntity.ok(new JwtAuthenticationResponse(newJwt));
                } else {
                    return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                            .body("유효하지 않은 토큰입니다.");
                }
            }
            // lgUser가 null이 아닐 경우 (기존 로직)
            else {
                // DB에 저장된 정보로 사용자 권한 가져오기
                List<GrantedAuthority> authorities = new ArrayList<>();
                String roles = lgUser.get("USR_AUTH").toString();
                authorities.add(new SimpleGrantedAuthority(roles));

                // 검증된 lgUser 정보를 이용해 UserPrincipal 생성
                UserPrincipal userPrincipal = new UserPrincipal(
                        lgUser.get("USR_ID").toString(),
                        lgUser.get("USR_NM").toString(),
                        lgUser.get("USR_PW").toString(),
                        authorities,
                        lgUser.get("USR_NM").toString(),
                        lgUser.get("USR_PN").toString(),
                        (Integer) lgUser.get("USR_TI")
                );

                // Authentication 객체 생성 및 SecurityContext에 등록
                Authentication authentication = new UsernamePasswordAuthenticationToken(
                        userPrincipal, null, userPrincipal.getAuthorities()
                );
                SecurityContextHolder.getContext().setAuthentication(authentication);

                // 재발급 JWT 토큰 생성
                String jwt = tokenProvider.generateToken(authentication);

                // AI Status 업데이트 로직 (기존과 동일)
                if(!wpp_code.equals("ss")){
                    try{
                        int serverNo = loginService.getServerNo();
                        if(serverNo == 1) {
                            updateAiStatus(2, "2","1");
                        } else if (serverNo == 2) {
                            updateAiStatus(1, "2","1");
                        } else {
                            updateAiStatus(1, "2","1");
                            updateAiStatus(2, "2","1");
                        }
                    }
                    catch (Exception e)
                    {
                        e.printStackTrace();
                    }
                }

                // JWT 토큰을 응답으로 반환
                return ResponseEntity.ok(new JwtAuthenticationResponse(jwt));
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    .body(e.getMessage());
        }
    }

    @GetMapping("/refreshTkn")
    public ResponseEntity<?> refreshToken(@RequestParam HashMap<String, String> rmap) {
        try {
            String receivedToken = rmap.get("tkn");
            //System.out.println("Received token: " + receivedToken);
            HashMap<String, Object> tknItem = new HashMap<>();
            tknItem.put("old_tkn",receivedToken);

            // 토큰을 "dot(.)"으로 분할 (헤더, 페이로드, 서명)
            String[] parts = receivedToken.split("\\.");
            if (parts.length != 3) {
                //System.out.println("잘못된 JWT 토큰 형식입니다."+parts.length);
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body("유효하지 않은 토큰입니다.");
            }
            String payload = new String(Base64.getUrlDecoder().decode(parts[1]));

            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> map = mapper.readValue(payload, HashMap.class);

            // "user_auth" 필드 처리: role 값이 "false"이면 0, "true"이면 1로 변환
            if (map.containsKey("user_auth")) {
                Object userAuthObj = map.get("user_auth");
                if (userAuthObj instanceof List) {
                    List<?> userAuthList = (List<?>) userAuthObj;
                    if (!userAuthList.isEmpty()) {
                        Object first = userAuthList.get(0);
                        if (first instanceof Map) {
                            Map<String, Object> roleMap = (Map<String, Object>) first;
                            Object roleValue = roleMap.get("role");
                            if (roleValue != null && roleValue instanceof String) {
                                String roleStr = ((String) roleValue).trim();
                                int converted = roleStr.equalsIgnoreCase("true") ? 1 : 0;
                                // user_auth 필드를 변환된 정수값으로 대체
                                map.put("user_auth", converted);
                            }
                        }
                    }
                }
            }

            //System.out.println("#map:"+map.toString());

            User user =   loginService.findUserById(map.get("sub").toString());

            // 1. 전달받은 토큰을 기반으로 DB에서 사용자 정보를 조회
            //HashMap<String, Object> lgUser = loginService.getUserTokenOnly(receivedToken);
            if (user == null) {
                // 토큰이 DB에 없거나 유효하지 않으면 401 반환
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                                     .body("유효하지 않은 토큰입니다.");
            }
            //System.out.println("lgUser: " + user.getUsrAuth());

            // 2. DB의 사용자 정보에서 권한 정보를 추출 (권한이 여러 개라면 콤마로 분리 가능)
            List<GrantedAuthority> authorities = new ArrayList<>();
            String roles = user.getUsrAuth().toString();
            // 단일 권한으로 처리
            authorities.add(new SimpleGrantedAuthority(roles));

            // 3. UserPrincipal 객체 생성 (필요한 경우 DB의 사용자 정보에서 추가 데이터도 설정)
            UserPrincipal userPrincipal = new UserPrincipal(
                    user.getUsrId(),   // id
                    user.getUsrNm(),   // username
                    user.getUsrPw(),   // password
                    authorities,       // authorities
                    user.getUsrNm(),   // usrNm 추가
                    user.getUsrPn(),   // usrPn 추가
                    user.getUsrTi()    // usrTi 추가
            );

            // 4. Authentication 객체 생성 후 SecurityContext에 등록
            Authentication authentication = new UsernamePasswordAuthenticationToken(
                    userPrincipal, null, userPrincipal.getAuthorities()
            );
            SecurityContextHolder.getContext().setAuthentication(authentication);

            // 5. 새로운 JWT 토큰 생성 (예: 만료시간 연장)
            String newJwt = tokenProvider.generateToken(authentication);
//            Date newExpiry = tokenProvider.getExpirationDateFromJWT(newJwt);
//            tknItem.put("tkn",newJwt);
//            tknItem.put("expr_ti", newExpiry);
//            loginService.updateToken(tknItem);

            //System.out.println("refreshTkn NEW JWT update: " + newJwt);
            // 6. 새 토큰을 응답으로 반환
            return ResponseEntity.ok(new JwtAuthenticationResponse(newJwt));
        }catch (Exception e)
        {
            return ResponseEntity.status(HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                                                         .body(e.getMessage());
        }
    }


    private static final RestTemplate restTemplate = new RestTemplate();

    public void updateAiStatus(int server, String status, String pumpGrp) {
        // 요청 데이터를 구성 (STATUS, PUMP_GRP)
        HashMap<String, Object> requestData = new HashMap<>();
        requestData.put("STATUS", status);
        requestData.put("PUMP_GRP", pumpGrp);
        String UPDATE_AI_STATUS_URL = "";
        String url = "";
        String url1 = "";
        String url2 = "";
        if(wpp_code.equals("gs")){
            url = "localhost";
            url1 = "localhost";
            url2 = "localhost";
        }else if(wpp_code.equals("gu")){
            url = "localhost";
            url1 = "localhost";
            url2 = "localhost";
        }else if(wpp_code.equals("ba")){
            url = "localhost";
            url1 = "localhost";
            url2 = "localhost";
        }
        if(server == 1)
        {
            UPDATE_AI_STATUS_URL = "http://"+ url1 +":10013/updateAiStatus";
        }
        else if(server == 2)
        {
            UPDATE_AI_STATUS_URL = "http://"+ url2 +":10013/updateAiStatus";
        }
        else {
            UPDATE_AI_STATUS_URL = "http://"+ url +":10013/updateAiStatus";
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<HashMap<String, Object>> requestEntity = new HttpEntity<>(requestData, headers);

        //System.out.println("UPDATE_AI_STATUS_URL: "+UPDATE_AI_STATUS_URL);
        // POST 요청을 보내고 응답 받기
        /*ResponseObject<String> response = restTemplate.postForObject(
            UPDATE_AI_STATUS_URL,
            requestEntity,
            ResponseObject.class
        );*/
    }

    public Map<String , Object> tokenMap (String receivedToken)
    {
        // 토큰을 "dot(.)"으로 분할 (헤더, 페이로드, 서명)
        String[] parts = receivedToken.split("\\.");
        if (parts.length != 3) {
            //System.out.println("잘못된 JWT 토큰 형식입니다."+parts.length);
            return null;
        }
        String payload = new String(Base64.getUrlDecoder().decode(parts[1]));
        try
        {
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> map = mapper.readValue(payload, HashMap.class);

            // "user_auth" 필드 처리: role 값이 "false"이면 0, "true"이면 1로 변환
            if (map.containsKey("user_auth")) {
                Object userAuthObj = map.get("user_auth");
                if (userAuthObj instanceof List) {
                    List<?> userAuthList = (List<?>) userAuthObj;
                    if (!userAuthList.isEmpty()) {
                        Object first = userAuthList.get(0);
                        if (first instanceof Map) {
                            Map<String, Object> roleMap = (Map<String, Object>) first;
                            Object roleValue = roleMap.get("role");
                            if (roleValue != null && roleValue instanceof String) {
                                String roleStr = ((String) roleValue).trim();
                                int converted = roleStr.equalsIgnoreCase("true") ? 1 : 0;
                                // user_auth 필드를 변환된 정수값으로 대체
                                map.put("user_auth", converted);
                            }
                        }
                    }
                }
            }
            //System.out.println("#map:"+map.toString());
            return map;
        }catch (Exception e){
            return null;
        }
    }


}
