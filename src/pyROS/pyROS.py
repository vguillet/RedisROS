from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import random
import string
import json

from redis import Redis
from redis_lock import Lock

# -> Import endpoint modules
# Core
from dep.pyROS.src.pyROS.Endpoints.Core.Publisher.Publisher_module import Publisher_module
from dep.pyROS.src.pyROS.Endpoints.Core.Subscriber.Subscriber_module import Subscriber_module
from dep.pyROS.src.pyROS.Endpoints.Core.Shared_variable.Shared_variable_module import Shared_variable_module

# Custom

# -> Import individual endpoint classes
from dep.pyROS.src.pyROS.Endpoints.Core.Publisher.Publisher import Publisher
from dep.pyROS.src.pyROS.Endpoints.Core.Subscriber.Subscriber import Subscriber
from dep.pyROS.src.pyROS.Endpoints.Core.Shared_variable.Shared_variable import Shared_variable
from dep.pyROS.src.pyROS.Timer import Timer

from dep.pyROS.src.pyROS.Callback_groups import ReentrantCallbackGroup

"""
Callback groups: https://docs.ros.org/en/foxy/How-To-Guides/Using-callback-groups.html

        "topic_1/subscribers": [subscriber_1, subscriber_2, ..., subscriber_n,]
        "topic_1/publishers": [publisher_1, publisher_2, ..., publisher_n,]
        
        "Node_1": [(publisher_1, Publisher, topic_1), (subscriber_1, Subscriber, topic_1), ..., (subscriber_n, Subscriber, topic_n),]
        
        # -> Subscriber queues
        "subscriber_1" = [...]
        "subscriber_2" = [...]     
"""


