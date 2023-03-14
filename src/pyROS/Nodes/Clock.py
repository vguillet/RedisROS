

from dep.pyROS.src.pyROS.pyROS import PyROS

class Clock(PyROS):
    def __init__(self, namespace: str = "", ref: str = None):
        super().__init__(
            namespace=namespace, 
            ref=ref)