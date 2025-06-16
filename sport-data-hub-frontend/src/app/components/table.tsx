"use client"

import { useState, useEffect } from "react";
import {MatchDetails } from "@/app/types/interfaces";
import { Stats } from "fs";


const MatchDetailsTable: React.FC<{matchDetails:Array<MatchDetails>; type:Array<string>; selectedCountry:string; selectedPlayerStat:string}> = ({ matchDetails, type, selectedCountry, selectedPlayerStat}) => {
  if (!matchDetails) return <p className="text-gray-500">No match details available.</p>;

  matchDetails.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  const playerNames = Object.keys(matchDetails[0].players[selectedCountry]);
  const anyTeam = Object.keys(matchDetails[0]["players"])[0];
  const anyKey = Object.keys(matchDetails[0]["players"][anyTeam])[0];
  const statName = Object.keys(matchDetails[0]["players"][anyTeam][anyKey])
    .filter(stat => !["match_id", "stat_id", "team_id", "home_team_name",	"away_team_name", "player_name"].includes(stat));
  if (type.includes("players")) {
    return (
      <table className="border-collapse border border-gray-400 w-full">
        <thead>
          <tr>
            <th className="border border-gray-300 p-2 capitalize">Player Name</th>
            <th className="border border-gray-300 p-2 capitalize">Team</th>
            
            {Object.keys(matchDetails)
                .map((key) => (
                <th key={key} className="border border-gray-300 p-2 capitalize">
                {key}
                </th>
            ))}            
          </tr>
        </thead>
        <tbody>
          {playerNames.map(playerName => (
          <tr key={playerName}>
            <td className="border border-gray-300 p-2">{playerName}</td>
            <td className="border border-gray-300 p-2">{selectedCountry}</td>
            {matchDetails.map(match => {
              const playerStats = match.players[selectedCountry][playerName] || {}; // Ensure player exists in match
              
              
              return (
              <td key={`${match.match_id}-${selectedPlayerStat}`} className="border border-gray-300 p-2">
                {playerStats[selectedPlayerStat] ?? "-"} {/* Display stats dynamically */}
              </td>
              );
            })}
          </tr>
        ))}
        </tbody>
      </table>
    );
  };
    

  return (
    <table className="border-collapse border border-gray-400 w-full">
      <thead>
        <tr>
            <th className="border border-gray-300 p-2 capitalize">Label</th>
            <th className="border border-gray-300 p-2 capitalize">Country</th>
            {Object.keys(matchDetails)
                .map((key) => (
                <th key={key} className="border border-gray-300 p-2 capitalize">
                {key}
                </th>
            ))}
        
        </tr>
      </thead>
      <tbody>
      {Object.keys(matchDetails[0]) // ✅ Iterate over the first match object to get all possible keys
          .filter((key) => type.includes(key)) // ✅ Apply filtering logic
          .map((key) => (
          <tr key={key}>
            <td className="border border-gray-300 p-2 capitalize">{key.replace(/_/g, " ")}</td>
            <td className="border border-gray-300 p-2 capitalize">{selectedCountry}</td>
            {matchDetails.map((match) => (
              
              // if selected team is home - same colour
              key.includes("home") && match.home_team_name === selectedCountry ? 
              <td key={match.match_id} className="border border-gray-300 p-2 bg-selectedCountry">
                {String(match[key])} 
              </td> :
              // else if selected team is away - same colour
              key.includes("away") && match.away_team_name === selectedCountry ?
              <td key={match.match_id} className="border border-gray-300 p-2 bg-selectedCountry">
                {String(match[key])} 
              </td> :
              //else if general item - not home and away specific
              !key.includes("home") && !key.includes("away") ?
              <td key={match.match_id} className="border border-gray-300 p-2 bg-selectedCountry">
                {String(match[key])} 
              </td> :
              
              // else other colour or no colour since it is not the selected team
              <td key={match.match_id} className="border border-gray-300 p-2">
                {String(match[key])}
              </td>
            ))}
          </tr>
          ))}
      </tbody>
    </table>
  );
};

export default MatchDetailsTable;
