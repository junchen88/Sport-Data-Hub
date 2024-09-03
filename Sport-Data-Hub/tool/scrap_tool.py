import re
from datetime import datetime, timedelta
from time import localtime, strftime
import json
import os
from requests_html import HTMLSession, AsyncHTMLSession
from tqdm.asyncio import tqdm as async_tqdm
import asyncio
import webbrowser
import logging

# Dictionary mapping status codes to messages
STATUS_MESSAGES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}
MAXSTARTINGPLAYER = 11
SENTINELBIRTHEPOCH = -2208988800 # represents 1900-01-01

class Scraper():
    def __init__(self, logger:logging.Logger) -> None:
        self.session            = HTMLSession()
        self.APIURL             = "https://www.sofascore.com/api/v1/"
        self.SCHEDULEMATCHURL   = f"{self.APIURL}sport/football/scheduled-events/"
        self.EVENTURL           = f"{self.APIURL}event/"
        self.TEAMURL            = f"{self.APIURL}team/"
        self.PLAYERURL          = f"{self.APIURL}player/"
        self.logger = logger

    def getLatestFinishedMatch(self, teamID):
        """
        Returns the latest finished match information for database check.
        """
        pastMatchURL = self.TEAMURL + str(teamID) + "/events/last/0"

        pass

    def findMatchWithPlayerStat(self, matchJsonData, matchIDs, teamName=None, numberOfMatchesWithData=None):
        """
        Determine whether the given match matchJsonData has
        player statistics. If it has the stats, then information
        regarding the match will be appended into matchIDs

        Parameters:
            - matchJsonData: JSON data containing information regarding the match
            - matchIDs: dict of dict, team name as key and another dict as its value
            - teamName (or None): the football team name
            - numberOfMatchesWithData (or None): counter for keeping the number of past matches with player stats appended

        Returns:
            - numberOfMatchesWithData (or None): counter for keeping the number of past matches with player stats appended
        """
        try:

            if matchJsonData["status"]["type"] == "finished" and "isAwarded" not in matchJsonData.keys():
                matchInfo = {
                    'customId': matchJsonData['customId'], 
                    'id': str(matchJsonData['id']), 
                    'slug': matchJsonData["slug"], 
                    'home': matchJsonData['homeTeam']['name'], 
                    'away': matchJsonData['awayTeam']['name'],
                    'home_id':matchJsonData['homeTeam']['id'], 
                    'away_id':matchJsonData['awayTeam']['id'],
                    'startTimestamp': matchJsonData["startTimestamp"],
                    'league': matchJsonData["tournament"]["name"],
                    "home_country": matchJsonData['homeTeam']['country']['name'],
                    "away_country": matchJsonData['awayTeam']['country']['name']

                }

                if "hasEventPlayerStatistics" in matchJsonData.keys():
                    if matchJsonData["hasEventPlayerStatistics"] == True:
                        matchInfo["hasPlayerStats"] = True
                    else:
                        matchInfo["hasPlayerStats"] = False
                    
                elif matchJsonData['tournament']['uniqueTournament']['hasEventPlayerStatistics'] == True:
                    matchInfo["hasPlayerStats"] = True
                else:
                    matchInfo["hasPlayerStats"] = False
    
                if matchInfo["hasPlayerStats"] == True:

                    if teamName:
                        matchIDs[teamName].append(matchInfo)
                        numberOfMatchesWithData += 1
                    else:
                        matchIDs.append(matchInfo)
                
            return numberOfMatchesWithData

        except KeyError as e:
            # print(e, "Player stat is not available")  
            # don't append the current match info into matchIDs
            self.logger.error(f"matchID : {matchJsonData['id']}, KeyError: {e}")

            return numberOfMatchesWithData 

        except Exception as e:
            # log instead
            self.logger.error(f"matchID : {matchJsonData['id']}, {e}")
            # don't append the current match info into matchIDs
            return numberOfMatchesWithData


    async def getPast5Matches(self, asession, teamID, teamName, matchIDs, pageNum):
        """
        If database doesn't have the latest H2H match, it will need to call this function to
        get the latest 5 h2h data
        """
        # init dict to store result
        if matchIDs is None:
            matchIDs = {teamName:[]}

        pastMatchURL = self.TEAMURL + str(teamID) + f"/events/last/{pageNum}"
        response = await asession.get(pastMatchURL, stream=True)
        # check for request status
        if response.status_code != 200:
            # log instead!
            try:
                self.logger.error(f"failed to obtain past 5 matches data for team {pastMatchURL}: {response.status_code} {STATUS_MESSAGES[response.status_code]}")
            except:
                self.logger.error(f"failed to obtain past 5 matches data for team {pastMatchURL}: {response.status_code}")

            return {}
        dataJson = response.json()
        
        numberOfMatchesWithData = 0
        
        if len(dataJson["events"]) >= 5:
            # -6 since we want 5 results as range stops at target-1
            # latest result is at page 0 and at the end
            for i in range(len(dataJson["events"])-1, -1, -1):
                match = dataJson["events"][i]
                if "status" in match.keys():
                    numberOfMatchesWithData = self.findMatchWithPlayerStat(match, matchIDs, teamName, numberOfMatchesWithData)
                
                if numberOfMatchesWithData >= 5:
                    
                    break #stop loop if we got at least 5 data


        
        # go to the next page and get more data if possible
        if numberOfMatchesWithData < 5 and dataJson.get("hasNextPage", False):
            pageNum += 1
            await self.getPast5Matches(asession, teamID, teamName, matchIDs, pageNum)
        
        return matchIDs


    def findScheduledMatchWithPlayerStats(self, matchJsonData, matchIDs):
        if "status" in matchJsonData.keys():
            if matchJsonData["status"]["type"] == "notstarted" and "isAwarded" not in matchJsonData.keys():

                if matchJsonData['tournament']['uniqueTournament']['hasEventPlayerStatistics'] == True:
                    matchInfo = {
                        'customId': matchJsonData['customId'], 
                        'id': str(matchJsonData['id']), 
                        'slug': matchJsonData["slug"], 
                        'home': matchJsonData['homeTeam']['name'], 
                        'away': matchJsonData['awayTeam']['name'], 
                        'home_id':matchJsonData['homeTeam']['id'], 
                        'away_id':matchJsonData['awayTeam']['id'],
                        'startTimestamp': matchJsonData["startTimestamp"],
                        'league': matchJsonData["tournament"]["name"],

                        'home_country':matchJsonData['homeTeam']['country'].get('name', 'NA'),
                        'away_country':matchJsonData['awayTeam']['country'].get('name', 'NA')
                    }
                    matchIDs.append(matchInfo)
        


    def getScheduledMatch(self, days):
        if days > 2 and days < 0:
            self.logger.error("days parameter should not exceed 2 as scheduled match may not be accurate. Aborting get scheduled match...")
            return None
        else:
            date = datetime.now() + timedelta(days=days)
            date = date.strftime("%Y-%m-%d")
            requestURL      = self.SCHEDULEMATCHURL + date
            response = self.session.get(requestURL)
            dictData = response.json()

            matchIDs = []
            for match in dictData['events']:
                dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
                if dateStr == date:
                    self.findScheduledMatchWithPlayerStats(match, matchIDs)

            requestURL = requestURL + "/inverse"
            response = self.session.get(requestURL)
            moreData = response.json()

            for match in moreData['events']:
                dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
                if dateStr == date:
                    self.findScheduledMatchWithPlayerStats(match, matchIDs)

            print(len(matchIDs))


            return matchIDs # return this to caller function to get historical data from database
                            # if data doesn't exist or not updated, call getPast5Matches function


    async def getPlayerInformation(self, asession, playerID):
        """
        Get the player information using its playerID such as player name, player's team, player's country, and player's birthdate
        
        Parameters:
            playerID: player ID

        Returns:
            playersInfo (dict): a dictionary containing the player info:
            {name, team, country, birth_date}
            {} if not valid
        """
        playerURL = f"{self.PLAYERURL}{playerID}"
        response = await asession.get(playerURL, stream=True)

        # check for request status
        if response.status_code != 200:
            # log instead!
            try:
                self.logger.error(f"failed to obtain player data for Player {playerID}: {response.status_code} {STATUS_MESSAGES[response.status_code]}")
            except:
                self.logger.error(f"failed to obtain player data for Player {playerID}: {response.status_code}")

            return {}

        playersInfo = {}

        response = response.json()["player"]
        try:
            playersInfo["player_name"] = response["name"]
            playersInfo["team"] = {"name":response["team"]["name"], "country": response["team"]["country"]["name"]}
            
            playersInfo["country"] = response["country"]["name"]
            birthdate = datetime.utcfromtimestamp(response.get('dateOfBirthTimestamp',SENTINELBIRTHEPOCH)).date()
            birthdate = datetime.combine(birthdate, datetime.min.time()) # convert back to datetime obj

            playersInfo["birth_date"] = birthdate
            return playersInfo

        except Exception as e:
            self.logger.error(f"failed to obtain player data: {e}")
            return {}
        

    async def getPlayerMatchStat(self, asession, matchID):
        """
        Get player statistic such as shot made, shot on target, assist, goal scored, fouls, was fouled, shot saved if available
        
        Parameters:
            matchID: ID of the football match

        Returns:
            all_player_stats (dict of dict of dict): a dictionary containing home/away as key, item = dict containing
            player names as key, and a dictionary containing the player stats as value
            {player:{playerid, matchid, shot on target, assist, goal scored, fouls, was fouled, shot saved if available}, ...}
            {} if not valid
        """
        lineupPart = matchID["id"] + "/lineups"
        lineupURL = self.EVENTURL + lineupPart
        response = await asession.get(lineupURL, stream=True)

        # check for link validity, league such as Champions League Qualification
        # will not have players stats, but after qualification, they will have it

        # check for request status
        if response.status_code != 200:
            # log instead!
            try:
                self.logger.error(f"failed to obtain player stats for {matchID}: {response.status_code} {STATUS_MESSAGES[response.status_code]}")
            except:
                self.logger.error(f"failed to obtain player stats for {matchID}: {response.status_code}")

            return {}

        allPlayersStats = response.json()
        all_player_stats = {}               # to store players stat for the match
        customID = matchID["customId"]
        id = matchID["id"]
        slug = matchID["slug"]


        
        # check for available player id as all player id should be unique
        try:
            for team in allPlayersStats.keys():
                if team != "confirmed" and (team == "home" or team == "away"):
                    all_player_stats[team] = {}
                    for i, player in enumerate(allPlayersStats[team]["players"]):
                        
                        # init dict
                        player_dict = {}
                       
                        player_dict["match id"] = f"{customID}_{id}_{slug}"
                        player_dict["player id"] = player["player"]["id"]

                        # starting player if it is the first 11 players
                        player_dict["is starting player"] = True if i < MAXSTARTINGPLAYER else False
                        

                        player_dict["country"] = player['player']["country"].get("name", "NA")
                        birthdate = datetime.utcfromtimestamp(player['player'].get('dateOfBirthTimestamp',SENTINELBIRTHEPOCH)).date()
                        birthdate = datetime.combine(birthdate, datetime.min.time()) # convert back to datetime obj
                        
                        player_dict["birth_date"] = birthdate

                        # if key doesn't exist, it means 0
                        if "statistics" in player.keys():
                            minutesPlayed = player["statistics"].get("minutesPlayed", 0)
                            player_dict["minutesPlayed"] = minutesPlayed

                            # get shots related data
                            blockedShots    = player["statistics"].get("blockedScoringAttempt", 0)
                            shotOffTargets  = player["statistics"].get("shotOffTarget", 0)
                            shotOnTargets   = player["statistics"].get("onTargetScoringAttempt", 0)
                            player_dict["shot made"] = blockedShots + shotOffTargets + shotOnTargets
                            player_dict["shot on target"] = shotOnTargets

                            # get goal related data
                            goalAssist = player["statistics"].get("goalAssist", 0)
                            player_dict["assist"] = goalAssist
                            goals = player["statistics"].get("goals", 0)
                            player_dict["goal scored"] = goals

                            # get foul related data
                            fouls = player["statistics"].get("fouls", 0)
                            player_dict["fouls"] = fouls
                            foulWon = player["statistics"].get("wasFouled", 0)
                            player_dict["foul won (was fouled)"] = foulWon

                            # get shot saved data
                            saves = player["statistics"].get("saves", 0)
                            player_dict["shot saved"] = saves
                        
                        # when player doesn't have the statistics keyword
                        else:
                            raise KeyError("no statistic keyword for player = no statistic")

                        # add to match player dict
                        all_player_stats[team][player["player"]["name"]] = player_dict


        except Exception as e:
            self.logger.error(f"failed to obtain player stats {repr(e)}, removing the match {matchID}...")
            all_player_stats = {}

        return all_player_stats

    async def getMatchStat(self, asession, matchIDs):
        """
        Get overall match statistic such as team shot made, team shot on target, corner, offside, fouls, yellow/red cards, 
        for the whole match, 1st half, and 2nd half

        Parameters:
            matchID: ID of the football match

        Returns:
            match_stats (dict): a dictionary containing the match id and the overall match statistic as described above as value
            {match id: {stats}, ...}
        """
        statPart = matchIDs["id"] + "/statistics"
        lineupURL = self.EVENTURL + statPart
        response = await asession.get(lineupURL, stream=True)
        match_stats = {}
        match_stats["home"] = matchIDs["home"]
        match_stats["away"] = matchIDs["away"]
        match_stats["home_country"] = matchIDs["home_country"]
        match_stats["away_country"] = matchIDs["away_country"]
        match_stats["date"] =  datetime.utcfromtimestamp(matchIDs["startTimestamp"])
        match_stats["league"] = matchIDs["league"]

        requiredInformationCount = 0

        if response.status_code == 200:
            allMatchStats = response.json()
            customID = matchIDs["customId"]
            id = matchIDs["id"]
            slug = matchIDs["slug"]
            matchID = f"{customID}_{id}_{slug}"

            periodPrefix = ""
            match_stats["match id"] = matchID
            

            for matchStats in allMatchStats["statistics"]:
                if matchStats["period"] != "ALL":
                    periodPrefix = matchStats["period"] + "_"

                else:
                    periodPrefix = ""
                    
                homePrefix = periodPrefix + "home_"
                awayPrefix = periodPrefix + "away_"

                # init required stats
                match_stats[f"{homePrefix}corners"] = 0
                match_stats[f"{awayPrefix}corners"] = 0
                match_stats[f"{homePrefix}fouls"] = 0
                match_stats[f"{awayPrefix}fouls"] = 0
                match_stats[f"{homePrefix}yellowCards"] = 0
                match_stats[f"{awayPrefix}yellowCards"] = 0
                match_stats[f"{homePrefix}redCards"] = 0
                match_stats[f"{awayPrefix}redCards"] = 0
                match_stats[f"{homePrefix}totalShot"] = 0
                match_stats[f"{awayPrefix}totalShot"] = 0
                match_stats[f"{homePrefix}shotOnTarget"] = 0
                match_stats[f"{awayPrefix}shotOnTarget"] = 0
                match_stats[f"{homePrefix}totalSaves"] = 0
                match_stats[f"{awayPrefix}totalSaves"] = 0

                # update each stat type if exists
                for statsType in matchStats["groups"]:
                    if statsType["groupName"] == "Match overview":
                        requiredInformationCount += 1

                        # go though each stats under the Match Overview category
                        # we only want corner kicks and fouls from this category
                        for statItem in statsType["statisticsItems"]:
                            if statItem["name"] == "Corner kicks":
                                
                                match_stats[f"{homePrefix}corners"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}corners"] = statItem.get("away", 0)

                            elif statItem["name"] == "Fouls":
                                match_stats[f"{homePrefix}fouls"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}fouls"] = statItem.get("away", 0)

                            elif statItem["name"] == "Yellow cards":
                                match_stats[f"{homePrefix}yellowCards"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}yellowCards"] = statItem.get("away", 0)
                        
                            elif statItem["name"] == "Red cards":
                                match_stats[f"{homePrefix}redCards"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}redCards"] = statItem.get("away", 0)

                    elif statsType["groupName"] == "Shots":
                        requiredInformationCount += 1

                        # go though each stats under the Shots category
                        # we only want total shots and shots on target from this category
                        for statItem in statsType["statisticsItems"]:
                            if statItem["name"] == "Total shots":
                                match_stats[f"{homePrefix}totalShot"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}totalShot"] = statItem.get("away", 0)
                            
                            elif statItem["name"] == "Shots on target":
                                match_stats[f"{homePrefix}shotOnTarget"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}shotOnTarget"] = statItem.get("away", 0)


                    elif statsType["groupName"] == "Goalkeeping":
                        requiredInformationCount += 1

                        # go though each stats under the Goalkeeping category
                        # we only want total saves from this category
                        for statItem in statsType["statisticsItems"]:
                            if statItem["name"] == "Total saves":
                                match_stats[f"{homePrefix}totalSaves"] = statItem.get("home", 0)
                                match_stats[f"{awayPrefix}totalSaves"] = statItem.get("away", 0)
                                break #exit the loop as we got the required stat already
        else:
            match_stats = {}

        if requiredInformationCount < 3:
            match_stats = {}
        return match_stats
                    


    async def getAllMatchCompleteStat(self, matchIDs):
        """
        Get overall match stat and player stat

        Parameters:
            matchIDs (list of dict): list of dict containing customId, id, and slug. All of these are IDs of each match

        Returns:
            past_match_stat (dict of dict): a dictionary containing match ID as key, with dictionary containing 
            player statistic and overall match statistic as value        
        """
        asession = AsyncHTMLSession()

        # create a list of asynchronous task to execute
        tasks = [self.getPlayerMatchStat(asession, matchID) for matchID in matchIDs]

        

        # executes in the order of the awaits in the list
        # the result is an aggregate list of returned values
        playerStats = await async_tqdm.gather(*tasks, desc="getting player stats")

        tasks = [self.getMatchStat(asession, matchID) for matchID in matchIDs]
        past_match_stat = await async_tqdm.gather(*tasks, desc="getting stats for each match")
        
        updated_past_match_stat = []
        for i , match in enumerate(matchIDs):
            if past_match_stat[i]:
                if playerStats[i]:
                    past_match_stat[i]["player_stats"] = playerStats[i]
                    updated_past_match_stat.append(past_match_stat[i])
                else:
                    continue

        return updated_past_match_stat

        

    def getPastDateMatchStat(self, date:datetime):
        """
        Get finished matches complete stats for a particular past date

        Parameters:
            date: past datetime obj

        Returns:
            pastMatchesStats (dict of dict): a dictionary containing match ID as key, with dictionary containing 
            player statistic and overall match statistic as value
        """
        date = date.strftime("%Y-%m-%d")
        requestURL      = self.SCHEDULEMATCHURL + date
        response = self.session.get(requestURL)
        dictData = response.json()
        
        
       
        matchIDs = []

        self.filterMatchesWithPlayerStat(date,dictData,matchIDs)

        requestURL = requestURL + "/inverse"
        response = self.session.get(requestURL)
        moreData = response.json()
        self.filterMatchesWithPlayerStat(date,moreData,matchIDs)

        print(f"number Of Matches = {len(matchIDs)}")

        pastMatchesStats = asyncio.run(self.getAllMatchCompleteStat(matchIDs))

        return pastMatchesStats



    def filterMatchesWithPlayerStat(self, date, matchJSON:dict, matchIDs:list):
        for match in matchJSON['events']:
            dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
            if dateStr == date:
                if "status" in match.keys():
                    self.findMatchWithPlayerStat(match,matchIDs)

    def closeASession(self):
        """
        Close the browser for async
        """
        self.asession.close()

    def closeSession(self):
        """
        Close the browser
        """
        self.session.close()

