package com.wapplab.pms.web.common;

import io.swagger.annotations.ApiModelProperty;
import io.swagger.annotations.ApiParam;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class DateForm {

    @ApiModelProperty(example = "2021-10-22 00:00:00")
    private String startDate;

    @ApiModelProperty(example = "2021-10-23 00:00:00")
    private String endDate;

}
