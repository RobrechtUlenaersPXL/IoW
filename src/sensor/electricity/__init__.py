import time
import json

from math import sqrt
from typing import List
from multiprocessing import Process, Event, Queue, Lock
from src.base import EdgiseBase
from grove.adc import ADC
from config import cfg
import json

import queue


class ACSensor(Process, EdgiseBase):
    def __init__(self, stop_event: Event, logging_q: Queue, washcycle_q: Queue, output_q: Queue,
                 config_dict, resource_lock: Lock, **kwargs):
        self._stop_event = stop_event
        self._logging_q: Queue = logging_q
        self._washcycle_q: Queue = washcycle_q
        self._output_q: Queue = output_q
        self.RMS_voltage = 230
        self.VCC = 3.3
        self._config_dict = config_dict
        self._name = self._config_dict['name']
        self._threshold = self._config_dict['threshold']
        self.adc = ADC(address=self._config_dict['i2cAddress'])
        self.i2c_lock = resource_lock

        Process.__init__(self)
        EdgiseBase.__init__(self, name=self._name, logging_q=logging_q)

        # config = {
        #           "name":str
        #           "PINNR":int,
        #           "SensorI    bD":int,
        #           "Unit":"cm"
        #           "SensorType":""
        #           }

    def read_sensor(self):
        sample_time = 2
        start_time = time.time()
        sensor_max = 0
        self.info("start sampling")
        while (time.time() - start_time < sample_time):
            sensor_value = self.adc.read_raw(self._config_dict['pin'])
            if (sensor_value > sensor_max):
                sensor_max = sensor_value
        print("------------------------------------------------------------sensor value {}".format(sensor_max))
        return sensor_max

    def amplitude_current(self, sensor_value):
        return 2 * (float(sensor_value) / 4096 * self.VCC / 800 * 2000)  # 1:2000 coils -> A => 2000000 mA

    def RMS_current(self, amplitude_current):
        return amplitude_current / sqrt(2)

    def avg_power_consumption(self, RMS_current):
        return self.RMS_voltage * RMS_current

    def start_washcycle(self, raw_val, threshold):
        if raw_val > threshold:
            self._washcycle_q.put_nowait(True)
        elif raw_val < threshold:
            try:
                self._washcycle_q.get_nowait()
            except queue.Empty:
                pass

    def run(self) -> None:
        self.info("Starting AC sensor")
        print(self._config_dict['name'])
        # threshold = 4 # not representable value

        while not self._stop_event.is_set():

            self.i2c_lock.acquire()
            try:
                raw_val = self.read_sensor()
            finally:
                self.i2c_lock.release()

            self.info("threshold: {}".format(self._threshold))
            self.start_washcycle(raw_val, self._threshold)
            if not self._washcycle_q.empty():
                self.info("Raw Value: {}".format(raw_val))
                amplitude_current = self.amplitude_current(raw_val)
                self.info("A I Value: {}".format(amplitude_current))
                rms_current = self.RMS_current(amplitude_current)
                self.info("RMS I Value: {}".format(rms_current))
                avg_power = self.avg_power_consumption(rms_current)
                self.info("AVG W Value: {}".format(avg_power))

                data = {'electricitySensorData': {
                    'rawVal': raw_val,
                    'currentAmp': amplitude_current,
                    'rmsCurrent': rms_current,
                    'avgPower': avg_power
                }}
                measurement = {'data': data}
                self._output_q.put_nowait({'event': json.dumps(measurement)})
            time.sleep(3)
