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
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    country = models.ForeignKey(Team, on_delete=models.CASCADE)


    def __str__(self):
        return self.player_name

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    date = models.DateField(db_index=True)
    venue = models.CharField(max_length=100)
    homeTeam = models.ForeignKey(Team, on_delete=models.CASCADE)
    awayTeam = models.ForeignKey(Team, on_delete=models.CASCADE)
    stat_id = models.AutoField(primary_key=True)
    yellow_cards = models.IntegerField(default=0)
    red_cards = models.IntegerField(default=0)
    home_shots = models.IntegerField(default=0)
    away_shots = models.IntegerField(default=0)
    home_shots_target = models.IntegerField(default=0)
    away_shots_target = models.IntegerField(default=0)
    fouls = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['home_team', 'date']),  # Index for home_team and date
            models.Index(fields=['away_team', 'date']),  # Index for away_team and date
            # Additional indexes can be added as needed
        ]

    def __str__(self):
        return f"{self.date} - {self.country.country_name} - {self.venue}"


    
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