package com.wapplab.pms;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class KwaterPmsServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(KwaterPmsServiceApplication.class, args);
    }

}
