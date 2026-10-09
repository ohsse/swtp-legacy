package com.wapplab.pms.web.common;

import io.swagger.annotations.ApiModelProperty;
import lombok.*;

@Getter
@Setter
@ToString
@NoArgsConstructor
@AllArgsConstructor
public class PumpForm {

    @ApiModelProperty(example = "주입될 key 값")
    private Object id;

    @ApiModelProperty(example = "2021-10-22 00:00:00")
    private String startDate;

    @ApiModelProperty(example = "2021-10-23 00:00:00")
    private String endDate;

}
