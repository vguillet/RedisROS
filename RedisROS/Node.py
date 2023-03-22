from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import random
import string
import json

from redis import Redis
from redis.commands.graph import Graph, Edge
from redis.commands.graph import Node as Redis_node

from redis_lock import Lock

# -> Import endpoint modules
# Core
from RedisROS.Endpoints.Core.Publisher.Publisher_module import Publisher_module
from RedisROS.Endpoints.Core.Subscriber.Subscriber_module import Subscriber_module
from RedisROS.Endpoints.Core.Shared_variable.Shared_variable_module import Shared_variable_module
from RedisROS.Endpoints.Core.Timer.Timer_module import Timer_module

# Custom

# -> Import individual endpoint classes
from RedisROS.Endpoints import Publisher
from RedisROS.Endpoints import Subscriber
from RedisROS.Endpoints import Shared_variable
from RedisROS.Async_timer import Async_timer
from RedisROS.Callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup

"""
Callback groups: https://docs.ros.org/en/foxy/How-To-Guides/Using-callback-groups.html

        "topic_1/subscribers": [subscriber_1, subscriber_2, ..., subscriber_n,]
        "topic_1/publishers": [publisher_1, publisher_2, ..., publisher_n,]
        
        "Node_1": [(publisher_1, Publisher, topic_1), (subscriber_1, Subscriber, topic_1), ..., (subscriber_n, Subscriber, topic_n),]
        
        # -> Subscriber queues
        "subscriber_1" = [...]
        "subscriber_2" = [...]     
"""


