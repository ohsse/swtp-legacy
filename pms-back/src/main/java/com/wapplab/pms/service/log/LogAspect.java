package com.wapplab.pms.service.log;

import com.wapplab.pms.web.common.Message;
import java.util.Locale;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
@Slf4j
public class LogAspect {
    private static final String PRINT_LINE = "===============";


    @Around("within(com.wapplab.pms.service..*)")
    public Object logPrinter(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        //log.info(PRINT_LINE + methodName + PRINT_LINE);
        Object proceed = joinPoint.proceed();
        //log.info(PRINT_LINE + methodName + " " + Message.SUCCESS.getMessage().toUpperCase(Locale.ROOT) + PRINT_LINE);
        return proceed;
    }

}
