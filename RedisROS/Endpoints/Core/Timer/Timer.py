import json
from datetime import datetime
import random
import string

from redis.commands.graph import Graph, Edge, Node
from redis_lock import Lock

from ..Endpoint_abc import Endpoint_abc


class Timer(Endpoint_abc):
    def __init__(self,
                callback,
                timer_period: float = 1,
                ref: str = None,
                parent_node_ref: str = None,
                namespace: str = "",
                 manual_spin: bool = False
                ):

        # -> Create a unique ID for the timer
        if ref is None: 
            self.ref = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
        else:
            self.ref = ref

        # -> Initialise the timer properties
        self.timer_period = timer_period
        self.callback = callback

        # -> Setup endpoint
        Endpoint_abc.__init__(self,
                              parent_node_ref=parent_node_ref,
                              namespace=namespace,
                              manual_spin=manual_spin
                              )

        # TODO: Couple timer with run clock to ensure the desired timer_period is achieved
        if timer_period != 1:
            print(f"WARNING - {self.ref} : Timers time_period currently not implemented, timer will run at a rate of 1Hz per spin")

    def spin(self) -> None:
        # ----- Spin rate is larger than timer rate
        # if spin_rate > self.timer_period:

        # -> Call callback
        self.callback()

    # Placeholder methods
    def declare_endpoint(self) -> None:
        pass
    
    def destroy_endpoint(self) -> None:
        pass
