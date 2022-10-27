from concurrent.futures import ThreadPoolExecutor


class CallbackGroup:
    def __init__(self, name: str = ""):
        """
        Initialise the callback group

        :param name: The name of the callback group
        """

        # -> Initialise the callback group properties
        self.name = name
        self.callbacks = []

    def add_callback(self, callback):
        """
        Add a callback to the callback group
        """
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        """
        Remove a callback from the callback group
        """
        self.callbacks.remove(callback)

    def has_entity(self, callback):
        """
        Check if the given callback belongs to the callback group
        """
        if callback in self.callbacks:
            return True
        else:
            return False

    def get_entities(self, entity_type):
        """
        Get all the entities in the callback group of the given type
        """
        publishers = []
        for callback in self.callbacks:
            if isinstance(callback, entity_type):
                publishers.append(callback)
        return publishers


class MutuallyExclusiveCallbackGroup(CallbackGroup):
    def __init__(self, name: str = ""):
        CallbackGroup.__init__(self, name=name)

    def spin(self) -> None:
        """
        Spin the callbacks in the callback group in order
        """

        for callback in self.callbacks:
            callback.spin()


class ReentrantCallbackGroup(CallbackGroup):
    def __init__(self, name: str = ""):
        CallbackGroup.__init__(self, name=name)

    def spin(self) -> None:
        """
        Spin the callbacks in the callback group in threads
        """

        # -> Create a thread pool
        with ThreadPoolExecutor(max_workers=worker_pool_size) as executor:
            # -> Call the callbacks in the callback group in threads
            for callback in self.callbacks:
                executor.submit(callback.spin)
