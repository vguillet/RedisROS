

from tracemalloc import start
from dep.pyROS.src.pyROS.pyROS import PyROS
from datetime import datetime

zero_timestamp = datetime(year=1, month=1, day=1)

class Clock(PyROS):
    def __init__(self, ref: str = "Clock", namespace: str = "", start_timestamp: datetime.timestamp = zero_timestamp, time_factor = 1):
        super().__init__(
            namespace=namespace, 
            ref=ref
            )

        # ----- Setup clock
        self.real_start_timestamp = datetime.timestamp(datetime.now())
        self.sim_start_timestamp = start_timestamp

        self.time_factor = time_factor

        self.datetime_publisher = self.create_publisher(
            msg_type=None,
            topic=ref
        )

        self.create_timer(
            timer_period_sec=0.01,
            callback=self.datetime_callback
        )

    def datetime_callback(self):
        delta_t = datetime.timestamp(datetime.now()) - self.real_start_timestamp

        sim_timestamp = self.sim_start_timestamp + delta_t * self.time_factor

        self.datetime_publisher.publish(msg=str(sim_timestamp))
