
from abc import ABC, abstractmethod
import random
import string

from redis import Redis


class Endpoint(ABC):
    def __init__(self,
                 parent_node_ref: str,
                 namespace: str = ""
                 ):
        """
        The base class for all endpoints

        :param parent_node_ref: The reference of the parent node
        """

        # -> Generate a unique ID for the subscriber
        self.id = str(id(self))

        # -> Set the parent node reference
        self.parent_node_ref = parent_node_ref
        self.parent_address = self.get_topic(topic_elements=[parent_node_ref])

        # -> Set namespace/comm graph
        self.namespace = namespace

        # -> Get comm_graph
        self.comm_graph = "Comm_graph"

        if self.namespace != "":
            self.comm_graph = self.get_topic(topic_elements=[namespace, self.comm_graph])

        # -> Setup endpoint redis connection
        self.client = Redis(client_name=self.id)

    @staticmethod
    def get_topic(topic_elements: list):
        topic = "/"

        for topic_element in topic_elements:
            topic += f"{topic_element}/"

        if topic[0] == topic[1] and topic[0]:   # TODO: Fix to also check for if == \
            topic = topic[1:]

        return topic[:-1] 

    @staticmethod
    def check_topic(topic):
        """
        Check if the given topic is in the correct format
        """

        # -> Check if topic starts with /
        if topic[0] != "/":
            raise ValueError(f"Topic must start with '/', current topic: {topic}")

        else:
            return topic

    @abstractmethod
    def spin(self) -> None:
        pass

    @abstractmethod
    def declare_endpoint(self) -> None:
        pass

    def destroy_endpoint(self) -> None:
        pass
