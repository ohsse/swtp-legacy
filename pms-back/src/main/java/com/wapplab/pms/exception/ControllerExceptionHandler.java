package com.wapplab.pms.exception;

import com.wapplab.pms.web.common.Message;
import com.wapplab.pms.web.common.ResponseDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;

@ControllerAdvice(basePackages = "com.wapplab.pms.web")
public class ControllerExceptionHandler {

    @ExceptionHandler(Exception.class)
    @ResponseBody
    public ResponseEntity<ResponseDTO> exception(Exception e) {
        return ResponseEntity.badRequest().body(ResponseDTO.badRequest(e.getMessage(), Message.ERROR.getMessage()));
    }

}
