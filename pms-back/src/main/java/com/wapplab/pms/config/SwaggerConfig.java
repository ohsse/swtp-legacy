package com.wapplab.pms.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@Configuration
@EnableSwagger2
public class SwaggerConfig {

    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
            .apiInfo(apiInfo())
            .select()
            .apis(RequestHandlerSelectors.basePackage("com.wapplab.pms"))
            .paths(PathSelectors.any())
            .build();
    }

    private ApiInfo apiInfo() {
        return new ApiInfoBuilder()
            .title("K-Water PMS REST API")
            .version("0.0.1")
            .description(makeDescription())
            .build();
    }

    private String makeDescription() {
        StringBuilder sb = new StringBuilder();
        sb.append("PMS 수자원 공사 서비스 API\n")
            .append("착수유입밸브\n")
            .append("water_controll_valve_01 : 착수 1번\n")
            .append("water_controll_valve_02 : 착수 2번\n");

        sb
            .append("송수펌프\n")
            .append("motor_01 ~ motor_04 평택\n")
            .append("motor_05 : 송산 2번\n")
            .append("motor_06 : 송산 1번\n");

        sb
            .append("pump_scada_01 ~ pump_scada_04 평택\n")
            .append("pump_scada_05 : 송산 1번\n")
            .append("pump_scada_06 : 송산 2번\n");

        sb
            .append("자동 급수 펌프 : auto_water_pump_01\n");

        sb
            .append("응집기 : agglomerate_01 ~ 08 \n");

        sb
            .append("gac역세펌프 : gac_backwash_pump_01 ~ 03\n");

        sb
            .append("pac튜브펌프 : pac_tube_pump_01 ~ 03\n");

        sb
            .append("pahcs튜브펌프 : pahcs_tube_pump_01 ~ 03\n");

        sb
            .append("급속분사교반기 : rapid_agitator_01 ~ 02\n");

        sb
            .append("냉각수펌프 : cooling_pump_01 ~ 04\n");

        sb
            .append("모티브펌프 : motif_pump_01 ~ 04\n");

        sb
            .append("슬러지수집기 : sludge_collector_01\n");

        sb
            .append("여과 역세 펌프 : filter_backwash_pump_01 ~ 04\n");

        sb
            .append("역세송풍기 : backwash_blower_01\n");

        sb
            .append("vcb반\n")
            .append("vcb_01 : VCB반 EHV-A3(VCB)\n")
            .append("vcb_02 : VCB반 EHV-A4(VCB)\n")
            .append("vcb_03 : VCB반 HV-MA1(VCB)\n")
            .append("vcb_04 : VCB반 EHV-B3(VCB)\n")
            .append("vcb_05 : VCB반 EHV-B4(VCB)\n")
            .append("vcb_06 : VCB반 HV-MA2(VCB)\n");

        sb
            .append("변압기\n")
            .append("transformer_01 : 변압기 Main TR#1\n")
            .append("transformer_02 : 변압기 Main TR#2\n")
            .append("transformer_03 : 변압기 저압(송수)TR#1\n")
            .append("transformer_04 : 변압기 저압(송수)TR#2\n");

        sb
            .append("펌프기동반\n")
            .append("pump_board_01\n")
            .append("pump_board_02\n")
            .append("pump_board_03\n")
            .append("pump_board_04\n");

        return sb.toString();
    }

}
