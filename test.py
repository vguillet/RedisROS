
from concurrent.futures import ThreadPoolExecutor, thread
from datetime import datetime
import time

from RedisROS.Nodes import Clock
from RedisROS import Node

NAMESPACE = "namespace"


class test_pub(Node):
    def __init__(self, ref: str = "test_pub") -> None:
        super().__init__(
            ref=ref,
            namespace=NAMESPACE
        )

        self.test_publisher = self.create_publisher(
            msg_type=None,
            topic="test_topic",
        )

        self.create_timer(
            timer_period_sec=0.01,
            callback=self.test_callback
            )

    def run(self):
        self.spin()

        # time.sleep(2)
        # self.default_spin_condition.set_value(value=False, instant=True)
        # test_timer.cancel()
        # self.destroy_timer(timer=test_timer)

    def test_callback(self):
        msg = f"Hello World! |{datetime.timestamp(datetime.now())}|"
        # print(f"\n-> Publishing message: {msg}")
        self.test_publisher.publish(msg, instant=False)


class test_sub(Node):
    def __init__(self, ref: str = "test_sub") -> None:
        super().__init__(
            ref=ref,
            namespace=NAMESPACE
        )

        self.test_subscription = self.create_subscription(
            msg_type=None,
            topic="test_topic",
            callback=self.test_callback,
            qos_profile=None,
            callback_group=None
        )

    def run(self):
        self.spin()

    def test_callback(self, msg):
        ts = datetime.timestamp(datetime.now())
        msg_ts = msg.split("|")[1]

        # -> Get timestamp difference
        ts_diff = ts - float(msg_ts)

        # -> Convert timestamp difference to seconds
        ts_diff_sec = ts_diff

        print(f"-> New message: {msg}, (comm delay: {ts_diff_sec})")


from redis import Redis
from threading import Thread
from multiprocessing import Process

client = Redis()
client.flushall()

# clock_thread = Process(target=lambda: Clock(ref="Sim_clock", namespace=NAMESPACE, time_factor=10))
# clock_thread.start()

# pub_lst = []
# sub_lst = []

# for i in range(3):
#     pub_lst.append(test_pub(ref=f"Publisher_{i+1}"))
#     sub_lst.append(test_sub(ref=f"Subscriber_{i+1}"))

# thread_lst = []

# for i in range(10):
#     thread_lst.append(Thread(target=test_pub))
#     thread_lst.append(Thread(target=test_sub))

# for thread in thread_lst:
#     thread.start()

test_pub1 = test_pub()
test_sub1 = test_sub()

print("Created Nodes")

pub_thread = Thread(target=test_pub1.run)
sub_thread = Thread(target=test_sub1.run)

pub_thread.start()
sub_thread.start()

print("Primed")
