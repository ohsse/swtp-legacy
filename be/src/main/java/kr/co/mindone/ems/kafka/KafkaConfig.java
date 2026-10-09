package kr.co.mindone.ems.kafka;
/**
 * kafka 2중화 구성변경으로 미사용
 */

import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;

import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

// !gu2 : 군산 섀도우는 읽기 전용이라 Kafka 를 쓰지 않는다. 운영과 같은 group.id 로
//        조인하면 파티션이 갈려 기존 앱이 SCADA 를 절반만 받는다(에러 없이 조용히).
@Profile("!dev & !gm2 & !hy2 & !hp2 & !ji2 & !gr & !wm & !gs & !gu & !gu2 & !ba & !ss")
@Configuration
@EnableKafka
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaConfig {
    @Value("${spring.kafka.bootstrap-servers}")
    private String bootstrapServers;

    @Value("${spring.kafka.consumer.auto-offset-reset}")
    private String autoOffsetReset;

    public static final String TIME_ALL = "all";
    public static final String TIME_HOUR = "hour";
    public static final String TIME_MIN = "min";
    public static final String TIME_SEC = "sec";

    @Bean
    public AdminClient adminClient() {
        Properties properties = new Properties();
        properties.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        return AdminClient.create(properties);
    }



    @Bean
    public ConsumerFactory<String, String> consumerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, autoOffsetReset);  // 이 줄을 추가
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        // 다른 소비자 설정 추가 가능...

        return new DefaultKafkaConsumerFactory<>(config);
    }



    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, String> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, String> factory = new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());
        // factory의 다른 설정 (예: 오류 핸들러, 동시성, 등)...
        return factory;
    }


}
