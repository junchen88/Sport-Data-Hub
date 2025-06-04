"use client"

import { useState, useEffect } from "react";
import {MatchDetails } from "@/app/types/interfaces";
import { Stats } from "fs";


const MatchDetailsTable: React.FC<{matchDetails:Array<MatchDetails>; type:Array<string>}> = ({ matchDetails, type}) => {
  if (!matchDetails) return <p className="text-gray-500">No match details available.</p>;
  {console.log(Object.keys(matchDetails[0]).filter((key) => type.includes(key)))}
  
  return (
    <table className="border-collapse border border-gray-400 w-full">
      <thead>
        <tr>
            <th className="border border-gray-300 p-2 capitalize">Label</th>
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
            {matchDetails.map((match) => (
              <td key={match.match_id} className="border border-gray-300 p-2">
                {String(match[key])} {/* ✅ Populate match data */}
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