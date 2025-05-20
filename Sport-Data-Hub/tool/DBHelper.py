from sqlalchemy import create_engine, func, or_
from sqlalchemy.engine import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, aliased
from sqlalchemy import create_engine
import os
from django.conf import settings
import datetime
import logging
from sqlalchemy.exc import IntegrityError
import pandas as pd

class DBHelper():
    def __init__(self, logger:logging.Logger):
        self.engine = create_engine("postgresql+psycopg2://demouser:12345678@localhost:5432/demo")

        # Reflect the existing database schema
        Base = automap_base()
        Base.prepare(autoload_with=self.engine)


        # Map the Django models
        self.Team = Base.classes.football_team
        self.Player = Base.classes.football_player
        self.Match = Base.classes.football_match
        self.PlayerStats = Base.classes.football_playerstats

        self.logger = logger

    def insert_player(self, data):
        """
        Insert player

        Parameters:
            - data: tuple containing player info - name, team id, country id, birth date

        Returns:
            - newPlayerID: ID of the inserted item
            - None: insert fail
        """
        session = Session(self.engine)
        try:
            player = self.Player(
                player_name = data[0],
                team_id = data[1],
                country_id = data[2],
                birth_date = data[3],
            )
            session.add(player)
            session.commit()
            newPlayerID = player.player_id
            session.close()
            return newPlayerID


        except Exception as e:
            session.rollback()
            self.logger.error(f"Fail to add the following player: {e.orig}")
            session.close()
            return None


        

    def insert_team(self, data):
        """
        Insert team/country into db

        Parameters:
            - data: tuple containing team info - (team_name, country)

        Returns:
            - newTeamID: ID of the inserted team
            - None: insert fail
        """
        session = Session(self.engine)
        try:
            team = self.Team(
                team_name = data[0],
                country = data[1],
            )
            session.add(team)
            session.commit()
            newTeamID = team.team_id
            session.close()
            return newTeamID
            

        except Exception as e:
            session.rollback()
            self.logger.error(f"Fail to add the following team/country: {e.orig}")
            session.close()
            return None

    # Insert function
    def insert_stat_data(self, data, teamToIDDict, playerToIDDict):
        """
        Insert match and player stats into the db

        Parameters:
            - data (list of dict): a list of dict containing match info, match stats, and player stats
            - teamToIDDict: mapping dict of team name to its db ID
            - playerToIDDIct: mapping dict of (player name, birthdate) to its db ID
        """
        matchID = None
        try:
            session = Session(self.engine)

            # Insert for match
            match = self.Match(
                date=data["date"],  # Replace with match date
                # venue=data.get('venue', 'Unknown Venue'),

                # Assign homeTeam and awayTeam using query data
                # homeTeam=session.query(self.Team).filter_by(team_name=data['home']).first(),
                # awayTeam=session.query(self.Team).filter_by(team_name=data['away']).first(),
                league=data["league"],
                homeTeam_id=teamToIDDict[data["home"]],
                awayTeam_id=teamToIDDict[data["away"]],
                yellow_cards=int(data['home_yellowCards']),
                red_cards=int(data['away_redCards']),
                home_shots=int(data['home_totalShot']),
                away_shots=int(data['away_totalShot']),
                home_shots_target=int(data['home_shotOnTarget']),
                away_shots_target=int(data['away_shotOnTarget']),
                home_fouls = int(data['home_fouls']),
                away_fouls = int(data['away_fouls']),
                home_corners = int(data['home_corners']),
                away_corners = int(data['away_corners']),
            )

            session.add(match)
            session.commit()
            matchID = match.match_id # obtain added match's ID after the commit


        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"IntegrityError occurred: The item already exists or violates a constraint.\nError details: {e.orig}")

        try:
            if matchID != None:

                # Insert PlayerStats if there are player stats
                player_stats_data = data['player_stats']
                if player_stats_data:
                    for team, playerStats in player_stats_data.items():
                        for player_name, stats in playerStats.items():

                            # get the player's db ID
                            playerID = playerToIDDict[(player_name, stats["birth_date"])]


                            player_stat = self.PlayerStats(
                                match_id=matchID,
                                player_id=playerID,
                                goals_scored=int(stats['goal scored']),
                                assists=int(stats['assist']),
                                # yellow_cards=int(stats['yellow_cards']),
                                # red_cards=int(stats['red_cards']),
                                shots=int(stats['shot made']),
                                shots_target=int(stats['shot on target']),
                                fouls_committed=int(stats['fouls']),
                                fouls_won=int(stats['foul won (was fouled)']),
                            )
                            session.add(player_stat)
                    

            session.commit()
            session.close()
        # except KeyError as e:
        #     session.rollback()
        #     session.close()
        #     self.logger.error(f"Fail to add the match and players stats: {e}")
        #     print(data['home'], "\n\n\n\n\n", e)
        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"IntegrityError occurred: The item already exists or violates a constraint.\nError details: {e.orig}")



        # except Exception as e:
        #     session.rollback()
        #     self.logger.error(f"Fail to add the match and players stats: {e}")
        #     # print(data, "\n\n\n\n\n", e)
        #     session.close()

    def checkItemInDB(self, countryInDB:dict=None, countryNotInDB:set=None, playerCountry=None, **kwargs):
        """
        Check whether item is in db

        Parameters:
            - countryInDB (or None): dict containing countries/teams in db
            - countryNotInDB (or None): dict containing countries/teams not in db
            - playerCountry (or None): player's country
            - kwargs: contains the required data of the item 
        
        Returns:
            - False: when item is not in db
            - id: the item's id inside the db
        """
        if len(kwargs) != 3:
            self.logger.error(f"Incorrect number of parameters in DBHelper: at least 3 is needed")
            return False

        
        session = Session(self.engine)
        
        try:
            parameter = kwargs["table"]
            
            table = self.Player if parameter == "player" else self.Team

            query = session.query(table)

            # we also need to check for country if it is a player
            if parameter == "player":
                countryQuery = session.query(self.Team)
                if playerCountry not in countryInDB:
                    countryQuery = countryQuery.filter_by(team_name = playerCountry, country = playerCountry)
                
                    countryResult = countryQuery.all()
                    
                    # if country is in the db, we record its id if country name is not in the mapping dict
                    if countryResult:
                        for aCountry in countryResult:
                            if aCountry.team_name not in countryInDB.keys():
            
                                countryInDB[aCountry.team_name] = aCountry.team_id

                    else:
                        countryNotInDB.add((playerCountry,playerCountry))
                    
            # create query using kwargs except the value with key "table"
            for key, value in kwargs.items():
                if key != "table":
                    query = query.filter_by(**{key:value})
                
            # db query
            result = query.all()

                
            # 1 player/team is found in the db
            if len(result) == 1:
                
                id = result[0].player_id if parameter == "player" else result[0].team_id
                session.commit()
                session.close()
                return id

            # multiple item are found
            elif len(result) > 1:
                pri = []
                for r in result:
                    pri.append(r.player_name if parameter == "player" else r.team_name)
                self.logger.error(f"more than one items are found in the table {pri}")
                session.commit()
                session.close()
                return False

            # no item found
            else:
                session.commit()
                session.close()
                return False
            

        except Exception as e:
            self.logger.error(f"Cannot check item in db: {e}")
            session.rollback()
            session.commit()
            session.close()
            return False

    def getTeam(self, teamName, country):

        session = Session(self.engine)
        try:
            table = self.Team
            result = session.query(table).filter_by(team_name=teamName, country=country).first()
            
            if result:
                team = {
                    "team_id":result.team_id, 
                    "team_name":result.team_name, 
                    "country":result.country
                    }
                session.close()
                return team
            else:
                session.close()
                return None
        except Exception as e:
            session.rollback()
            session.close()
            self.logger.error(f"failed to query for team at getTeam: {repr(e)}")
            return None


    # def aggregate_group(self, group):
    #     #TODO drop columns, keep only columns related to player stats + more
    #     print(group.columns)
    #     a = self.Match.__table__.c
    #     home_players = {name: group[group['player_name'] == name].drop(columns=['player_name']).to_dict(orient='records')[0]
    #                 for name in group['player_name'][group['team_id'] == group['homeTeam_id']].unique()}
    
    #     away_players = {name: group[group['player_name'] == name].drop(columns=['player_name']).to_dict(orient='records')[0]
    #                 for name in group['player_name'][group['team_id'] == group['awayTeam_id']].unique()}

    #     return pd.Series({"players": {group["home_team_name"].iloc[0]: home_players, group["away_team_name"].iloc[0]: away_players}})


    def aggregate_group(self, group):
        # Define relevant player stat columns
        playerStatCol = [col.name for col in self.PlayerStats.__table__.c]

        # player_stat_columns = [col for col in group.columns if col not in playerStatCol]
        # print(player_stat_columns)
        # keep wanted columns upfront
        group = group[['player_name',"team_id","homeTeam_id","awayTeam_id","home_team_name","away_team_name"] + playerStatCol]
        # Convert data to a dictionary indexed by player_name
        player_data = group.set_index('player_name').to_dict(orient='index')

        # Separate home and away players
        home_players = {
            # filter out key "homeTeam_id" and "awayTeam_id" (not needed in playerstats)
            # for player name in the player_name column where the team id is the home team, make it as the new
            # dict key with value as the player stat value without the "homeTeam_id" and "awayTeam_id" 
            name: {key: val for key, val in player_data[name].items() if key not in ["homeTeam_id", "awayTeam_id"]}
            for name in group['player_name'][group['team_id'] == group['homeTeam_id']].unique()
        }
        away_players = {
            name: {key: val for key, val in player_data[name].items() if key not in ["homeTeam_id", "awayTeam_id"]}
            for name in group['player_name'][group['team_id'] == group['awayTeam_id']].unique()
        }

        # away_players = {name: player_data[name] for name in group['player_name'][group['team_id'] == group['awayTeam_id']].unique()}

        # Construct the result as a Pandas Series
        result = pd.Series({
            "players": {
                group["home_team_name"].iloc[0]: home_players,
                group["away_team_name"].iloc[0]: away_players
            }
        })

        return result


    def getTeamPastMatch(self, teamInfo, noOfMatches:int=None, year:int=None):

        team = self.getTeam(teamInfo[0], teamInfo[1])
        session = Session(self.engine)
        
        try:
            if team:
                # Create aliases for the Team table to join it twice (once for homeTeam and once for awayTeam)
                HomeTeam = aliased(self.Team, name='home_team')
                AwayTeam = aliased(self.Team, name='away_team')
                # uses the Core layer and returns raw data rows.
                # so we can convert it to dict later easily
                query = session.query(
                    self.PlayerStats.__table__, 
                    self.Player.__table__, 
                    self.Match.__table__, 
                    HomeTeam.team_name.label('home_team_name'), # we want team name only here
                    AwayTeam.team_name.label('away_team_name')
                )
                query = query.select_from(self.PlayerStats)
                query = query.join(self.Player)
                query = query.join(self.Match)
                
                query = query.filter(or_(self.Match.homeTeam_id==team["team_id"], self.Match.awayTeam_id==team["team_id"]))
                query = query.join(HomeTeam, self.Match.homeTeam_id == HomeTeam.team_id)
                query = query.join(AwayTeam, self.Match.awayTeam_id == AwayTeam.team_id)

                if year:
                    query = query.filter(func.extract("year", self.Match.date) == year)
                
                if noOfMatches:
                    query = query.limit(noOfMatches)

                results = query.all()

                
                allMatchesResults = {}
                matchCol = [column.name for column in self.Match.__table__.c]
                df = pd.DataFrame(results)

                # Use DataFrame.columns.duplicated() to drop duplicate columns
                df = df.loc[:,~df.columns.duplicated()].copy()
                playerCol = df.groupby(matchCol).apply(self.aggregate_group).reset_index()

                with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
                    print(playerCol)


        except Exception as e:
            session.close()
            self.logger.error(f"failed to get match data at getTeamPastMatch {repr(e)}")



                
        
        
