package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : AsyncConfig
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.context.annotation.Bean;
import java.util.concurrent.Executor;

@Configuration
@EnableAsync
public class AsyncConfig {

    /**
     * AsyncConfigurer으로 Project에서 사용되는 Async 관리
     * @return Async 설정
     */
    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(16);  // 기본 스레드 수
        executor.setMaxPoolSize(32);   // 최대 스레드 수
        executor.setQueueCapacity(500); // 큐 최대 크기
        executor.setThreadNamePrefix("singleThreadExecutor");
        executor.setKeepAliveSeconds(60);
        executor.initialize();
        return executor;
    }
}