package kr.co.mindone.ems.config;
/**
 * packageName    : kr.co.mindone.ems.config
 * fileName       : WebConfig
 * date           : 24. 9. 23.
 * description    : CORS 설정을 제공하는 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

	/**
	 * CORS 설정을 추가하는 메서드
	 *
	 * @param registry CORS 매핑을 관리하는 객체
	 */
	@Override
	public void addCorsMappings(CorsRegistry registry) {
		registry.addMapping("/**")
				.allowedOrigins("*")
				.exposedHeaders(HttpHeaders.AUTHORIZATION)
				.maxAge(60 * 60)
				.allowedMethods(
						HttpMethod.GET.name(),
						HttpMethod.POST.name(),
						HttpMethod.DELETE.name(),
						HttpMethod.PUT.name(),
						HttpMethod.PATCH.name()
				);
	}

	/*@Override
	public void addInterceptors(InterceptorRegistry registry) {
		// 인터셉터 등록 및 경로 설정
		registry.addInterceptor(new LoginInterceptor())
				.addPathPatterns("/**"); // 모든 경로에 대해 인터셉터 적용
				//.excludePathPatterns("/api/login", "/api/logout"); // 특정 경로는 제외
	}*/
}


