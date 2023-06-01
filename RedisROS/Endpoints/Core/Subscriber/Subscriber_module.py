
from RedisROS.Endpoints import Subscriber
from RedisROS.Callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup


class Subscriber_module:
    def __init__(self):
        pass

    @property
    def subscriptions(self):
        """
        Get subscriptions that have been created on this node in every callback groups.
        """
        # -> Get all the subscriptions in every callback group
        subscriptions = []

        for callback_group in self.callbackgroups.values():
            for callback in callback_group.callbacks:
                if isinstance(callback, Subscriber):
                    subscriptions.append(callback)
                    
        # -> Return the list of subscriptions
        return subscriptions

    # ----------------- Factory
    def create_subscription(self,
                            msg_type,
                            topic: str,
                            callback,
                            qos_profile=None,
                            callback_group: MutuallyExclusiveCallbackGroup or ReentrantCallbackGroup = None) -> Subscriber:
        """
        Create a subscription for the given topic.
        Call the callback function when a message is received.

        :param msg_type: The type of the message to be received.
        :param topic: The topic to subscribe to.
        :param callback: The callback function to call when a message is received.
        :param qos_profile: The QoS profile to use.
        :param callback_group: The callback group for the subscription. If None, the default callback group is used.
        """

        # -> Create a subscription for the given topic
        new_subscription = Subscriber(
            msg_type=msg_type,
            topic=topic,
            callback=callback,
            qos_profile=qos_profile,
            parent_node_ref=self.ref,
            namespace=self.namespace
            )

        # -> If not callback group is given, use the default publisher callback group
        if callback_group is None:
            self.callbackgroups["default_subscriber_callback_group"].add_callback(new_subscription)
        else:
            callback_group.add_callback(new_subscription)

        # -> Return the subscription object
        return new_subscription

    # ----------------- Destroyer
    def destroy_subscription(self, subscriber: Subscriber) -> None:
        """
        Destroy the given subscriber.
        """

        # -> Destroy subscriber endpoint
        subscriber.destroy_endpoint()

        # -> Remove the subscriber from the corresponding callback group
        for callback_group in self.callbackgroups.values():
            if callback_group.has_entity(subscriber):
                callback_group.remove_callback(subscriber)
                break