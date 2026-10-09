package kr.co.mindone.ems.login.dto;

import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

@Getter // 모든 필드에 대한 getter를 자동으로 생성
public class UserPrincipal implements UserDetails {

    private final String id;
    private final String username;
    private final String password;
    private final Collection<? extends GrantedAuthority> authorities;
    private final String usrNm;
    private final String usrPn;
    private final Integer usrTi;

    public UserPrincipal(String id, String username, String password,
                         Collection<? extends GrantedAuthority> authorities,
                         String usrNm, String usrPn, Integer usrTi) {
        this.id = id;
        this.username = username;
        this.password = password;
        this.authorities = authorities;
        this.usrNm = usrNm;
        this.usrPn = usrPn;
        this.usrTi = usrTi;
    }

    /**
     * User 엔티티를 기반으로 UserPrincipal 객체 생성
     */
    public static UserPrincipal create(User user) {
        List<GrantedAuthority> authorities = new ArrayList<>();
        authorities.add(new SimpleGrantedAuthority("ROLE_USER"));
        return new UserPrincipal(
                user.getUsrId(),
                user.getUsrNm(),
                user.getUsrPw(),
                authorities,
                user.getUsrNm(),
                user.getUsrPn(),
                user.getUsrTi()
        );
    }

    // Lombok의 @Getter가 있으므로, getId(), getUsrNm() 등은 삭제했습니다.
    // 하지만 @Override가 필요한 UserDetails 메서드는 유지해야 합니다.
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }
}