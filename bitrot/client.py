from .networking import Networking
from .engine import Match


class Client:
    def __init__(self, network: Networking):
        self.network = network
