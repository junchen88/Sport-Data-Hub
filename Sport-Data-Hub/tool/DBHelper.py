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
            matchID = match.match_id


        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"IntegrityError occurred: The item already exists or violates a constraint.\nError details: {e.orig}")

        try:
            if matchID == None:
                # query for the match ID
                pass

            else:
                # Insert PlayerStats
                player_stats_data = data['player_stats']
                if player_stats_data:
                    for team, playerStats in player_stats_data.items():
                        for player_name, stats in playerStats.items():
                            # player = session.query(self.Player).filter_by(player_name=player_name).first()  # Example query
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
                    
                    if countryResult:
                        for aCountry in countryResult:
                            if aCountry.team_name not in countryInDB.keys():
            
                                countryInDB[aCountry.team_name] = aCountry.team_id

                    else:
                        countryNotInDB.add((playerCountry,playerCountry))
                    

            for key, value in kwargs.items():
                if key != "table":
                    query = query.filter_by(**{key:value})
                

            result = query.all()

                

            if len(result) == 1:
                
                id = result[0].player_id if parameter == "player" else result[0].team_id
                session.commit()
                session.close()
                return id

            elif len(result) > 1:
                pri = []
                for r in result:
                    pri.append(r.player_name if parameter == "player" else r.team_name)
                self.logger.error(f"more than one items are found in the table {pri}")
                session.commit()
                session.close()
                return False

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


