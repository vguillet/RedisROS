import json
from datetime import datetime

from redis.commands.graph import Graph, Edge, Node
from redis_lock import Lock

from dep.pyROS.src.pyROS.Endpoints.Endpoint import Endpoint


class Publisher(Endpoint):
    def __init__(self,
                 topic: str,
                 msg_type: str = "Unspecified",
                 qos_profile=None,
                 parent_node_ref: str = None,
                 namespace: str = ""
                 ) -> None:
        """
        Create a publisher endpoint for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param qos_profile: The QoS profile to use

        :param parent_node_ref: The reference of the parent node
        """

        # -> Initialise the publisher properties
        self.msg_type = msg_type
        self.topic = self.get_topic(topic_elements=[topic])
        self.qos_profile = qos_profile

        # -> Initialise the publisher's cache
        self.cache = []

        # -> Setup endpoint
        Endpoint.__init__(self, 
                          parent_node_ref=parent_node_ref,
                          namespace=namespace)

        # -> Declare the endpoint in the comm graph
        self.declare_endpoint()

    def __build_msg(self, msg) -> dict:
        # -> Add message metadata
        msg = {
            "timestamp": datetime.timestamp(datetime.now()),
            "msg_type": self.msg_type,
            "parent_node_ref": self.parent_node_ref,
            "publisher_id": self.id,
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
        with Lock(redis_client=self.client, name=self.comm_graph):
            # -> Get the communication graph from the redis server
            comm_graph = self.client.json().get(self.comm_graph)

            # -> Declare the endpoint in the parent node
            comm_graph[self.parent_address].append(
                {"id": self.id,
                 "type": "publisher",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Update comm_graph shared variable
            self.client.json().set(self.comm_graph, "$",  comm_graph)

            # ======================== Redis graph declaration
            # -> Add edge in redis graph
            redis_graph = Graph(client=self.client, name="ROS_graph")

            # -> Check if topic node is in graph
            query = "MATCH (n:topic {name: '%s'}) RETURN n" % (self.topic)
            topic_node = redis_graph.query(query).result_set

            # -> Get topic node
            if len(topic_node) == 0:    # if it does not exist
                # -> Create topic node
                topic_node = Node(
                    label="topic",
                    properties={
                        "name": self.topic,
                        "pyROS_id": self.id,
                        "msg_type": str(self.msg_type),
                        "namespace": self.namespace
                    }
                )

                # -> Add to graph
                redis_graph.add_node(node=topic_node)
                redis_graph.commit()

            # -> Create relationship
            edge_properties = "{" + f"namespace: '{self.namespace}', msg_type: '{str(self.msg_type)}', qos_profile: '{str(self.qos_profile)}'" + "}"

            query = f"MATCH (p:node), (t:topic) WHERE p.name = '{self.parent_address}' AND t.name = '{self.topic}' CREATE (p)-[r:Publish {edge_properties}] -> (t) RETURN r"
            redis_graph.query(query)

    def destroy_endpoint(self) -> None:
        with Lock(redis_client=self.client, name=self.comm_graph):
            # -> Get the communication graph from the redis server
            comm_graph = self.client.json().get(self.comm_graph)

            # -> Undeclare the endpoint in the parent node
            comm_graph[self.parent_address].remove(
                {"id": self.id,
                 "type": "publisher",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Update comm_graph shared variable
            self.client.json().set(self.comm_graph, "$",  comm_graph)
