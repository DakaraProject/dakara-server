class PlayerStatus(object):
    """ Class for status communication from the player to the server
    """

    def __init__(self, playlist_entry_id=0, timing=0):
        self.playlist_entry_id = playlist_entry_id
        self.timing = timing

class PlayerCommand(object):
    """ Class for command communication from the server to the player
    """

    def __init__(self, pause=False, skip=False):
        self.pause = pause
        self.skip = skip
