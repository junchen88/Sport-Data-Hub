from django.db import models

# keep a table of mapping for next 5 days schedule to map team name and country to id.
# Create your models here.
class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        unique_together = ('team_name', 'country')  # Ensures team_name and country combination is unique
    
    def __str__(self):
        return self.team_name

class Player(models.Model):
    player_id = models.AutoField(primary_key=True)
    player_name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    country = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players_country')
    birth_date = models.DateField()

    class Meta:
        unique_together = ('player_name', 'birth_date')  # Ensure player is unique

    def __str__(self):
        return self.player_name

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    date = models.DateField(db_index=True)
    # venue = models.CharField(max_length=100)
    league = models.CharField(max_length=100)

    # Reverse Accessors: Django creates reverse relationships automatically unless a related_name is provided
    # related_name is needed. eg. ateam.home_matches.all() will return all the past matches played as the home
    # team
    homeTeam = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    awayTeam = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    home_shots = models.IntegerField(default=0)
    away_shots = models.IntegerField(default=0)
    home_shots_target = models.IntegerField(default=0)
    away_shots_target = models.IntegerField(default=0)
    fouls = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['homeTeam', 'date']),  # Index for home_team and date
            models.Index(fields=['awayTeam', 'date']),  # Index for away_team and date
            # Additional indexes can be added as needed
        ]

    def __str__(self):
        return f"{self.date} - {self.league} - {self.homeTeam} vs {self.awayTeam} - {self.venue}"

    class Meta:
        unique_together = ('date', 'league', 'homeTeam', 'awayTeam')  # Ensure each player has stats only once per match


    
class PlayerStats(models.Model):
    stat_id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    goals_scored = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)
    shots_target = models.IntegerField(default=0)
    fouls_committed = models.IntegerField(default=0)
    fouls_won = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.match} - {self.player.player_name}"

    class Meta:
        unique_together = ('match', 'player')  # Ensure each player has stats only once per match