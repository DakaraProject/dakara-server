from rest_framework import serializers
from library.models import Song, Artist, Work, SongWorkLink, WorkType, SongTag


class SecondsDurationField(serializers.DurationField):
    """ Field that displays only seconds
    """

    def to_representation(self, obj):
        """ Method for serializing duration in right format
        """
        return str(int(round(obj.total_seconds())))


class ArtistNoCountSerializer(serializers.ModelSerializer):

    """ Class for artist serializer
        Only contains name
        Used in song representation
    """
    class Meta:
        model = Artist
        fields = (
                'id',
                'name',
                )


class ArtistSerializer(serializers.ModelSerializer):
    """ Class for artist serializer
        Including a song count
        Used in artists listing
    """
    song_count =  serializers.SerializerMethodField()
    class Meta:
        model = Artist
        fields = (
                'id',
                'name',
                'song_count'
                )

    def get_song_count(self, artist):
        return Song.objects.filter(artists=artist).count()


class WorkTypeSerializer(serializers.ModelSerializer):
    """ Class for work type serializer
    """
    class Meta:
        model = WorkType 
        fields = (
                'name',
                'query_name',
                'icon_name'
                )


class WorkNoCountSerializer(serializers.ModelSerializer):
    """ Class for work serializer
    """
    work_type = WorkTypeSerializer(many=False, read_only=True)
    class Meta:
        model = Work
        fields = (
                'id',
                'title',
                'subtitle',
                'work_type'
                )

class WorkSerializer(serializers.ModelSerializer):
    """ Class for work serializer
    """
    work_type = WorkTypeSerializer(many=False, read_only=True)
    song_count =  serializers.SerializerMethodField()
    class Meta:
        model = Work
        fields = (
                'id',
                'title',
                'subtitle',
                'work_type',
                'song_count'
                )

    def get_song_count(self, work):
        return Song.objects.filter(works=work).count()


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """ Class for serializing the use of a song in a work
    """
    work = WorkNoCountSerializer(many=False, read_only=True)
    link_type_name = serializers.SerializerMethodField()

    class Meta:
        model = SongWorkLink
        fields = (
                'work',
                'link_type',
                'link_type_name',
                'link_type_number',
                'episodes',
                )

    def get_link_type_name(self, song_work_link):
        link_type_name = [ 
                choice[1] 
                for choice in SongWorkLink.LINK_TYPE_CHOICES 
                if choice[0] == song_work_link.link_type
                ]
        if len(link_type_name) < 1:
            return song_work_link.link_type 

        return link_type_name[0]

class SongTagSerializer(serializers.ModelSerializer):
    """ Class for song tags serializer
    """
    class Meta:
        model = SongTag
        fields = (
                'name',
                'color_id',
                )


class SongSerializer(serializers.ModelSerializer):
    """ Class for song serializer
    """
    duration = SecondsDurationField()
    artists = ArtistNoCountSerializer(many=True, read_only=True)
    tags = SongTagSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True, source='songworklink_set')

    class Meta:
        model = Song
        fields = (
                'id',
                'title',
                'file_path',
                'duration',
                'version',
                'detail',
                'detail_video',
                'tags',
                'artists',
                'works',
                'date_created',
                'date_updated',
                )


class SongForPlayerSerializer(serializers.ModelSerializer):
    """ Class for song serializer, to be used by the player
    """
    artists = ArtistNoCountSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True, source='songworklink_set')
    class Meta:
        model = Song
        fields = (
                'title',
                'artists',
                'works',
                'file_path',
                )