class Node(
    # Core
    Publisher_module,
    Subscriber_module,
    Shared_variable_module,
    Timer_module,

    # Custom
    # ROS_publisher_module,
    # ROS_subscriber_module,
):
    def __init__(self, 
                 ref: str = None,
                 namespace: str = "",
                 labels: list = []
                 ) -> None:
        # -> Setup endpoint redis connection
        self.client = Redis()

        # ---- Initialise the node
        # -> Set id
        self.id = str(id(self))
        self.namespace = namespace
        self.labels = labels

        # -> Get comm_graph
        self.comm_graph = "Comm_graph"

        if self.namespace != "":
            self.comm_graph = self.get_topic(topic_elements=[namespace, self.comm_graph])

        # -> Initialise ref if it does not exist
        if ref is not None:
            # -> Set ref
            self.ref = ref

        elif not hasattr(self, "ref"):
            # -> Generate a random ref
            self.ref = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])

        # -. Generate node address
        self.address = self.get_topic(topic_elements=[self.ref])

        # -> Declare node
        self.declared_node = False

        with Lock(redis_client=self.client, name=self.comm_graph):
            if not self.client.exists(self.comm_graph):
                # -> Create comm_graph shared variable
                self.client.json().set(self.comm_graph, "$", {f"{self.address}": []})

            else:
                # -> Get comm_graph shared variable
                comm_graph = self.client.json().get(self.comm_graph)

                # -> Add node to comm_graph
                comm_graph[f"{self.address}"] = []

                # -> Update comm_graph shared variable
                self.client.json().set(self.comm_graph, "$",  comm_graph)

            # ======================== Redis graph
            # -> Get pubsub graph
            redis_graph = Graph(client=self.client, name="ROS_graph")

            # -> Add node
            new_node = Redis_node(
                label=["node"] + self.labels,
                properties={
                    "name": self.address,
                    "pyROS_id": self.id,
                    "ref": self.ref,
                    "namespace": self.namespace
                }
            )

            redis_graph.add_node(node=new_node)
            redis_graph.commit()

        self.declared_node = True

        # -> Initialise the node dictionary
        self._node_dict = {
            "async_timers": {},
        }

        # -> Initialise pointers
        self.threaded_spin = None
        self.spin_rate = 0.01

        # -> Initialise the node callbackgroups dictionary
        self.callbackgroups = {
            # Core
            "default_publisher_callback_group": ReentrantCallbackGroup(name="default_publisher_callback_group"),
            "default_subscriber_callback_group": MutuallyExclusiveCallbackGroup(name="default_subscriber_callback_group"),
            "default_shared_variable_callback_group": ReentrantCallbackGroup(name="default_shared_variable_callback_group"),
            "default_timer_callback_group": ReentrantCallbackGroup(name="default_timer_callback_group"),

            # Custom
            "ros_callback_group": ReentrantCallbackGroup(name="ros_callback_group"),
        }

        # -> Setup node messaging basis
        # -> Spin control variable
        self.spin_state = self.declare_shared_variable(
            name=f"spin_state",
            value=False,
            descriptor=f"Spin_state variable for node {self.ref}. Can be used to spin/stop node spin",
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
        Timer_module.__init__(self)

        # Custom
        # ROS_publisher_module.__init__(self)
        # ROS_subscriber_module.__init__(self)

    # ================================================================== Spin logics
    def spin(self,
             spin_rate: float = 0.01,
             condition: Shared_variable = None,
             threaded: bool = False,
             ) -> None:
        """
        Spin the node until the condition is met or until default spin condition is False.
        If no condition is given, spin until default spin condition is False.
        If threaded is True, spin in a separate thread.
        -> Unlike with ROS, publishers/control variables/parameters do not need to be spun if instant is set to True.

        ROS2 compatibility note:
        - condition cannot be used
        - threaded cannot be used

        :param spin_rate: The rate rate at which to spin the node
        :param condition: A function that returns True or False. A condition must contain a control variable
        :param threaded: If True, spin in a separate thread.
        """
        if not self.spin_state.get_value(spin=True):
            with Lock(redis_client=self.client, name=self.ref):
                # -> Reset spin control variable
                self.spin_state.set_value(value=True, instant=True)

            # -> Set spin rate
            self.spin_rate = spin_rate

            # ----- Condition provided
            # -> If threaded is True and condition is given
            if threaded and condition is not None:
                self.threaded_spin = Thread(target=self.__conditional_spin, args=(condition,))
                self.threaded_spin.start()

            # -> If threaded is False and condition is given
            elif condition is not None:
                self.__conditional_spin(spin_condition=condition)

            # ----- No condition provided
            # -> If threaded is True and no condition is given
            elif threaded:
                self.threaded_spin = Thread(target=self.__unconditional_spin)
                self.threaded_spin.start()

            # -> If threaded is False and no condition is given
            else:
                self.__unconditional_spin()

        else:
            print(f"!!! Node {self.ref} is already spinning !!!")

    def __unconditional_spin(self):
        """
        Spin while the condition is met.
        """
        spin_timer = self.create_async_timer(
            timer_period_sec=self.spin_rate,
            callback=self.spin_once,
            ref=self.ref + "_spin_timer"
            )

        # -> Start all timers
        for timer in self.async_timers.values():
            timer.start()

        while self.spin_state.get_value(spin=True):
            pass

        # -> Stop all timers
        for timer in self.timers.values():
            timer.cancel()
        
        self.destroy_timer(timer=spin_timer)

    def __conditional_spin(self, spin_condition):
        """
        Spin while the condition is met.
        """
        # -> Create spin timer
        spin_timer = self.create_async_timer(
            timer_period_sec=1/self.spin_rate, 
            callback=self.spin_once
            )
        
        # -> Start all timers
        for timer in self.async_timers.values():
            timer.start()
        
        # -> Check for kill condition
        while spin_condition.get_value() and self.spin_state.get_value(spin=True):
            pass
        
        # -> Stop all timers
        for timer in self.timers.values():
            timer.cancel()
        
        # -> Destroy spin timer
        self.destroy_timer(timer=spin_timer)

    def spin_once(self) -> None:
        """
        For every callback group, call the callbacks in a reentrant way.
        """
        # -> Create a thread pool
        with ThreadPoolExecutor(max_workers=100) as executor:
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
                    self.undeclare_shared_variable(shared_variable=callback)

        # -> Destroy every timer in the node
        timer_lst = self._node_dict["async_timers"]
        for timer in timer_lst:
            self.destroy_timer(timer=timer)

        # -> Remove node from comm graph
        with Lock(redis_client=self.client, name=self.comm_graph):
            # -> Get comm_graph shared variable
            comm_graph = self.client.json().get(self.comm_graph)

            # -> Delete node entry from comm_graph
            del comm_graph[f"{self.address}"]

            # -> Update comm_graph shared variable
            self.client.json().set(self.comm_graph, "$",  comm_graph)

            # ======================== Redis graph
            # -> Get pubsub graph
            redis_graph = Graph(client=self.client, name="ROS_graph")

            # -> Delete node
            query = f"MATCH (n:node) WHERE n.name = '{self.address}' DELETE n"
            redis_graph.query(query)

    # ================================================================== Misc
    # ---------------------------------------------- Timer
    @property
    def async_timers(self):
        """
        Get timers that have been created on this node.
        """

        # -> Return the list of timers
        return self._node_dict["async_timers"]

    # ----------------- Factory
    def create_async_timer(self,
                     timer_period_sec: float,
                     callback,
                     ref: str = None
                     ) -> Async_timer:
        """
        Create a timer that calls the callback function at the given rate.

        :param timer_period_sec: The period (s) of the timer.
        :param callback: A user-defined callback function that is called when the timer expires.
        """

        # -> Create a timer
        new_timer = Async_timer(
            timer_period=timer_period_sec,
            callback=callback,
            ref=ref
            )

        # -> Start the timer
        # new_timer.start()

        # -> Add the timer to the node dictionary timers
        self._node_dict["async_timers"][new_timer.ref] = new_timer

        # -> Return the timer object
        return new_timer

    # ----------------- Destroyer
    def destroy_async_timer(self, timer: Async_timer) -> None:
        """
        Destroy the given timer.
        """

        # -> Stop the timer
        timer.cancel()

        # -> Remove the timer from the node dictionary timers
        del self._node_dict["async_timers"][timer.ref]

    @staticmethod
    def get_topic(topic_elements: list):
        topic = "/"

        for topic_element in topic_elements:
            topic += f"{topic_element}/"

        return topic[:-1] 

    def __del__(self):
        if self.declared_node:
            self.destroy_node()
