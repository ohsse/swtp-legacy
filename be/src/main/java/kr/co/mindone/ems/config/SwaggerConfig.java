package kr.co.mindone.ems.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * packageName    : kr.co.mindone.ems.config
 * fileName       : SwaggerConfig
 * date           : 24. 9. 23.
 * description    : Swagger 설정을 제공하는 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
@Configuration
@EnableSwagger2
public class SwaggerConfig {

	/**
	 * API 이름
	 */
	private static final String API_NAME = "EMS API";

	/**
	 * API 버전
	 */
	private static final String API_VERSION = "0.0.1";

	/**
	 * API 설명
	 */
	private static final String API_DESCRIPTION = "정수장 API 명세서";

	/**
	 * Swagger Docket 빈을 생성하는 메서드
	 *
	 * @return Docket Swagger를 구성하는 주요 빌더 객체
	 */
	@Bean
	public Docket api() {
		return new Docket(DocumentationType.SWAGGER_2)
				.select()
				.apis(RequestHandlerSelectors.basePackage("kr.co.mindone.ems"))
				.paths(PathSelectors.any())
				.build()
				.apiInfo(apiInfo());
	}

	/**
	 * API 정보를 설정하는 메서드
	 *
	 * @return ApiInfo API 이름, 설명, 버전 등 메타 정보를 포함하는 객체
	 */
	private ApiInfo apiInfo() {
		return new ApiInfoBuilder()
				.title(API_NAME)
				.description(API_DESCRIPTION)
				.version(API_VERSION)
				.build();
	}
}

	/** 스웨거 사용자 인증 부분 **/
//	private ApiKey apiKey() {
//		return new ApiKey(Header.JWT_TYPE, HttpHeaders.AUTHORIZATION, "header");
//	}

//	private SecurityContext securityContext() {
//		return SecurityContext.builder().securityReferences(defaultAuth()).build();
//	}

//	private List<SecurityReference> defaultAuth() {
//		AuthorizationScope authorizationScope = new AuthorizationScope("global", "accessEverything");
//		AuthorizationScope[] authorizationScopes = new AuthorizationScope[1];
//		authorizationScopes[0] = authorizationScope;
//		return Arrays.asList(new SecurityReference(Header.JWT_TYPE, authorizationScopes));
//	}

//}
