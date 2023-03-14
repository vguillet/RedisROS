import json

from redis_lock import Lock

from dep.pyROS.src.pyROS.Endpoints.Endpoint import Endpoint


class Subscriber(Endpoint):
    def __init__(self,
                 topic: str,
                 callback,
                 msg_type: str = "Unspecified",
                 qos_profile=None,
                 parent_node_ref: str = None,
                 namespace: str = ""
                 ) -> None:
        """
        Create a subscriber endpoint for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param callback: The callback function to call when a message is received
        :param qos_profile: The QoS profile to use

        :param parent_node_ref: The reference of the parent node
        """

        # -> Initialise the subscriber properties
        self.msg_type = msg_type
        self.topic = self.get_topic(topic_elements=[topic])
        self.callback = callback
        self.qos_profile = qos_profile

        # -> Setup endpoint
        Endpoint.__init__(self, 
                          parent_node_ref=parent_node_ref,
                          namespace=namespace)

        # -> Setup the subscriber's pubsub connection
        self.pubsub = self.client.pubsub(ignore_subscribe_messages=True)

        # -> Subscribe to the topic
        self.pubsub.subscribe(**{self.topic: self.__callback})

        # -> Declare the endpoint in the comm graph
        self.declare_endpoint()

    def spin(self) -> None:
        """
        Retrieve the message from the topic according to the subscriber's qos profile,
        and call the subscriber's callback function
        """

        self.pubsub.get_message()

    def __callback(self, raw_msg):
        # -> Convert raw message to dictionary
        raw_msg = json.loads(raw_msg["data"])

        # -> Call the subscriber's callback function
        
        # Attempt to provide both message and msg meta in callback
        try:
            self.callback(raw_msg["msg"], raw_msg)
        
        # Only provide msg
        except:
            self.callback(raw_msg["msg"])

    def declare_endpoint(self) -> None:
        with Lock(redis_client=self.client, name=self.comm_graph):
            # -> Get the communication graph from the redis server
            comm_graph = self.client.json().get(self.comm_graph)

            # -> Declare the endpoint in the parent node
            comm_graph[self.parent_address].append(
                {"id": self.id,
                 "type": "subscriber",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Update comm_graph shared variable
            self.client.json().set(self.comm_graph, "$",  comm_graph)

    def destroy_endpoint(self) -> None:
        with Lock(redis_client=self.client, name=self.comm_graph):
            # -> Get the communication graph from the redis server
            comm_graph = self.client.json().get(self.comm_graph)

            # -> Undeclare the endpoint in the parent node
            comm_graph[self.parent_address].remove(
                {"id": self.id,
                 "type": "subscriber",
                 "msg_type": self.msg_type,
                 "topic": self.topic}
            )

            # -> Unsubscribe the end point from the topic
            self.pubsub.unsubscribe()

            # -> Update comm_graph shared variable
            self.client.json().set(self.comm_graph, "$",  comm_graph)

    @staticmethod
    def get_topic(topic_elements: list):
        topic = "/"

        for topic_element in topic_elements:
            topic += f"{topic_element}/"

        return topic[:-1] 