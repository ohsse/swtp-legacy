package kr.co.mindone.ems;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
// @EnableScheduling 은 SchedulerConfig 로 일원화했다. 여기에 중복 선언이 남아 있으면
// SchedulerConfig 의 @Profile("!gu2") 게이트를 새어나가 섀도우 스택에서도 스케줄러가 돈다.
@EnableAsync
public class EmsApplication {

	public static void main(String[] args) {
		SpringApplication.run(EmsApplication.class, args);
	}

}
