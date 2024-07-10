from django.shortcuts import render
from .utils import getPastFiveMatchesAndPlayersStats, getScheduledMatches
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
# Create your views here.

@api_view(['GET'])
def getScheduledMatches(request, day):

    # Check if day is within the valid range (0-7)
    try:
        day = int(day)
        if day < 0 or day > 7:
            raise ValueError("Day value must be between 0 and 7.")
            
    except ValueError:
        return Response({'error': 'Invalid day value. Day must be an integer between 0 and 7.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(getScheduledMatches(day))

# @api_view(['GET'])
# def get_last_5_matches_with_player_stats(request, team_name):
#     try:
#         team = get_object_or_404(Team, team_id=team_id)
#     except Team.DoesNotExist:
#         return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)
#
# getPastFiveMatchesAndPlayersStats(team_name, country):