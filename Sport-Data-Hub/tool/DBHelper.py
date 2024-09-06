from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import os
from django.conf import settings
import datetime
import logging
from sqlalchemy.exc import IntegrityError

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


