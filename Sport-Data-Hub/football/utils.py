# This is the response that we will return
from rest_framework.response import Response
# This is the model that we will use
from .models import Team, Player, Match, PlayerStats
# This is the serializer that we will use
from .serializers import TeamSerializer, PlayerSerializer, MatchSerializer, PlayerStatsSerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q  # Import Q object for complex queries
from tool.DBHelper import DBHelper
from tool.getScheduledMatchData import getScheduledMatchStat
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='messages.log', encoding='utf-8', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

dbHelper = DBHelper(logger)
SCHEDULEDMATCHES = {}

def getPastFiveMatchesAndPlayersStats(team_name, country):
    team = get_object_or_404(Team, team_name=team_name, country=country)  
    teamID = team.team_id
    
    try:
        # Query the last 5 matches for the team
        last_5_matches = Match.objects.filter(Q(home_team_id=teamID) | Q(away_team_id=teamID)) \
                                    .order_by('-date')[:5]

        match_serializer = MatchSerializer(last_5_matches, many=True)
        serialized_matches = match_serializer.data
    except Exception as e:
        print(e)
        serialized_matches = []
    matches_with_stats = []

    # Fetch player stats for each match
    for match in last_5_matches:
        try:
            # Query player stats for the current match
            player_stats = PlayerStats.objects.filter(match=match)

            # Serialize player stats for the current match
            player_stats_serializer = PlayerStatsSerializer(player_stats, many=True)
            serialized_player_stats = player_stats_serializer.data
        except Exception as e:
            print(e)
            serialized_player_stats = []

        # Append match data along with player stats to the list
        matches_with_stats.append({
            'match': serialized_matches[last_5_matches.index(match)],
            'player_stats': serialized_player_stats
        })
    return matches_with_stats
    

def getScheduledMatches(day):
    global SCHEDULEDMATCHES
    # get matches based on date
    dateWanted = datetime.now() + timedelta(day)
    dateWanted = dateWanted.date()
    
    if not SCHEDULEDMATCHES:
        matches = getScheduledMatchStat(day)
        SCHEDULEDMATCHES = matches

    
    return SCHEDULEDMATCHES
