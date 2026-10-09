package kr.co.mindone.ems.login;
import kr.co.mindone.ems.login.dto.User;
import kr.co.mindone.ems.login.dto.UserPrincipal;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.stereotype.Service;

import java.util.HashMap;

@Service
public class LoginService implements UserDetailsService {

    @Autowired
    LoginMapper loginMapper;

    // 사용자 이름으로 User 엔티티 조회
    public User findUserByUsername(String username) {
        // TODO: 실제 DB 조회 로직 구현 (예: JPA Repository, MyBatis 등)
        // 예: return userRepository.findByUsername(username).orElse(null);
        return null;
    }

    public void updateToken(HashMap<String,Object> item)
    {
        loginMapper.updateToken(item);
    }

    public HashMap<String, Object> getUserToken(String tkn) {
       // TODO: 실제 DB 조회 로직 구현 (예: JPA Repository, MyBatis 등)
        return loginMapper.getUserToken(tkn);
   }

    public HashMap<String, Object> getUserTokenOnly(String tkn) {
       // TODO: 실제 DB 조회 로직 구현 (예: JPA Repository, MyBatis 등)
        return loginMapper.getUserTokenOnly(tkn);
   }

    // 사용자 ID(문자열)로 User 엔티티 조회
    public User findUserById(String id) {

        // TODO: 실제 DB 조회 로직 구현 (예: JPA Repository, MyBatis 등)
        // 예: return userRepository.findById(id).orElse(null);
        HashMap<String, Object> item = loginMapper.findUserId(id);
        User user = new User();
        user.setUsrId(item.get("USR_ID").toString());
        user.setUsrNm(item.get("USR_NM").toString());
        user.setUsrPw(item.get("USR_PW").toString());
        user.setUsrPn(item.get("USR_PN").toString());
        user.setUsrTi(Integer.parseInt(item.get("USR_TI").toString()));
        if(item.get("USR_AUTH").toString().equals("false") || item.get("USR_AUTH").toString().equals("0"))
        {
            user.setUsrAuth(0);
        }
        else {
            user.setUsrAuth(1);
        }

        return user;
    }

    // UserDetailsService 인터페이스 메서드: username으로 사용자 인증 정보 반환
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = findUserByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("User not found with username: " + username);
        }
        return UserPrincipal.create(user);
    }

    // 추가 메서드: JWT 토큰 등에서 사용자 ID로 UserDetails 조회 시 사용
    public UserDetails loadUserById(String id) {
        User user = findUserById(id);
        if (user == null) {
            throw new UsernameNotFoundException("User not found with id: " + id);
        }
        return UserPrincipal.create(user);
    }

    public int getServerNo()
    {
        int serverNo = 0;
        HashMap<String,Object> item = loginMapper.getServerNo();

        if(item.get("value") != null)
        {
            serverNo = Integer.parseInt(item.get("value").toString());
        }

        return serverNo;
    }
}

