package com.wapplab.pms.kafka;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.stereotype.Component;

@Profile("!dev & !gm2")
@PropertySource("classpath:application-${spring.profiles.active}.yaml")
@Component
@ConfigurationProperties(prefix = "spring.kafka")
@Getter
@Setter
public class KafkaProperties {

	private String bootstrapServers;
	private Consumer consumer;

	public static class Consumer {
		private String keyDeserializer;
		private String valueDeserializer;
		private String autoOffsetReset;

		// getters and setters
	}
}
