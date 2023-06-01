import time
from threading import Timer as ThreadTimer
import random
import string


class Async_timer(ThreadTimer):
    def __init__(self,
                 timer_period,
                 callback,
                 ref: str = None
                 ):
        super().__init__(interval=timer_period, function=callback)

        # -> Create a unique ID for the timer
        if ref is None: 
            self.ref = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
        else:
            self.ref = ref

        # -> Initialise the timer properties
        self.timer_period = timer_period
        self.callback = callback

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

    def destroy_endpoint(self) -> None:
        pass


if __name__ == "__main__":
    def callback():
        print("Hello World!")

    timer = Timer(timer_period=0.1, callback=callback)
    timer.run()

