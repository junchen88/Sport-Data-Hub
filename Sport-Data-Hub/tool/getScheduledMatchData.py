from tool import scrap_tool as st
from requests_html import HTMLSession, AsyncHTMLSession
import logging
import asyncio
from tqdm.asyncio import tqdm as async_tqdm
import json
from tool import DBHelper, scrape_config
from tqdm import tqdm
from datetime import datetime



logger = logging.getLogger(__name__)
logging.basicConfig(filename='messages.log', encoding='utf-8', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
scraper = st.Scraper(logger)
dbHelper = DBHelper.DBHelper(logger)


teamChecked = set() # to store the teams/countries that were checked whether they are in the db to prevent additional checkings
playerChecked = set() #to store the players that were checked whether they are in the db to prevent additional checkings

teamNeedInfo = set() #to store the teams/countries that is not in db
playerNeedInfo = set() #to store the players that is not in db

teamToIDDict = {}
playerToIDDict = {}


async def getMatchLineup(asession, match, queue):
    response = {}
    try:
        response = await scraper.getMatchLineup(asession, match["id"], queue)
        return response.json()


    except Exception as e:
        scraper.logger.error(f"failed to fetch player lineup {repr(e)}")
        return {}


async def getScheduledLineup(matchInfos):
    asession = AsyncHTMLSession()
    # Humanize request
    #--------------------------------------------------------
    # Fill queue with 3 slots to control execution
    queue = asyncio.Queue()
    for _ in range(scrape_config.QUEUE_SLOTS):
        queue.put_nowait(True)
    #--------------------------------------------------------
    tasks = [getMatchLineup(asession, match, queue) for match in matchInfos]
    responses = await async_tqdm.gather(*tasks, desc="getting past 5 matches info")
    await asession.close()
    return responses


# scrape past matches for each team, default no of matches = 5
# read db and get data first, if not use scraper.getPast5matches
async def scrapeScheduledMatchStat(scraper:st.Scraper, scheduledMatchesInfos):
    """
    Scrape past matches for each team, default no of matches = 5

    Parameters:
        - scraper: Scraper class obj used to scrape data
        - scheduledMatchesInfos (list of dict): a list of dict containing match infos

    Returns:
        - pastMatchesStats: (list of dict): a list of dict containing match info,
            match stats, and player stats  
    """
    asession = AsyncHTMLSession()
    
    # Humanize request
    #--------------------------------------------------------
    # Fill queue with 3 slots to control execution
    queue = asyncio.Queue()
    for _ in range(scrape_config.QUEUE_SLOTS):
        queue.put_nowait(True)
    #-------------------------------------------------------
    # get past 5 matches for each new team that has not enough data
    pageNum = 0
    tasks = [scraper.getPastMatches(asession, match["home_id"], match["home"], pastMatchInfo=None, pageNum=pageNum, queue=queue) for match in scheduledMatchesInfos]
    tasks.extend([scraper.getPastMatches(asession, match["away_id"], match["home"], pastMatchInfo=None, pageNum=pageNum, queue=queue) for match in scheduledMatchesInfos])
    allPast5MatchIDs = await async_tqdm.gather(*tasks, desc="getting past 5 matches info")
    # print(allPast5MatchIDs)    

    # combine all the matchinfo result into one list
    teamPastMatchID = []
    for teamMatchInfo in allPast5MatchIDs:
        for team, matchIDs in teamMatchInfo.items():
            teamPastMatchID.extend(matchIDs)

    # fetch all stats for each match such as match and player stats
    pastMatchesStats = await scraper.getAllMatchCompleteStat(teamPastMatchID, asession, queue)

    await asession.close()
    return pastMatchesStats

# allPast5MatchesID = await scraper.getPlayerInformation(asession, 111505)

# print(allPast5MatchesID)

def checkInDb(scrapedData, checkType="team"):
    """
    Method to check whether the scrapedData team or player exists
    in the db

    Parameters:
        - scrapedData: list of dict containing matchinfos
        - checkType: the check type. Default is team
    
    """

    # if check type is team, we check whether the team is in the db
    if checkType=="team":
        for match in scrapedData:
            if match:
                # if team has checked already, do not check it
                # check it if it is not checked and add to set
                # check home team
                if (match["home"], match["home_country"]) not in teamChecked:
                    teamChecked.add((match["home"], match["home_country"]))
                    
                    # check item in db, if result is bool, then it's not in db
                    # else, record the id as value with team's name as key
                    result = dbHelper.checkItemInDB(table="team", team_name=match["home"], country=match["home_country"])
                    if type(result) is bool:
                        teamNeedInfo.add((match["home"], match["home_country"]))
                    else:
                        teamToIDDict[match["home"]] = result

                # check away team
                if (match["away"], match["away_country"]) not in teamChecked:
                    teamChecked.add((match["away"], match["away_country"]))

                    result = dbHelper.checkItemInDB(table="team", team_name=match["away"], country=match["away_country"])
                    if type(result) is bool:
                        teamNeedInfo.add((match["away"], match["away_country"]))
                    else:
                        teamToIDDict[match["away"]] = result

    # if checktype is player          
    else:
     
        for match in scrapedData:
            # if player has checked already, do not check it
            # check it if it is not checked and add to set
            if match:

                # look at the player stats dict/section
                # team is "home"/"away", players is dict containing all player's info
                # for the team - with player's name as key and player info as value
                for team, players in match["player_stats"].items():
                    for name, player in players.items():
                        if (name, player["birth_date"]) not in playerChecked:
                            playerChecked.add((name, player["birth_date"]))
                            
                            # check player in db, if result is bool, then it's not in db
                            # else, record the id as value with player's name and birth date 
                            # as key since problem arises when players have the same name in the 
                            # same match
                            result = dbHelper.checkItemInDB(teamToIDDict, teamNeedInfo, player['country'], table="player", player_name=name, birth_date=player["birth_date"])
                            if type(result) is bool:
                                playerNeedInfo.add((name, match[team], player['country'], player["birth_date"]))

                            else:
                                playerToIDDict[(name, player["birth_date"])] = result

                    
  
def addDataToDB(pastMatchesStats):
    """
    Add new data to db

    Parameters:
        - pastMatchesStats (list of dict): a list of dict containing match info, match stats, and player stats
    """

    # add team into db and create team name -> id mapping
    if teamNeedInfo:
        for teamInfo in tqdm(teamNeedInfo, desc="Writing team info to db"):
            # record its id
            teamId = dbHelper.insert_team(teamInfo)
            if teamId is not None:
                teamToIDDict[teamInfo[0]] = teamId

    # add player into db and create player name, birthdate -> id mapping
    if playerNeedInfo:
        for playerInfo in tqdm(playerNeedInfo, desc="Writing player info to db"):
            try:
                playerInfoForDB = (playerInfo[0], teamToIDDict[playerInfo[1]], teamToIDDict[playerInfo[2]], playerInfo[3])
            except Exception as e:
                logger.error(f"cannot write player into db {e}")
                continue

            # insert player and record its id
            playerID = dbHelper.insert_player(playerInfoForDB)
            if playerID is not None:
                playerToIDDict[(playerInfo[0], playerInfo[3])] = playerID
            
    # insert player and match stat data
    for matchStats in tqdm(pastMatchesStats, desc="Writing match stat to db"):
        if matchStats:
            dbHelper.insert_stat_data(matchStats, teamToIDDict, playerToIDDict)
  

def serialize_datetime(obj):
    """
    Used to serialise datetime obj

    Parameters:
        - obj: datetime obj

    Returns:
        - obj.isoformat(): convert datetime to ISO 8601 string format
    """
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 string format
    raise TypeError(f"Type {type(obj)} not serializable")


def getScheduledMatchStat(day):
    """
    To get scheduled match stat

    Parameters:
        - day: the day offset with respect to today's date
    """
    matchesInfos = scraper.getScheduledMatch(day)
    if matchesInfos:
        checkInDb(matchesInfos)

        # check db for past stats before getting new data
        
        pastMatchesStats = asyncio.run(scrapeScheduledMatchStat(scraper, matchesInfos))



        # add checkings for team and players
        checkInDb(pastMatchesStats, "player")
        checkInDb(pastMatchesStats)

        fp = open("jsonData.json", "w")
        json.dump(pastMatchesStats, fp, indent = 6, default=serialize_datetime)

        # print(playerNeedInfo)
        addDataToDB(pastMatchesStats)
        # dbHelper.insert_player({"name":"Jordan Pickford", "team_id":"5", "country_id":"5", "birth_date": datetime.now()})
        # dbHelper.insert_team({"team":"test club", "country": "test country"})
        scraper.closeSession()

        lineupDatas = asyncio.run(getScheduledLineup(matchesInfos))

        for i,match in enumerate(matchesInfos):
            
            match["lineup"] = lineupDatas[i]

        print(matchesInfos)
    return matchesInfos

# getScheduledMatchStat(1)