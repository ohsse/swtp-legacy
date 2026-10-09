package kr.co.mindone.ems.common;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;

@Configuration
// [군산 섀도우] gu2 프로파일에서는 이 설정 자체가 뜨지 않아 @EnableScheduling 이 꺼진다.
// 그러면 SchedulerService / AlarmService / DrvnConfig / PumpScheduler / KafkaProducerTasks 의
// @Scheduled 가 한꺼번에 멈춘다 - 운영 스택과 병행 기동할 때 자정 삭제 3종과 매분 집계가
// 두 번 도는 것을 막기 위함이다.
// 개별 클래스에 @Profile 을 걸지 않는 이유: AlarmService 는 @Profile 이 없는 @Service 이고
// AlarmController / AiService 가 그 빈에 의존한다. 클래스를 끄면 알람 화면이 깨진다.
// 아래 TaskScheduler 빈을 주입받는 코드는 한 곳도 없어 이 설정이 통째로 빠져도 기동에 지장이 없다.
@Profile("!gu2")
@EnableScheduling
public class SchedulerConfig {
	@Bean
	public TaskScheduler taskScheduler() {
		ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
		scheduler.setPoolSize(5); // 동시에 5개 작업 실행 가능
		scheduler.setThreadNamePrefix("scheduler-task-");
		scheduler.initialize();
		return scheduler;
	}
}
