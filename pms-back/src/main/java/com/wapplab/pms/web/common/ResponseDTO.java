package com.wapplab.pms.web.common;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import org.springframework.http.HttpStatus;

@Data
public class ResponseDTO {

    @ApiModelProperty(
        example = "200"
    )
    private int status;

    @ApiModelProperty(
        example = "success"
    )
    private String message;

    @ApiModelProperty(
        example = "["
            + "    {"
            + " \"key\": \"value\""
            + "},"
            + "  ]"
    )
    private Object datas;

    public ResponseDTO(int status, String message, Object datas) {
        this.status = status;
        this.message = message;
        this.datas = datas;
    }

    public static ResponseDTO ok(String message, Object datas) {
        return new ResponseDTO(HttpStatus.OK.value(), message, datas);
    }

    public static ResponseDTO badRequest(String message, Object datas) {
        return new ResponseDTO(HttpStatus.BAD_REQUEST.value(), message, datas);
    }

}
