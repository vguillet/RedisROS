
from RedisROS.Endpoints import Publisher


class ROS_publisher_module:
    def __init__(self):
        pass

    @property
    def ros_publishers(self) -> list[Publisher]:
        """
        Get ros publishers that have been created on this node in ros callback groups.
        """

        return self.callbackgroups["ros_callback_group"].get_publishers()

    # ----------------- Factory
    def create_ros_publisher(self,
                             msg_type,
                             topic: str,
                             qos_profile=None) -> Publisher:
        """
        Create a ros publisher for the given topic

        :param msg_type: The type of the message to be published
        :param topic: The topic to publish to
        :param qos_profile: The QoS profile to use
        """

        # -> Create a publisher for the given topic
        new_publisher = Publisher(
            msg_type=msg_type,
            topic=self.namespace + topic,
            qos_profile=qos_profile,
            parent_node_ref=self.ref,
            comms_structure=self._comms_structure,
            comms_msgs=self._comms_msgs)

        # -> Add the publisher to the ros callback group
        self.callbackgroups["ros_callback_group"].add_callback(new_publisher)

        # -> Publish the ros publisher creation msg
        self.framework_msgs.publish(
            msg={
                "Source": self.ref,
                "Type": "ROS_Publisher_Creation",
                "Memo": {
                    "Topic": topic,
                }
            }
        )

        # -> Return the publisher object
        return new_publisher

    # ----------------- Destroyer
    def destroy_ros_publisher(self, publisher: Publisher) -> None:
        """
        Destroy the given publisher.
        """
        # -> Destroy publisher endpoint
        publisher.destroy_endpoint()

        # -> Publish the ros publisher destruction msg
        self.framework_msgs.publish(
            msg={
                "Source": self.ref,
                "Type": "ROS_Publisher_Destruction",
                "Memo": {
                    "Topic": publisher.topic,
                }
            }
        )

        # -> Remove the publisher from its callback group
        try:
            self.callbackgroups["ros_callback_group"].remove_callback(publisher)
        except:
            print("Error: Publisher not found in ros callback group")
