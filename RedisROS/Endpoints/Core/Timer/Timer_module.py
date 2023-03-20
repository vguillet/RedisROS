
from RedisROS.Endpoints import Timer
from RedisROS.Callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup


class Timer_module:
    def __init__(self):
        pass
    
    @property
    def timers(self):
        """
        Get timers that have been created on this node in every callback groups.
        """
        # -> Get all the timers in every callback group
        timers = []

        for callback_group in self.callbackgroups.values():
            for callback in callback_group.callbacks:
                if isinstance(callback, Timer):
                    timers.append(callback)

        # -> Return the list of timers
        return timers  

    def create_timer(self,
                    timer_period_sec: float,
                    callback,
                    ref: str = None,
                    callback_group: MutuallyExclusiveCallbackGroup or ReentrantCallbackGroup = None
                    ) -> Timer:
        """
        Create a timer that calls the callback function at the given rate.

        :param timer_period_sec: The period (s) of the timer.
        :param callback: A user-defined callback function that is called when the timer expires.
        """

        # -> Create a timer
        new_timer = Timer(
            timer_period=timer_period_sec,
            callback=callback,
            ref=ref
            )

        # -> Add the timer to the node dictionary timers
        if callback_group is None:
            self.callbackgroups["default_timer_callback_group"].add_callback(new_timer)
        else:
            callback_group.add_callback(new_timer)

        # -> Return the timer object
        return new_timer
    
    # ----------------- Destroyer
    def destroy_timer(self, timer: Timer) -> None:
        """
        Destroy the given timer.
        """
        # -> Destroy timer endpoint
        timer.destroy_endpoint()

        # -> Remove the timer from its callback group
        for callback_group in self.callbackgroups.values():
            if callback_group.has_entity(timer):
                callback_group.remove_callback(timer)
                break