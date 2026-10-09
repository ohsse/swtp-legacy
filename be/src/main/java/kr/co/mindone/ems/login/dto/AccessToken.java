package kr.co.mindone.ems.login.dto;

import javax.persistence.*;
import java.util.Date;

@Entity
@Table(name = "tb_acs_tkn")
public class AccessToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "seq")
    private Integer seq;

    @Column(name = "tkn", length = 256)
    private String tkn;

    @Column(name = "usr_id", length = 40)
    private String usrId;

    @Column(name = "usr_nm", length = 100)
    private String usrNm;

    @Column(name = "usr_auth")
    private Integer usrAuth; // 필요한 경우 Boolean 또는 Enum 등으로 변경 가능

    @Column(name = "expr_ti")
    @Temporal(TemporalType.TIMESTAMP)
    private Date exprTi;

    // 기본 생성자
    public AccessToken() {}

    // Getter/Setter
    public Integer getSeq() {
        return seq;
    }

    public void setSeq(Integer seq) {
        this.seq = seq;
    }

    public String getTkn() {
        return tkn;
    }

    public void setTkn(String tkn) {
        this.tkn = tkn;
    }

    public String getUsrId() {
        return usrId;
    }

    public void setUsrId(String usrId) {
        this.usrId = usrId;
    }

    public String getUsrNm() {
        return usrNm;
    }

    public void setUsrNm(String usrNm) {
        this.usrNm = usrNm;
    }

    public Integer getUsrAuth() {
        return usrAuth;
    }

    public void setUsrAuth(Integer usrAuth) {
        this.usrAuth = usrAuth;
    }

    public Date getExprTi() {
        return exprTi;
    }

    public void setExprTi(Date exprTi) {
        this.exprTi = exprTi;
    }
}

