<template>
    <div class="align-itmes-center justify-content-center" style="height: 300px; display: flex;">
        <b-col v-bind:style="{ height: '95%', width: '100%' }" class="d-flex justify-content-center align-items-center">
        <AreaChart ref="AreaChart"/>
        <!-- <div class="box-value-contents">
            <div class="box-value-contents_nodata">No Data</div>
        </div> -->
      </b-col>
    </div>
</template>
<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
// import ChartClass from "@/components/Chart/ChartClass.js";
import ChartLineClass from "@/components/Chart/ChartLineClass";
// import LineChart from "@/components/Chart/LineChart.vue";
export default {
    components:{
        AreaChart,
        // LineChart
    },
    data(){
        return{
            fac_name:null,
            data :{},
            chartStyle:null,
            nodataStyle:null,
            chartView:{
                display : 'block'
            },
            noData:{
                display : 'none'
            },
            chartHtml:{

            }
            
        }
    },
    methods:{
        setChartData(datas){
            this.data = datas
          
            if(this.fac_name != null){
                if(this.data.yData[this.fac_name] != undefined){
                    
                    this.makeChart()
                }else{
                    this.noDataView()
                }
            }else{
                this.noDataView()
            }
        },
        selectFac(fac_name){
         
            this.fac_name = fac_name;
            if(Object.keys(this.data).length !== 0){
           
                if(this.data.yData[this.fac_name] != undefined){
      
                    this.makeChart()
                }else{
                    this.noDataView()
                }

            }else{
                this.noDataView()
            }
        },
        makeChart(){
            this.chartStyle = this.chartView
            this.nodataStyle = this.noData
            let chartClass = new ChartLineClass(this.data.xData, [this.data.yData[this.fac_name]],[this.fac_name], null,"날짜", "m")
            chartClass.changeSingleChart();
            chartClass.legendHide();
            chartClass.setGridSize('5%','8%','10%',10,true)
            this.$refs.AreaChart.changeData(chartClass);
        },
        noDataView(){
            this.chartStyle = this.noData
            this.nodataStyle = this.chartView
        }
    }
}
</script>
<style>
.box-value-contents_nodata {
  width: 100%;
  text-shadow: 0 0 9px #5cafff;
  font-size: 40px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 0;
  letter-spacing: normal;
  text-align: center;
  color: #fff;
  font-family: "LAB디지털" !important;
}
</style>