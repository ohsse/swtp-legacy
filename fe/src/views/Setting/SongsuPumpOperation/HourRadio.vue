<template>
    <b-col class="div_content_col2 h-100 mx-1">
        <div class="custom-radio">
            <input :id="name + type" type="radio" :name="name" :value="name" :checked="checked()"
                @change="$emit('input', name, type)" />
            <label class="radio-shape radioBg" :for="name + type"></label>
        </div>
    </b-col>
</template>
<script>

export default {
    props: {
        name: {
            type: String,
            required: true,
        },
        type: {
            type: String,
            required: true,
        },
        value: {
            type: String,
            required: true,
        }
    },
    methods: {
        handleRadioChange() {
            this.$emit('input', this.name, this.type);
        },
        checked() {
            if (this.type == "top" && this.value == "0") {
                return true;
            } else if (this.type == "bot" && this.value == "1") {
                return true;
            } else {
                return false
            }
        }
    },
}
</script>
<style scoped>
.div_box_border {
    border: 1px solid #489cf2d1;
    box-shadow: 0 0 3px #489cf2;
    background-color: #0947ae66;
    border-radius: 5px;
}

.custom-radio input {
    margin: 0;
    padding: 0;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
}

.radioBg {
    background-image: url(@/assets/img/pump/pump_on.png);
}

.custom-radio input:active+.radio-shape {
    opacity: .9;
}

.custom-radio input:checked+.radio-shape {
    -webkit-filter: none;
    -moz-filter: none;
    filter: none;
}

.radio-shape {
    cursor: pointer;
    background-size: contain;
    background-repeat: no-repeat;
    display: inline-block;
    width: 40px;
    height: 40px;
    -webkit-transition: all 100ms ease-in;
    -moz-transition: all 100ms ease-in;
    transition: all 100ms ease-in;
    -webkit-filter: brightness(1.8) grayscale(1) opacity(.4);
    -moz-filter: brightness(1.8) grayscale(1) opacity(.4);
    filter: brightness(1.8) grayscale(1) opacity(.4);
}

.div_content_col2 {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: #0a4cba8f;
    border: 2px solid #0A5AAE8f;
    border-radius: 5px;
    color: #fff;
}
</style>
