# Sport-Data-Hub
Website for displaying stats for sports like football, AFL, etc

## TODO:
1. Add yellow and red card for players. eg need to get from this link: https://www.sofascore.com/api/v1/event/12450881/incidents. This will add script run time.
2. Doesn't have venue information if using football homepage to scrape, need to go to individual matches page. Can add this if wanted, but this increases script run time
`venue": f"{matchJsonData['venue']['stadium']['name']}, ({matchJsonData['venue']['city']['name']}, {matchJsonData['venue']['country']['name']})`
3. Add comment, then work on check db before scraping, and check for player club status/changes