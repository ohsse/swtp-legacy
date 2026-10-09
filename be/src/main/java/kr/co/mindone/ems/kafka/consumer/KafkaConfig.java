package kr.co.mindone.ems.kafka.consumer;
/**
 * packageName    : kr.co.mindone.ems.kafka.consumer
 * fileName       : KafkaConfig
 * date           : 24. 9. 23.
 * description    : Kafka 설정 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
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

@Profile({
        "gm2",
        "hy2",
        "hp2",
        "ji2",
        "gr",
        "wm",
        "gs",
        "gu",
        "ba",
        "ss"
})
@Configuration
@EnableKafka
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaConfig {
    @Value("${spring.kafka.bootstrap-servers-1}")
    private String bootstrapServers1;

    @Value("${spring.kafka.bootstrap-servers-2}")
    private String bootstrapServers2;

    @Value("${spring.kafka.consumer.auto-offset-reset}")
    private String autoOffsetReset;

    public static final String TIME_ALL = "all";
    public static final String TIME_HOUR = "hour";
    public static final String TIME_MIN = "min";
    public static final String TIME_SEC = "sec";

    /**
     * 첫 번째 Kafka 클러스터의 AdminClient를 생성하는 메서드
     *
     * @return AdminClient 인스턴스
     */
    @Bean
    public AdminClient adminClient1() {
        Properties properties = new Properties();
        properties.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers1);
        return AdminClient.create(properties);
    }

    /**
     * 첫 번째 Kafka 클러스터의 ConsumerFactory를 생성하는 메서드
     *
     * @return ConsumerFactory<String, String> 인스턴스
     */
    @Bean
    public ConsumerFactory < String, String > consumerFactory1() {
        Map < String, Object > config = new HashMap < > ();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers1);
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, autoOffsetReset); // 이 줄을 추가
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        // 다른 소비자 설정 추가 가능...

        return new DefaultKafkaConsumerFactory < > (config);
    }

    /**
     * 첫 번째 Kafka 클러스터의 ConcurrentKafkaListenerContainerFactory를 생성하는 메서드
     *
     * @return ConcurrentKafkaListenerContainerFactory<String, String> 인스턴스
     */
    @Bean
    public ConcurrentKafkaListenerContainerFactory < String, String > kafkaListenerContainerFactory1() {
        ConcurrentKafkaListenerContainerFactory < String, String > factory = new ConcurrentKafkaListenerContainerFactory < > ();
        factory.setConsumerFactory(consumerFactory1());
        // factory의 다른 설정 (예: 오류 핸들러, 동시성, 등)...
        return factory;
    }

    /**
     * 두 번째 Kafka 클러스터의 AdminClient를 생성하는 메서드
     *
     * @return AdminClient 인스턴스
     */
    @Bean
    public AdminClient adminClient2() {
        Properties properties = new Properties();
        properties.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers2);
        return AdminClient.create(properties);
    }

    /**
     * 두 번째 Kafka 클러스터의 ConsumerFactory를 생성하는 메서드
     *
     * @return ConsumerFactory<String, String> 인스턴스
     */
    @Bean
    public ConsumerFactory < String, String > consumerFactory2() {
        Map < String, Object > config = new HashMap < > ();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers2);
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, autoOffsetReset); // 이 줄을 추가
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        // 다른 소비자 설정 추가 가능...

        return new DefaultKafkaConsumerFactory < > (config);
    }

    /**
     * 두 번째 Kafka 클러스터의 ConcurrentKafkaListenerContainerFactory를 생성하는 메서드
     *
     * @return ConcurrentKafkaListenerContainerFactory<String, String> 인스턴스
     */
    @Bean
    public ConcurrentKafkaListenerContainerFactory < String, String > kafkaListenerContainerFactory2() {
        ConcurrentKafkaListenerContainerFactory < String, String > factory = new ConcurrentKafkaListenerContainerFactory < > ();
        factory.setConsumerFactory(consumerFactory2());
        // factory의 다른 설정 (예: 오류 핸들러, 동시성, 등)...
        return factory;
    }

}