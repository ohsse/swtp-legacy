package kr.co.mindone.ems.kafka;
/**
 * packageName    : kr.co.mindone.ems.kafka
 * fileName       : KafkaProperties
 * date           : 24. 9. 23.
 * description    : Kafka 관련 설정을 매핑하는 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.stereotype.Component;

//@Profile("!dev")
@Component
@ConfigurationProperties(prefix = "spring.kafka")
@Getter
@Setter
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaProperties {

	private String bootstrapServers;
	private Consumer consumer;

	/**
	 * Kafka Consumer 설정을 포함하는 클래스
	 */
	public static class Consumer {
		/**
		 * 메시지 키 역직렬화 설정
		 */
		private String keyDeserializer;

		/**
		 * 메시지 값 역직렬화 설정
		 */
		private String valueDeserializer;

		/**
		 * 메시지 자동 오프셋 리셋 설정
		 */
		private String autoOffsetReset;
	}
}