class PyROS(
    # Core
    Publisher_module,
    Subscriber_module,
    Shared_variable_module,

    # Custom
    # ROS_publisher_module,
    # ROS_subscriber_module,
):
    def __init__(self, namespace: str = "", ref: str = None):
        # -> Setup endpoint redis connection
        self.client = Redis()

        # -> Initialise the node
        self.namespace = namespace

        # -> Initialise ref if it does not exist
        if ref is not None:
            # -> Set ref
            self.ref = ref

        elif not hasattr(self, "ref"):
            # -> Generate a random ref
            self.ref = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])

        # -> Declare node
        with Lock(redis_client=self.client, name="Comm_graph"):
            if not self.client.exists("Comm_graph"):
                # -> Create comm_graph shared variable
                self.client.set("Comm_graph", json.dumps({
                    f"/{self.ref}": []
                }))
            else:
                # -> Get comm_graph shared variable
                comm_graph = json.loads(self.client.get("Comm_graph"))

                # -> Add node to comm_graph
                comm_graph[f"/{self.ref}"] = []

                # -> Update comm_graph shared variable
                self.client.set("Comm_graph", json.dumps(comm_graph))

        # -> Initialise the node dictionary
        self._node_dict = {
            "timers": {},
        }

        # -> Initialise pointers
        self.spinning = False
        self.threaded_spin = None
        self.threaded_timer_period = 0.00001

        # -> Initialise the node callbackgroups dictionary
        self.callbackgroups = {
            # Core
            "default_publisher_callback_group": ReentrantCallbackGroup(name="default_publisher_callback_group"),
            "default_subscriber_callback_group": ReentrantCallbackGroup(name="default_subscriber_callback_group"),
            "default_shared_variable_callback_group": ReentrantCallbackGroup(name="default_shared_variable_callback_group"),

            # Custom
            "ros_callback_group": ReentrantCallbackGroup(name="ros_callback_group"),
        }

        # -> Setup node messaging basis
        # -> Spin control variable
        self.default_spin_condition = self.declare_shared_variable(
            name="/default_spin_condition",
            value=True,
            descriptor=f"Default_spin_condition variable for node {self.ref}. Can be used to kill and spin process.",
            scope="local"
        )

        # -> Create publisher to the framework node msgs
        # self.framework_msgs = Publisher(
        #     msg_type="",
        #     topic="/Framework_msgs",
        #     qos_profile=None,
        #     parent_node_ref=self.ref
        # )

        # -> Initialise node endpoint modules
        # Core
        Publisher_module.__init__(self)
        Subscriber_module.__init__(self)
        Shared_variable_module.__init__(self)

        # Custom
        # ROS_publisher_module.__init__(self)
        # ROS_subscriber_module.__init__(self)

    # ================================================================== Spin logics
    def spin(self,
             condition: Shared_variable = None,
             threaded: bool = False,
             threaded_timer_period: float = None) -> None:
        """
        Spin the node until the condition is met or until default spin condition is False.
        If no condition is given, spin until default spin condition is False.
        If threaded is True, spin in a separate thread.
        -> Unlike with ROS, publishers/control variables/parameters do not need to be spun if instant is set to True.

        ROS2 compatibility note:
        - condition cannot be used
        - threaded cannot be used (and by extension threaded_timer_period)

        :param condition: A function that returns True or False. A condition must contain a control variable
        :param threaded: If True, spin in a separate thread.
        :param threaded_timer_period: The period of the timer used to spin in a separate thread.
        """

        if not self.spinning:
            with Lock(redis_client=self.client, name=self.ref):
                self.spinning = True

            # -> Set threaded timer period if provided
            if threaded_timer_period is not None:
                self.threaded_timer_period = threaded_timer_period

            # ----- Condition provided
            # -> If threaded is True, spin in a timer thread
            if threaded and condition is not None:
                self.threaded_spin = Thread(target=self.__conditional_spin, args=(condition,))
                self.threaded_spin.start()

            # -> If condition is given
            elif condition is not None:
                while condition.get_value() and self.default_spin_condition.get_value():
                    self.spin_once()

                # -> Reset spin control variable
                self.default_spin_condition.set_value(True)

            # ----- No condition provided
            elif threaded:
                self.threaded_spin = Thread(target=self.__unconditional_spin)
                self.threaded_spin.start()

            # -> If condition is not given, spin forever (break if spin control variable is False)
            else:
                while self.default_spin_condition.get_value():
                    self.spin_once()

                # -> Reset spin control variable
                self.default_spin_condition.set_value(True)

        else:
            print(f"!!! Node {self.ref} is already spinning. !!!")

    def __unconditional_spin(self):
        """
        Spin while the condition is met.
        """

        timer = self.create_timer(self.threaded_timer_period, self.spin_once)

        while self.default_spin_condition.get_value():
            pass

        timer.cancel()

        with Lock(redis_client=self.client, name=self.ref):
            self.spinning = False

            # -> Reset spin control variable
            self.default_spin_condition.set_value(True)

    def __conditional_spin(self, spin_condition):
        """
        Spin while the condition is met.
        """

        timer = self.create_timer(self.threaded_timer_period, self.spin_once)

        while spin_condition.get_value() and self.default_spin_condition.get_value():
            pass

        timer.cancel()

        with Lock(redis_client=self.client, name=self.ref):
            self.spinning = False

            # -> Reset spin control variable
            self.default_spin_condition.set_value(True)

    def spin_once(self) -> None:
        """
        For every callback group, call the callbacks in a reentrant way.
        """
        # -> Create a thread pool
        with ThreadPoolExecutor(max_workers=10) as executor:
            # -> Run every callback group in the callback group dictionary in a reentrant way
            for callback_group in self.callbackgroups.values():
                executor.submit(callback_group.spin)

    def destroy_node(self):
        """
        Destroy the node by removing all the publishers, subscribers, timers, etc...
        """
        # -> Destroy every publisher and subscriber in every callback group
        for callback_group in self.callbackgroups.values():
            for callback in callback_group.callbacks:
                # -> Destroy all the publishers in the callback
                if isinstance(callback, Publisher):
                    self.destroy_publisher(publisher=callback)

                # -> Destroy all the subscribers in the callback
                elif isinstance(callback, Subscriber):
                    self.destroy_subscription(subscriber=callback)

                # -> Destroy all the shared variables in the callback
                elif isinstance(callback, Shared_variable):
                    self.undeclare_shared_variable(name=callback.name)

        # -> Destroy every timer in the node
        timer_lst = self._node_dict["timers"]
        for timer in timer_lst:
            self.destroy_timer(timer=timer)

    # ================================================================== Misc
    # ---------------------------------------------- Timer
    @property
    def timers(self):
        """
        Get timers that have been created on this node.
        """

        # -> Return the list of timers
        return self._node_dict["timers"]

    # ----------------- Factory
    def create_timer(self,
                     timer_period_sec,
                     callback) -> Timer:
        """
        Create a timer that calls the callback function at the given rate.

        :param timer_period_sec: The period (s) of the timer.
        :param callback: A user-defined callback function that is called when the timer expires.
        """

        # -> Create a timer
        new_timer = Timer(
            timer_period=timer_period_sec,
            callback=callback)

        # -> Start the timer
        new_timer.start()

        # -> Add the timer to the node dictionary timers
        self._node_dict["timers"][new_timer.ref] = new_timer

        # -> Return the timer object
        return new_timer

    # ----------------- Destroyer
    def destroy_timer(self, timer: Timer) -> None:
        """
        Destroy the given timer.
        """

        # -> Stop the timer
        timer.cancel()

        # -> Remove the timer from the node dictionary timers
        del self._node_dict["timers"][timer.ref]
