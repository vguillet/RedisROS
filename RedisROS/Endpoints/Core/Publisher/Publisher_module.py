
from RedisROS.Endpoints import Publisher
from RedisROS.Callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup


class Publisher_module:
    def __init__(self):
        pass

    @property
    def publishers(self):
        """
        Get publishers that have been created on this node in every callback groups.
        """
        # -> Get all the publishers in every callback group
        publishers = []

        for callback_group in self.callbackgroups.values():
            for callback in callback_group.callbacks:
                if isinstance(callback, Publisher):
                    publishers.append(callback)

        # -> Return the list of publishers
        return publishers

    # ----------------- Factory
    def create_publisher(self,
                         msg_type,
                         topic: str,
                         qos_profile=None,
                         callback_group: MutuallyExclusiveCallbackGroup or ReentrantCallbackGroup = None
                         ) -> Publisher:
        """
        Create a publisher for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param qos_profile: The QoS profile to use
        :param callback_group: The callback group for the publisher. If None, use the default publisher callback group is used.
        """

        # -> Create a publisher for the given topic
        new_publisher = Publisher(
            msg_type=msg_type,
            topic=topic,
            qos_profile=qos_profile,
            parent_node_ref=self.ref,
            namespace=self.namespace
        )

        # -> If not callback group is given, use the default publisher callback group
        if callback_group is None:
            self.callbackgroups["default_publisher_callback_group"].add_callback(new_publisher)
        else:
            callback_group.add_callback(new_publisher)

        # -> Return the publisher object
        return new_publisher

    # ----------------- Destroyer
    def destroy_publisher(self, publisher: Publisher) -> None:
        """
        Destroy the given publisher.
        """
        # -> Destroy publisher endpoint
        publisher.destroy_endpoint()

        # -> Remove the publisher from its callback group
        for callback_group in self.callbackgroups.values():
            if callback_group.has_entity(publisher):
                callback_group.remove_callback(publisher)
                break
