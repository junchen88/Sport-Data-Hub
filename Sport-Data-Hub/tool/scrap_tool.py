from http.client import HTTPException
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
from tool import scrape_config
import random

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
    """
    Scraper class used to scrape soccer data
    """
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

    def findMatchWithPlayerStat(self, matchJsonData, pastMatchInfo, teamName=None, numberOfMatchesWithData=None):
        """
        Determine whether the given match matchJsonData has
        player statistics. If it has the stats, then information
        regarding the match will be appended into pastMatchInfo

        Parameters:
            - matchJsonData: JSON data containing information regarding the match
            - pastMatchInfo (1): dict of list of dict, team name as key and list of match info as its value
            - pastMatchInfo (2): list of matchinfo dict - if teamName is None 
            - teamName (or None): the football team name
            - numberOfMatchesWithData (or None): counter for keeping the number of past matches with player stats appended

        Returns:
            - numberOfMatchesWithData (or None): counter for keeping the number of past matches with player stats appended
        """
        try:

            # make sure the match is finished and not awarded
            if matchJsonData["status"]["type"] == "finished" and "isAwarded" not in matchJsonData.keys():

                # store match info
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

                # look for hasEventPlayerStatistics keyword as it normally has
                # player statistic if the keyword exists.
                if "hasEventPlayerStatistics" in matchJsonData.keys():
                    if matchJsonData["hasEventPlayerStatistics"] == True:
                        matchInfo["hasPlayerStats"] = True
                    else:
                        matchInfo["hasPlayerStats"] = False
                    
                elif matchJsonData['tournament']['uniqueTournament']['hasEventPlayerStatistics'] == True:
                    matchInfo["hasPlayerStats"] = True

                # if not, then we don't have player stats available and therefore
                # we don't store it into matchInfo
                else:
                    matchInfo["hasPlayerStats"] = False
    
                # store into matchInfo only if there is player stats available
                if matchInfo["hasPlayerStats"] == True:

                    if teamName:
                        pastMatchInfo[teamName].append(matchInfo)
                        numberOfMatchesWithData += 1
                    else:
                        pastMatchInfo.append(matchInfo)
                
            return numberOfMatchesWithData

        except KeyError as e:
            # print(e, "Player stat is not available")  
            # don't append the current match info into pastMatchInfo
            self.logger.error(f"matchID : {matchJsonData['id']}, KeyError: {e}")

            return numberOfMatchesWithData 

        except Exception as e:
            # log instead
            self.logger.error(f"matchID : {matchJsonData['id']}, {e}")
            # don't append the current match info into pastMatchInfo
            return numberOfMatchesWithData


    async def getPastMatches(self, asession, teamID, teamName, pastMatchInfo, pageNum, queue):
        """
        If database doesn't have the latest H2H match, it will need to call this function to
        get the latest NUMOFPASTMATCHES matches data for the team teamName
        
        Parameters:
            - asession: a AsyncHTMLSession
            - teamID: team ID used by website being scraped
            - teamName: team name
            - pastMatchInfo: dict with teamName as key and list of match info dict as value
            - pageNum: the current page number of the scraped api for the team's matches

        Returns:
            - pastMatchInfo: dict of team name as key with list of dict containing match infos as value
        
        """
        try:
            # humanize the requests
            #--------------------------------------------------------------------------
            used_queue_slot = False  # Track whether we acquired a queue slot
            if pageNum == 0: # Only acquire queue slot for the first request, not for recursion
                await queue.get()
                used_queue_slot = True
            delay = random.uniform(scrape_config.DELAY_RANGE[0],scrape_config.DELAY_RANGE[1])
            await asyncio.sleep(delay)
            headers = scrape_config.HEADERS
            
            #------------------------------------------------------------------------------
            
            # init dict to store result
            if pastMatchInfo is None:
                pastMatchInfo = {teamName:[]}

            # request for data
            pastMatchURL = self.TEAMURL + str(teamID) + f"/events/last/{pageNum}"
            response = await asession.get(pastMatchURL, stream=True, headers=headers)
            # check for request status
            if response.status_code != 200:
                # log instead!
                try:
                    self.logger.error(f"failed to obtain past 5 matches data for team {pastMatchURL}: {response.status_code} {STATUS_MESSAGES[response.status_code]}")
                except:
                    self.logger.error(f"failed to obtain past 5 matches data for team {pastMatchURL}: {response.status_code}")

                return {}
            dataJson = response.json()
            
            numberOfMatchesWithData = 0 # used to track the number of matches with stats, we use it as a counter to stop recursive function
            
            if len(dataJson["events"]) >= scrape_config.NUMOFPASTMATCHES:
                # -6 since we want 5 results as range stops at target-1
                # latest result is at page 0 and at the end
                for i in range(len(dataJson["events"])-1, -1, -1):
                    match = dataJson["events"][i]
                    if "status" in match.keys():
                        numberOfMatchesWithData = self.findMatchWithPlayerStat(match, pastMatchInfo, teamName, numberOfMatchesWithData)
                    
                    if numberOfMatchesWithData >= scrape_config.NUMOFPASTMATCHES:
                        
                        break #stop loop if we got at least 5 data


            
            # go to the next page and get more data if possible
            if numberOfMatchesWithData < scrape_config.NUMOFPASTMATCHES and dataJson.get("hasNextPage", False):
                pageNum += 1
                await self.getPastMatches(asession, teamID, teamName, pastMatchInfo, pageNum, queue)
        
        except Exception as e:
            self.logger.error(f"failed to obtain past 5 matches data for team: {repr(e)}")

        finally:
            if used_queue_slot:  # Only release queue slot if `queue.get()` was used
                queue.task_done()
            
                # Refill slot
                if queue.empty():
                    for _ in range(scrape_config.QUEUE_SLOTS):
                        queue.put_nowait(True)
                # print(queue.qsize())


        return pastMatchInfo


    def findScheduledMatchWithPlayerStats(self, matchJsonData, matchesInfos):
        """
        filter scheduled matches with player stats

        Parameters:
            - matchJsonData: JSON data containing information regarding the match
            - matchesInfos: list of dict - to store the a match information such as home, away, start time, etc (see matchInfo below)
        """
        try:
            # filter for match not started
            if "status" in matchJsonData.keys():
                if matchJsonData["status"]["type"] == "notstarted" and "isAwarded" not in matchJsonData.keys():

                    # when there is hasEventPlayerStatistics key word and it's true, it normally has player stats
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
                        matchesInfos.append(matchInfo)
        except Exception as e:
            customID = matchJsonData["customId"]
            id = matchJsonData["id"]
            slug = matchJsonData["slug"]
            identifier = f"{customID}_{id}_{slug}"
            self.logger.error(f"failed to filter current scheduled match ({identifier}) for player stats : {repr(e)}" )
        


    def getScheduledMatch(self, days):
        """
        Get scheduled matches with respect to todays date with days as the offset

        Parameters:
            - days: only 0 and 1 is allowed as the scheduled match data may not be accurate
        
        Returns:
            - matchesInfos: list of dict containing matchinfos
        """
        # filter function parameter
        if days > 2 and days < 0:
            self.logger.error("days parameter should not exceed 2 as the scheduled match may not be accurate. Aborting get scheduled match...")
            return None
        else:
            # get todays date for comparison later
            date = datetime.now() + timedelta(days=days)
            date = date.strftime("%Y-%m-%d")
            requestURL      = self.SCHEDULEMATCHURL + date

            try:
                response = self.session.get(requestURL)
                dictData = response.json()

                matchesInfos = []

                # filter for today's match and filter matches with player stats
                # then store it into matchesInfos
                for match in dictData['events']:
                    dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
                    if dateStr == date:
                        self.findScheduledMatchWithPlayerStats(match, matchesInfos)

                # continue to fetch for more matches
                requestURL = requestURL + "/inverse"
                response = self.session.get(requestURL)
                moreData = response.json()

                # filter for today's match and filter matches with player stats
                # then store it into matchesInfos
                for match in moreData['events']:
                    dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
                    if dateStr == date:
                        self.findScheduledMatchWithPlayerStats(match, matchesInfos)

                print(len(matchesInfos))
                return matchesInfos


            except Exception as e:
                self.logger.error(f"Cannot obtain scheduled matches: {repr(e)}")
                return []



    async def getPlayerInformation(self, asession, playerID):
        """
        Get the player information using its playerID such as player name, player's team, player's country, and player's birthdate
        
        Parameters:
            - playerID: player ID

        Returns:
            - playersInfo (dict): a dictionary containing the player info:
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

        # store data such as player name, player's team, player's country, and player's birthdate
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
        

    async def getMatchLineup(self, asession, matchID, queue, identifier=""):
        # humanize the requests
        #--------------------------------------------------------------------------
        await queue.get()

        delay = random.uniform(scrape_config.DELAY_RANGE[0],scrape_config.DELAY_RANGE[1])
        await asyncio.sleep(delay)   
        headers = scrape_config.HEADERS
        #------------------------------------------------------------------------------
        lineupPart = matchID + "/lineups"
        lineupURL = self.EVENTURL + lineupPart
        response = await asession.get(lineupURL, stream=True, headers=headers)

        queue.task_done()
        
        # Refill slot
        if queue.empty():
            for _ in range(scrape_config.QUEUE_SLOTS):
                queue.put_nowait(True)

        # check for request status
        if response.status_code != 200:
            try:
                exceptionMessage = f"{response.status_code} {STATUS_MESSAGES[response.status_code]}"
            except:
                exceptionMessage = f"{response.status_code}"

            raise HTTPException(exceptionMessage)
        
        return response

    async def getPlayerMatchStat(self, asession, matchInfo, queue):
        """
        Get player statistic such as shot made, shot on target, assist, goal scored, fouls, was fouled, shot saved if available
        
        Parameters:
            - matchInfo: football match info

        Returns:
            - all_player_stats (dict of dict of dict): a dictionary containing home/away as key, item = dict containing
            player names as key, and a dictionary containing the player stats as value
            {player:{playerid, matchInfo, shot on target, assist, goal scored, fouls, was fouled, shot saved if available}, ...}
            {} if not valid
        """
        

        # check for link validity, league such as Champions League Qualification
        # will not have players stats, but after qualification, they will have it
        try:
            
            response = await self.getMatchLineup(asession, matchInfo["id"], queue)


            allPlayersStats = response.json()
            all_player_stats = {}               # to store players stat for the match
            customID = matchInfo["customId"]
            id = matchInfo["id"]
            slug = matchInfo["slug"]
            
            # loop through home and away team
            for team in allPlayersStats.keys():

                # make sure key word is either home or away
                if team != "confirmed" and (team == "home" or team == "away"):
                    all_player_stats[team] = {} # init home/away dict to store player

                    # loop through each player
                    for i, player in enumerate(allPlayersStats[team]["players"]):
                        
                        # init dict
                        player_dict = {}
                       
                        player_dict["match id"] = f"{customID}_{id}_{slug}"
                        player_dict["player id"] = player["player"]["id"]

                        # starting player if it is the first 11 players
                        player_dict["is starting player"] = True if i < MAXSTARTINGPLAYER else False
                        

                        player_dict["country"] = player['player']["country"].get("name", "NA")

                        # get birthdate and convert into datetime obj with date data only
                        birthdate = datetime.utcfromtimestamp(player['player'].get('dateOfBirthTimestamp',SENTINELBIRTHEPOCH)).date()
                        birthdate = datetime.combine(birthdate, datetime.min.time()) # convert back to datetime obj     
                        player_dict["birth_date"] = birthdate

                        # if statistics key doesn't exist, raise error
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
                            raise KeyError("no player statistic keyword")

                        # add to match player dict
                        all_player_stats[team][player["player"]["name"]] = player_dict

        # return empty dict if failed to fetch player stats
        # so the match will get removed later on
        except Exception as e:
            customID = matchInfo["customId"]
            id = matchInfo["id"]
            slug = matchInfo["slug"]
            identifier = f"{customID}_{id}_{slug}"

            self.logger.error(f"failed to fetch player stats {repr(e)}, removing the match {identifier}...")
            all_player_stats = {}

        
        return all_player_stats

    async def getMatchStat(self, asession, matchInfo, queue):
        """
        Get overall match statistic such as team shot made, team shot on target, corner, offside, fouls, yellow/red cards, 
        for the whole match, 1st half, and 2nd half

        Parameters:
            - matchInfo: football match info

        Returns:
            - match_stats (dict): a dictionary containing the match id and the overall match statistic as described above as value
            {match id: {stats}, ...}
        """

        # humanize the requests
        #--------------------------------------------------------------------------

        await queue.get()

        delay = random.uniform(scrape_config.DELAY_RANGE[0],scrape_config.DELAY_RANGE[1])
        await asyncio.sleep(delay)
        headers = scrape_config.HEADERS
        
        #------------------------------------------------------------------------------

        try:
            # fetch data
            statPart = matchInfo["id"] + "/statistics"
            lineupURL = self.EVENTURL + statPart
            response = await asession.get(lineupURL, stream=True, headers=headers)

            # init and populate match stat dict
            match_stats = {}
            match_stats["home"] = matchInfo["home"]
            match_stats["away"] = matchInfo["away"]
            match_stats["home_country"] = matchInfo["home_country"]
            match_stats["away_country"] = matchInfo["away_country"]
            match_stats["date"] =  datetime.utcfromtimestamp(matchInfo["startTimestamp"])
            match_stats["league"] = matchInfo["league"]

            requiredInformationCount = 0            # to keep count of information required

            # if request is successful
            if response.status_code == 200:
                allMatchStats = response.json()
                customID = matchInfo["customId"]
                id = matchInfo["id"]
                slug = matchInfo["slug"]
                matchID = f"{customID}_{id}_{slug}"

                periodPrefix = ""                   # to store the prefix 1ST/2ND/etc (match period)
                match_stats["match id"] = matchID
                
                # loop through the match time period (eg 1st half/2nd half/etc)
                for matchStats in allMatchStats["statistics"]:
                    if matchStats["period"] != "ALL":
                        periodPrefix = matchStats["period"] + "_"

                    else:
                        periodPrefix = ""           # do not add prefix if it is ALL, which means full time
                        
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

            # if request are not successful, we set stat dict as empty and log it
            else:
                match_stats = {}
                customID = matchInfo["customId"]
                id = matchInfo["id"]
                slug = matchInfo["slug"]
                matchID = f"{customID}_{id}_{slug}"
                self.logger.error(f"Failed to fetch match statistic data for match {matchID}, removing it...")

            # if there are not enough information, set dict as empty
            if requiredInformationCount < 3:
                match_stats = {}
                
        except Exception as e:
            self.logger.error(f"failed to obtain match data: {e}")
            match_stats = {}
        finally:
            queue.task_done()
            
            # Refill slot
            if queue.empty():
                for _ in range(scrape_config.QUEUE_SLOTS):
                    queue.put_nowait(True)
            # print(queue.qsize())


            return match_stats
                    


    async def getAllMatchCompleteStat(self, pastMatchInfo, asession, queue):
        """
        Get overall match stat and player stat

        Parameters:
            - pastMatchInfo (list of dict): list of dict containing information such as
            customId, id, and slug. All of these are IDs of each match

        Returns:
            - updated_past_match_stat (list of dict): a list of dict containing match info,
            match stats, and player stats     
        """

        # create a list of asynchronous task to execute
        tasks = [self.getPlayerMatchStat(asession, match, queue) for match in pastMatchInfo]

        

        # executes in the order of the awaits in the list
        # the result is an aggregate list of returned values
        playerStats = await async_tqdm.gather(*tasks, desc="getting player stats")

        tasks = [self.getMatchStat(asession, match, queue) for match in pastMatchInfo]
        past_match_stat = await async_tqdm.gather(*tasks, desc="getting stats for each match")
        
        # go through in the order of past match info list
        # if both match stat and player stats are not empty, then append it 
        # into updated_past_match_stat
        updated_past_match_stat = []
        for i , match in enumerate(pastMatchInfo):
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
        
        
       
        pastMatchInfo = []

        self.filterMatchesWithPlayerStat(date,dictData,pastMatchInfo)

        requestURL = requestURL + "/inverse"
        response = self.session.get(requestURL)
        moreData = response.json()
        self.filterMatchesWithPlayerStat(date,moreData,pastMatchInfo)

        print(f"number Of Matches = {len(pastMatchInfo)}")

        pastMatchesStats = asyncio.run(self.getAllMatchCompleteStat(pastMatchInfo))

        return pastMatchesStats



    def filterMatchesWithPlayerStat(self, date, matchJSON:dict, pastMatchInfo:list):
        for match in matchJSON['events']:
            dateStr = strftime('%Y-%m-%d', localtime(match["startTimestamp"]))
            if dateStr == date:
                if "status" in match.keys():
                    self.findMatchWithPlayerStat(match,pastMatchInfo)


    def closeSession(self):
        """
        Close the browser
        """
        self.session.close()

