<template>
   <div class="box-edge top-L blur"></div>
         <div class="box-edge top-R blur"></div>
         <div class="box-edge bottom-L blur"></div>
         <div class="box-edge bottom-R blur"></div>
         <div class="box-edge top-L"></div>
         <div class="box-edge top-R"></div>
         <div class="box-edge bottom-L"></div>
         <div class="box-edge bottom-R"></div>
</template>

<style lang="scss" scoped>
.box-edge{
                    width: 15px;
                    height: 15px;
                    position: absolute;
                    
                }
                .top-L{
                    top: -1px;
                    left: -1px;
                    border-top: 2px solid #2C80FF;
                    border-left: 2px solid #2C80FF;
                    border-top-left-radius: 12px;
                }
                .top-R{
                    top: -1px;
                    right: -1px;
                    border-top: 2px solid #2C80FF;
                    border-right: 2px solid #2C80FF;
                    border-top-right-radius: 12px;
                }
                .bottom-L{
                    bottom: -1px;
                    left: -1px;
                    border-bottom: 2px solid #2C80FF;
                    border-left: 2px solid #2C80FF;
                    border-bottom-left-radius: 12px;
                }
                .bottom-R{
                    bottom: -1px;
                    right: -1px;
                    border-bottom: 2px solid #2C80FF;
                    border-right: 2px solid #2C80FF;
                    border-bottom-right-radius: 12px;
                }
    
                .blur{
                    filter: blur(3px);
                    -webkit-filter: blur(3px);
                    border-color: #24d3ff;
                }
</style>