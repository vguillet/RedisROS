import json
from datetime import datetime

from redis_lock import Lock

from dep.pyROS.src.pyROS.Endpoints.Endpoint import Endpoint


class Publisher(Endpoint):
    def __init__(self,
                 topic: str,
                 msg_type: str = "Unspecified",
                 qos_profile=None,
                 parent_node_ref: str = None,
                 ):
        """
        Create a publisher endpoint for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param qos_profile: The QoS profile to use

        :param parent_node_ref: The reference of the parent node
        """

        # -> Initialise the publisher properties
        self.msg_type = msg_type
        self.topic = self.check_topic(topic=topic)
        self.qos_profile = qos_profile

        # -> Initialise the publisher's cache
        self.cache = []

        # -> Setup endpoint
        Endpoint.__init__(self, parent_node_ref=parent_node_ref)

        # -> Declare the endpoint in the comm graph
        self.declare_endpoint()

    def __build_msg(self, msg) -> dict:
        # -> Add message metadata
        msg = {
            "timestamp": datetime.timestamp(datetime.now()),
            "msg_type": self.msg_type,
            "parent_node_ref": self.parent_node_ref,
            "publisher_ref": self.ref,
            "msg": msg
        }

        return msg

    def spin(self) -> None:
        """
        Publish the messages in the cache to the topic
        """

        for msg in self.cache:
            self.client.publish(self.topic, json.dumps(msg))

        # -> Clear the cache
        self.cache = []

    def publish(self,
                msg,
                instant: bool = True) -> None:
        """
        Publish the given message to the topic.
        If instant is True, the message will be published immediately, otherwise it will be published at the next spin

        ROS2 compatibility note:
        - Instant publishing is not supported

        :param msg: The message to publish
        :param instant: Whether to publish the message instantly or to cache it
        """

        # -> Add message metadata
        msg = self.__build_msg(msg=msg)

        # -> Publish the message
        if instant:
            self.client.publish(self.topic, json.dumps(msg))

        else:
            # -> Add the msg to the cache of messages to publish
            self.cache.append(msg)

    def declare_endpoint(self) -> None:
        with Lock(redis_client=self.client, name="Comm_graph"):
            # -> Get the communication graph from the redis server
            comm_graph = json.loads(self.client.get("Comm_graph"))

            # -> Declare the endpoint in the parent node
            comm_graph[self.parent_node_ref].append(
                {"ref": self.ref,
                 "type": "publisher",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Update comm_graph shared variable
            self.client.set("Comm_graph", json.dumps(comm_graph))

    def destroy_endpoint(self) -> None:
        with Lock(redis_client=self.client, name="Comm_graph"):
            # -> Get the communication graph from the redis server
            comm_graph = json.loads(self.client.get("Comm_graph"))

            # -> Undeclare the endpoint in the parent node
            comm_graph[self.parent_node_ref].remove(
                {"ref": self.ref,
                 "type": "publisher",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Update comm_graph shared variable
            self.client.set("Comm_graph", json.dumps(comm_graph))
