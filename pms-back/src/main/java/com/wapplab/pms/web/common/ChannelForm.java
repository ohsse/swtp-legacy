package com.wapplab.pms.web.common;

import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;

@Getter
@ToString
@NoArgsConstructor
@AllArgsConstructor
public class ChannelForm {

    @ApiModelProperty(example = "모터 ID")
    private String motor_id;

    @ApiModelProperty(example = "채널 이름")
    private String channel_nm;

    @ApiModelProperty(example = "2021-10-22 00:00:00")
    private String acq_date;



}
