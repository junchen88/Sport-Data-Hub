'use client';

import { useState, useEffect } from "react";
import axios, {AxiosResponse, AxiosError} from "axios";
import { Match, MatchDetails } from "@/app/types/interfaces";
import  MatchDetailsTable  from "@/app/components/table"
import DropdownWithCheckboxes from "@/app/components/dropdownWithCheckboxes"



// match dropdown component
export default function MatchDropdown() {

  //initial value: empty array, and null
  const [matches, setMatches] = useState<Match[]>([]);                      //matches stores an array of Match data fetched from API
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);  //selectedMatch stores the ID of the match chosen by user

  const [leagues, setLeague] = useState<string[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>("default");

  const [countries, setCountries] = useState<string[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>("default");
  const [selectedPlayerStat, setSelectedPlayerStat] = useState<string>("")
                                                                            
  const matchDetailKeys =[
    "yellow_cards",
    "red_cards",
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
    "away_corners",
    "away_fouls",
    "home_corners",
    "home_fouls",
    "players",
  ]

  const playerStatsOptions = [

    "goals_scored",
    "assists",
    "shots",
    "shots_target",
    "fouls_committed",
    "fouls_won",

  ]

  const [selectedStats, setSelectedStats] = useState<string[]>([]); // Add state for selected stats

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/football/api/returnScheduledMatches/0")
      .then((response: AxiosResponse<Match[]>) => {

        const formattedMatches = response.data.map((match: any) => {
          const timestampInMs = match.startTimestamp * 1000;
          const formattedDate  = new Date(timestampInMs).toLocaleString("en-AU", { timeZone: "Australia/Perth" }); // Store formatted date
          return {
            id: match.id,                                     // Mapping id
            date: new Date(timestampInMs).toLocaleString(),   // Mapping start time stamp to date

            // check if both team country is the same, if it's the same add country info after league
            // else: display league name only
            //TODO bug - same team country but not country competition (eg champions league etc)
            leagueName: match.home_country === match.away_country ? `${match.league} (${match.home_country})` : match.league,
            startTimeStampInMS: timestampInMs,
            name: `${formattedDate}: ${match.home} vs ${match.away}`, // Mapping home vs away to name
            home_team:match.home,
            away_team:match.away,
            home_country:match.home_country,
            away_country:match.away_country,
          }
          
        });
      formattedMatches.sort((a, b) => a.startTimeStampInMS - b.startTimeStampInMS);
      setMatches(formattedMatches);
      const uniqueLeagues = Array.from(
        new Set(formattedMatches.map(match => match.leagueName))
      );
      uniqueLeagues.sort()
      setLeague(uniqueLeagues)
      })
      .catch((error: AxiosError) => console.error("Error fetching matches:", error));
    }, []);

  return (
    <div className="relative gap-x-4">
      <select
        onChange={(e) => {
          const match = matches.find(m => m.name === e.target.value);
          setSelectedMatch(match || null);
          setSelectedLeague(match ? match.leagueName : "default")
          setCountries(match?[match.home_team, match.away_team]:[])
          setSelectedCountry(match? match.home_country:"default")
        }}
        className="p-2 border rounded bg-gray-200"
        name="matchDropdown"
        value={selectedMatch?selectedMatch.name : ""}
      >
        <option value="">Select a match...</option>
        {selectedLeague === "default" ? (
          matches.map(match => (
            <option key={match.name} value={match.name}>
              {match.name}
            </option>
          ))) : (
          matches.filter(match => match.leagueName === selectedLeague).map(match => (
            <option key={match.name} value={match.name}>
              {match.name}
            </option>
          ))
          )
        }

      </select>
      <select 
        name="leagueDropdown" id="leagueDropdown" className="p-2 border rounded bg-gray-200"
        value={selectedLeague}
        onChange={(e) => {

          setSelectedLeague(e.target.value)
          if (e.target.value === "default") {

            setSelectedMatch(null);
          }          
        }}
      >
        <option key="default" value="default">Select a League...</option>
        {
          leagues.map(
            (league) => (
              <option key={league} value={league}>
                {league}
              </option>
            )

          )
        
        }
      </select>
      {<DropdownWithCheckboxes options={matchDetailKeys} setSelectedOptions={setSelectedStats}/>}

      <select 
        name="countryDropdown" id="countryDropdown" className="p-2 border rounded bg-gray-200"
        value={selectedCountry}
        onChange={(e) => {
          setSelectedCountry(e.target.value)
        }}
      >
        <option key="" value="">Select a Country/Team...</option>
        {
          countries.map(
            (country) => (
              <option key={country} value={country}>
                {country}
              </option>
            )
          )
        }
      </select>
      {selectedStats.includes("players") && <PlayerStatsDropDown playerStatsOptions={playerStatsOptions} selectedPlayerStat={selectedPlayerStat} setSelectedPlayerStat={setSelectedPlayerStat}/>}

      {/* if a match is selected, render MatchDetailsComponent with matchId prop */}
      {selectedMatch && <MatchDetailsComponent match={selectedMatch} selectedStats={selectedStats} selectedCountry={selectedCountry} selectedPlayerStat={selectedPlayerStat}/>}
    </div>
  );
}

