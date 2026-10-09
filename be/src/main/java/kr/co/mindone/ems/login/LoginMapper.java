package kr.co.mindone.ems.login;
/**
 * packageName    : kr.co.mindone.alarm
 * fileName       : AlarmMapper
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import kr.co.mindone.ems.login.dto.User;
import org.apache.ibatis.annotations.Mapper;
import org.springframework.data.repository.query.Param;

import java.util.HashMap;
import java.util.List;

@Mapper
public interface LoginMapper {


	HashMap<String, Object> getUserToken(@Param("tkn") String tkn);

	HashMap<String, Object> getUserTokenOnly(@Param("tkn") String tkn);

	HashMap<String, Object>  getServerNo();

	HashMap<String, Object> findUserId(@Param("value") String value);

	void updateToken (HashMap<String,Object> item);
}
