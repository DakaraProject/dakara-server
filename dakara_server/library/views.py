from rest_framework.viewsets import ModelViewSet
from library.models import *
from library.serializers import *

class SongViewSet(ModelViewSet):
    """ Class for song query set
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
