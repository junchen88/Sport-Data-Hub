// Define types for the match data
export interface Match {
    id: string;
    leagueName:string;
    home_team:string;
    away_team:string;
    home_country:string;
    away_country:string;
    name: string;
    startTimeStampInMS: number;
    date: string;
  }
  
  export interface MatchDetails {
    match_id:number,
    date:object,
    yellow_cards:number,
    red_cards:number,
    home_shots:number,
    away_shots:number,
    home_shots_target:number,
    away_shots_target:number,
    awayTeam_id:number,
    homeTeam_id:number,
    league:string,
    away_corners:number,
    away_fouls:number,
    home_corners:number,
    home_fouls: number,
    players: Record<string, any>; // ✅ JSON should be defined explicitly;
    [key: string]: string | number | Record<string, any>; // ✅ Ensure dynamic key indexing supports objects
  }