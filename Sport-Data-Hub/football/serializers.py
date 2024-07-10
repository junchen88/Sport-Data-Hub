from django.contrib.auth.models import Group, User
from rest_framework import serializers

from rest_framework import serializers # Import the serializer class
from .models import Team, Player, Match, PlayerStats  # Import the Note model

# Create a serializer class
# This class will convert the Team model into JSON
class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

# This class will convert the Player model into JSON
class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

# This class will convert the Match model into JSON
class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

# This class will convert the PlayerStats model into JSON
class PlayerStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerStats
        exclude = ('match',)  # Exclude the 'match' field from serialization

