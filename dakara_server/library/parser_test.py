
def parse_file_name(file_name):
    """
    A simple parser used for test.
    Parse file name with the following pattern:
    "song_title - artist_name"
    """

    song_title, artist_name = file_name.split(' - ')
    return {
            'title_music': song_title,
            'version': '',
            'detail': '',
            'detail_video': '',
            'artists': [artist_name],
            }
