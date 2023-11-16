from sim.data.cmd.sim_cmd import SimCmd
import sqlite3


class SimCmdHistory:
    def __init__(self):
        self._history = []

        self._db = sqlite3.connect("commands.simlog")
        self._db.execute("TABLE")

    def __rshift__(self, other: SimCmd):
        self._history.append(other)
        self._db
