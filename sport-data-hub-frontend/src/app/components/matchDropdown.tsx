'use client';

import { useState, useEffect } from "react";
import axios, {AxiosResponse, AxiosError} from "axios";
import { Match, MatchDetails } from "@/app/types/interfaces";
import  MatchDetailsTable  from "@/app/components/table"



// match dropdown component
export default function MatchDropdown() {

  //initial value: empty array, and null
  const [matches, setMatches] = useState<Match[]>([]);                      //matches stores an array of Match data fetched from API
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);  //selectedMatch stores the ID of the match chosen by user

  const [leagues, setLeague] = useState<string[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>("default");
                                                                            

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/football/api/returnScheduledMatches/0")
      .then((response: AxiosResponse<Match[]>) => {

        const formattedMatches = response.data.map((match: any) => {
          const timestampInMs = match.startTimestamp * 1000;
          const formattedDate  = new Date(timestampInMs).toLocaleString("en-AU", { timeZone: "Australia/Perth" }); // ✅ Store formatted date
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
    <div className="relative">
      <select
        onChange={(e) => {
          const match = matches.find(m => m.name === e.target.value);
          setSelectedMatch(match || null);
          setSelectedLeague(match ? match.leagueName : "default")
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
          console.log(e.target.value)

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

      {/* if a match is selected, render MatchDetailsComponent with matchId prop */}
      {selectedMatch && <MatchDetailsComponent match={selectedMatch} />}
    </div>
  );
}

// Fetch match details when selected
const MatchDetailsComponent: React.FC<{ match: Match }> = ({ match }) => {
  const [matchData, setMatchData] = useState<MatchDetails[] | null>(null);

  useEffect(() => {
    axios.get(`http://127.0.0.1:8000/football/api/returnTeamPastMatches/?team=${match.home_team}&country=${match.home_country}`) // Axios GET request
      .then((response: AxiosResponse<MatchDetails[]>) => setMatchData(response.data)) // Axios auto-parses JSON
      .catch((error: AxiosError) => console.error("Error fetching matches:", error));
    }, [match]);

  return matchData ? (
    <div className="mt-4 p-4 bg-white shadow rounded">
      <h3 className="text-lg font-bold">Details</h3>
      <MatchDetailsTable matchDetails={matchData} type={["home_shots_target"]} />
    </div>
  ) : (
    <p>Loading match details...</p>
  );
};

//TODO create table for stats, why request twice for stats when first select team after default league - maybe because  useeffect, try onclick?