const PlayerStatsDropDown: React.FC<{playerStatsOptions: string[], selectedPlayerStat:string; setSelectedPlayerStat:(selectedPlayerStat: string) => void}>=({playerStatsOptions, selectedPlayerStat, setSelectedPlayerStat}) => (
  <select 
    name="playerDropdown" id="playerDropdown" className="p-2 border rounded bg-gray-200"
    value={selectedPlayerStat}
    onChange={(e) => {
      setSelectedPlayerStat(e.target.value)
    }}
  >
    <option key="" value="">Select a Player Stat</option>
    {
      playerStatsOptions.map(
        (playerStatsOption) => (
          <option key={playerStatsOption} value={playerStatsOption}>
            {playerStatsOption}
          </option>
        )
      )
    }
  </select>
)

// Fetch match details when selected
const MatchDetailsComponent: React.FC<{ match: Match; selectedStats: string[]; selectedCountry:string; selectedPlayerStat:string}> = ({ match, selectedStats, selectedCountry, selectedPlayerStat}) => {
  const [homeMatchData, setHomeMatchData] = useState<MatchDetails[] | null>(null);
  const [awayMatchData, setAwayMatchData] = useState<MatchDetails[] | null>(null);

  useEffect(() => {
    axios.get(`http://127.0.0.1:8000/football/api/returnTeamPastMatches/?team=${match.home_team}&country=${match.home_country}`) // Axios GET request
      .then((response: AxiosResponse<MatchDetails[]>) => setHomeMatchData(response.data)) // Axios auto-parses JSON
      .catch((error: AxiosError) => console.error("Error fetching matches:", error));
    }, [match]);
  
  useEffect(() => {
    axios.get(`http://127.0.0.1:8000/football/api/returnTeamPastMatches/?team=${match.away_team}&country=${match.away_country}`) // Axios GET request
      .then((response: AxiosResponse<MatchDetails[]>) => setAwayMatchData(response.data)) // Axios auto-parses JSON
      .catch((error: AxiosError) => console.error("Error fetching matches:", error));
    }, [match]);

  const matchData = match.home_team === selectedCountry ? homeMatchData : match.away_team === selectedCountry ?  awayMatchData : null;
  // console.log(awayMatchData);
  return matchData ? (
    <div className="mt-4 p-4 bg-white shadow rounded">
      <h3 className="text-lg font-bold capitalize">Details: {selectedPlayerStat.replace(/_/g, " ")}</h3>
      <MatchDetailsTable matchDetails={matchData||[]} type={selectedStats} selectedCountry={selectedCountry} selectedPlayerStat={selectedPlayerStat}/>
    </div>
  ) : selectedCountry ? (<p>Please select a country/team...</p>):
  
  (
    <p>Loading match details...</p>
  );
};

//TODO create table for stats, why request twice for stats when first select team after default league - maybe because  useeffect, try onclick?