"use client"

import { useState, useEffect } from "react";
import {MatchDetails } from "@/app/types/interfaces";
import { Stats } from "fs";


const MatchDetailsTable: React.FC<{matchDetails:Array<MatchDetails>; type:Array<string>; homeTeam:string; awayTeam:string; selectedCountry:string}> = ({ matchDetails, type, homeTeam, awayTeam, selectedCountry}) => {
  if (!matchDetails) return <p className="text-gray-500">No match details available.</p>;
  
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

// #TODO add another dropdownbox to select relevant stats wanted, can select multiple Stats, player stats can only select as single option