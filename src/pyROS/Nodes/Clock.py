

from tracemalloc import start
from dep.pyROS.src.pyROS.pyROS import PyROS
from datetime import datetime

zero_datetime = datetime(year=1, month=1, day=1)

class Clock(PyROS):
    def __init__(self, ref: str = "Clock", namespace: str = "", start_datetime: datetime = zero_datetime, time_factor = 1):
        super().__init__(
            namespace=namespace, 
            ref=ref
            )

        # ----- Setup clock
        self.real_start_datetime = datetime.now()
        self.sim_start_datetime = start_datetime

        self.time_factor = time_factor

        self.datetime_publisher = self.create_publisher(
            msg_type=None,
            topic=ref
        )

    def datetime_callback(self):
        # -> Get real elapsed time
        delta_t = datetime.now() - self.real_start_datetime

        # -> Determine sim time
        sim_datetime = self.sim_start_datetime + delta_t * self.time_factor
        
        # -> Convert datetime to string
        # sim_datetime_string = sim_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
        sim_datetime_string = sim_datetime.strftime('%04d-%02d-%02d %02d:%02d:%02d.%06d' % (sim_datetime.year, sim_datetime.month, sim_datetime.day, sim_datetime.hour, sim_datetime.minute, sim_datetime.second, sim_datetime.microsecond))

        # -> Publish sim time
        self.datetime_publisher.publish(msg=sim_datetime_string)

    def run(self):
        self.create_timer(
            timer_period_sec=0.01,
            callback=self.datetime_callback
        )
