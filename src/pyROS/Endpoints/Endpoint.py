
from abc import ABC, abstractmethod
import random
import string

from redis import Redis


class Endpoint(ABC):
    def __init__(self,
                 parent_node_ref: str
                 ):
        """
        The base class for all endpoints

        :param parent_node_ref: The reference of the parent node
        """

        # -> Generate a unique ID for the subscriber
        self.ref = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])

        # -> Set the parent node reference
        self.parent_node_ref = "/" + parent_node_ref

        # -> Setup endpoint redis connection
        self.client = Redis(client_name=self.ref)

    @staticmethod
    def check_topic(topic):
        """
        Check if the given topic is in the correct format
        """

        # -> Check if topic starts with /
        if topic[0] != "/":
            raise ValueError("Topic must start with '/'")

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
