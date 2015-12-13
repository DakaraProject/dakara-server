from rest_framework import viewsets
from library.models import *
from library.serializers import *

class SongViewSet(viewsets.ModelViewSet):
    """ Class for song query set
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
