class PlayerStatus(object):
    """ Class for status communication from the player to the server
    """

    def __init__(self, song_id, timing):
        self.song_id = song_id
        self.timing = timing

class PlayerCommand(object):
    """ Class for command communication from the server to the player
    """

    def __init__(self, pause, skip):
        self.pause = pause
        self.skip = skip
