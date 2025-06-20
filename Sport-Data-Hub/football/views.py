from django.shortcuts import render
from .utils import getTeamPastMatchesFromDB, getScheduledMatches
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse

# Create your views here.

@api_view(['GET'])
def returnScheduledMatches(request, day):

    # Check if day is within the valid range (0-7)
    try:
        day = int(day)
        if day < 0 or day > 7:
            raise ValueError("Day value must be between 0 and 7.")
            
    except ValueError:
        return Response({'error': 'Invalid day value. Day must be an integer between 0 and 7.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(getScheduledMatches(day))


@api_view(['GET'])
def getTeamPastMatches(request):
    team_name = request.GET.get('team')
    country = request.GET.get('country')
    if not team_name or not country:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    return Response(getTeamPastMatchesFromDB(team_name, country))
