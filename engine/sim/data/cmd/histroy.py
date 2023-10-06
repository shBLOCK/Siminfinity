from sim.data.cmd.cmd import Cmd
import sqlite3


class CmdHistory:
    def __init__(self):
        self.cmd_list = []
