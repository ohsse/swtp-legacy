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
public class SettingForm {

    @ApiModelProperty(example = "모터 ID")
    private String grp_id;

    @ApiModelProperty(example = "채널 이름")
    private String channel_nm;

    @ApiModelProperty(example = "파라메타 명")
    private String parm_nm;
    
    @ApiModelProperty(example = "파라메타 값")
    private String parm_value;

}
