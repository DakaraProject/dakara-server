def parse_file_name(file_name):
    """
    A simple parser used for test.
    Parse file name with the following pattern:
    "song_title - artist_name - work_title - tag"
    """

    song_title, artist_name, work_title, tag = file_name.split(" - ")
    return {
        "title_music": song_title,
        "version": "",
        "detail": "",
        "detail_video": "",
        "artists": [artist_name],
        "title_work": work_title,
        "subtitle_work": "",
        "work_type_query_name": "anime",
        "link_type": "OP",
        "tags": [tag],
    }
