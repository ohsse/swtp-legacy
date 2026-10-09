export default class SongsuListClass {
  constructor(
    motor_id,
    scada_id,
    idx,
  ) {
        //         alarm: false,
        //         id: 'motor_01',
        //         scadaId: 'pump_scada_01',
        //         brg_motor_de_temp: 0,
        //         brg_motor_nde_temp: 0,
        //         brg_pump_de_temp: 0,
        //         brg_pump_nde_temp: 0,
        //         motor_de_rms_amp: 0,
        //         motor_nde_rms_amp: 0,
        //         pump_de_rms_amp: 0,
        //         pump_nde_rms_amp: 0,
      this.alarm = false;
      this.id = motor_id;
      this.scada_id = scada_id;
      this.brg_motor_de_temp = 0;
      this.brg_motor_nde_temp = 0;
      this.brg_pump_de_temp = 0;
      this.brg_pump_nde_temp = 0;
      this.motor_de_rms_amp = 0;
      this.motor_nde_rms_amp = 0;
      this.pump_de_rms_amp = 0;
      this.pump_nde_rms_amp = 0;
      this.idx = idx;
  }
}
