export default class ModelListClass {
  constructor(
    title,
    id,
    scada_id,
    threshold,
    idx,
  ) {
    // title: '평택계통 송수펌프모터 #1',
    // id: 'motor_01',
    // scada_id: 'pump_scada_01',
    // motor_de_amp: [],
    // motor_nde_amp: [],
    // pump_de_amp: [],
    // pump_nde_amp: [],
    // motor_de_amp_val: 0,
    // motor_nde_amp_val: 0,
    // pump_de_amp_val: 0,
    // pump_nde_amp_val: 0,
    // eq_on: true,
    // alarm: false,
    // select: true,
    // idx: 0,
    // visible: true,
    this.title = title;
    this.threshold = threshold;
    this.id = id;
    this.scada_id = scada_id;
    this.motor_de_amp = [];
    this.motor_nde_amp = [];
    this.pump_de_amp = [];
    this.pump_nde_amp = [];
    this.motor_de_amp_val = 0;
    this.motor_nde_amp_val = 0;
    this.pump_de_amp_val = 0;
    this.pump_nde_amp_val = 0;
    this.eq_on = true;
    this.alarm = false;
    if (idx == 0) this.select = true;
    else this.select = false;
    this.idx = idx;
    this.visible = true;
    this.flag = true;
  }
}
