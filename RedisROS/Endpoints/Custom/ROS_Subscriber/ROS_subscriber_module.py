
from RedisROS.Endpoints import Subscriber


class ROS_subscriber_module:
    def __init__(self):
        pass

    @property
    def ros_subscribers(self) -> list[Subscriber]:
        """
        Get ros subscribers that have been created on this node in ros callback groups.
        """

        return self.callbackgroups["ros_callback_group"].get_subscribers()

    # ----------------- Factory
    def create_ros_subscriber(self,
                              msg_type,
                              topic: str,
                              qos_profile=None) -> Subscriber:
        """
        Create a ros subscriber for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param qos_profile: The QoS profile to use
        """

        # -> Create a subscriber for the given topic
        new_subscription = Subscriber(
            msg_type=msg_type,
            topic=self.namespace + topic,
            callback=callback,
            qos_profile=qos_profile,
            parent_node_ref=self.ref,
            comms_structure=self._comms_structure,
            comms_msgs=self._comms_msgs
            )

        # -> Add the subscriber to the ros callback group
        self.callbackgroups["ros_callback_group"].add_callback(new_subscription)

        # -> Publish the ros subscriber creation msg
        self.framework_msgs.publish(
            msg={
                "Source": self.ref,
                "Type": "ROS_Subscription_Creation",
                "Memo": {
                    "Topic": topic,
                }
            }
        )

        # -> Return the subscriber object
        return new_subscriber

    # ----------------- Destroyer
    def destroy_ros_subscriber(self, subscriber: Subscriber) -> None:
        """
        Destroy the given subscriber.
        """
        # -> Destroy subscriber endpoint
        subscriber.destroy_endpoint()

        # -> Publish the ros subscriber destruction msg
        self.framework_msgs.publish(
            msg={
                "Source": self.ref,
                "Type": "ROS_Subscription_Destruction",
                "Memo": {
                    "Topic": subscriber.topic,
                }
            }
        )

        # -> Remove the subscriber from its callback group
        try:
            self.callbackgroups["ros_callback_group"].remove_callback(subscriber)
        except:
            print("Error: Subscriber not found in ros callback group")
