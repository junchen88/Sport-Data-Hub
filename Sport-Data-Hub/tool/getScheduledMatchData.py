from tool import scrap_tool as st
from requests_html import HTMLSession, AsyncHTMLSession
import logging
import asyncio
from tqdm.asyncio import tqdm as async_tqdm
import json
from tool import DBHelper
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

# scrape past matches for each team, default no of matches = 5
# read db and get data first, if not use scraper.getPast5matches
async def scrapeScheduledMatchStat(scraper:st.Scraper, matchIDs):
        
    asession = AsyncHTMLSession()
    
    pageNum = 0
    tasks = [scraper.getPast5Matches(asession, match["home_id"], match["home"], matchIDs=None, pageNum=pageNum) for match in matchIDs]
    tasks.extend([scraper.getPast5Matches(asession, match["away_id"], match["home"], matchIDs=None, pageNum=pageNum) for match in matchIDs])
    allPast5MatchIDs = await async_tqdm.gather(*tasks, desc="getting past 5 matches info")
    # print(allPast5MatchIDs)
    teamPastMatchID = []
    for teamMatchInfo in allPast5MatchIDs:
        for team, matchIDs in teamMatchInfo.items():
            teamPastMatchID.extend(matchIDs)

    pastMatchesStats = await scraper.getAllMatchCompleteStat(teamPastMatchID)

    return pastMatchesStats

# allPast5MatchesID = await scraper.getPlayerInformation(asession, 111505)

# print(allPast5MatchesID)

def checkInDb(scrapedData, checkType="team"):
    if checkType=="team":
        for match in scrapedData:
            if match:
                # if team is checked already, do not check it
                # check it if it is not checked and add to set
                if (match["home"], match["home_country"]) not in teamChecked:
                    teamChecked.add((match["home"], match["home_country"]))
                    
                    result = dbHelper.checkItemInDB(table="team", team_name=match["home"], country=match["home_country"])
                    if type(result) is bool:
                        teamNeedInfo.add((match["home"], match["home_country"]))
                    else:
                        teamToIDDict[match["home"]] = result

                if (match["away"], match["away_country"]) not in teamChecked:
                    teamChecked.add((match["away"], match["away_country"]))

                    result = dbHelper.checkItemInDB(table="team", team_name=match["away"], country=match["away_country"])
                    if type(result) is bool:
                        teamNeedInfo.add((match["away"], match["away_country"]))
                    else:
                        teamToIDDict[match["away"]] = result

                
    else:
     
        for match in scrapedData:
            # if team is checked already, do not check it
            # check it if it is not checked and add to set
            if match:
                for team, players in match["player_stats"].items():
                    for name, player in players.items():
                        if (name, player["birth_date"]) not in playerChecked:
                            playerChecked.add((name, player["birth_date"]))
                            
                            result = dbHelper.checkItemInDB(teamToIDDict, teamNeedInfo, player['country'], table="player", player_name=name, birth_date=player["birth_date"])
                            if type(result) is bool:
                                playerNeedInfo.add((name, match[team], player['country'], player["birth_date"]))

                            else:
                                playerToIDDict[(name, player["birth_date"])] = result

                    
  
def addDataToDB(pastMatchesStats):

    if teamNeedInfo:
        for teamInfo in teamNeedInfo:
            # record its id
            teamId = dbHelper.insert_team(teamInfo)
            if teamId is not None:
                teamToIDDict[teamInfo[0]] = teamId

    if playerNeedInfo:
        for playerInfo in tqdm(playerNeedInfo):
            try:
                playerInfoForDB = (playerInfo[0], teamToIDDict[playerInfo[1]], teamToIDDict[playerInfo[2]], playerInfo[3])
            except Exception as e:
                logger.error(f"cannot write player into db {e}")
                continue

            playerID = dbHelper.insert_player(playerInfoForDB)
            if playerID is not None:
                playerToIDDict[(playerInfo[0], playerInfo[3])] = playerID
            

    for matchStats in pastMatchesStats:
        if matchStats:
            dbHelper.insert_stat_data(matchStats, teamToIDDict, playerToIDDict)
  

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 string format
    raise TypeError(f"Type {type(obj)} not serializable")


def getScheduledMatchStat():
    matchIDs = scraper.getScheduledMatch(1)
    if matchIDs:
        checkInDb(matchIDs)

        # check db for past stats before getting new data

        pastMatchesStats = asyncio.run(scrapeScheduledMatchStat(scraper, matchIDs))



        # add checkings for team and players
        checkInDb(pastMatchesStats, "player")
        checkInDb(pastMatchesStats)

        fp = open("jsonData.json", "w")
        json.dump(pastMatchesStats, fp, indent = 6, default=serialize_datetime)

        # print(playerNeedInfo)
        addDataToDB(pastMatchesStats)
        # dbHelper.insert_player({"name":"Jordan Pickford", "team_id":"5", "country_id":"5", "birth_date": datetime.now()})
        # dbHelper.insert_team({"team":"test club", "country": "test country"})

getScheduledMatchStat()