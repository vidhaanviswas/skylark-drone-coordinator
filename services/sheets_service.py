"""Google Sheets integration service."""

import os
import json
from typing import Optional, List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd


class SheetsService:
    """Service for syncing data with Google Sheets."""
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        pilot_sheet_id: Optional[str] = None,
        drone_sheet_id: Optional[str] = None,
        mission_sheet_id: Optional[str] = None
    ):
        """
        Initialize the sheets service.
        
        Args:
            credentials_path: Path to Google service account credentials
            pilot_sheet_id: Spreadsheet ID for pilot roster
            drone_sheet_id: Spreadsheet ID for drone fleet
            mission_sheet_id: Spreadsheet ID for missions
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        self.pilot_sheet_id = pilot_sheet_id or os.getenv('PILOT_ROSTER_SHEET_ID')
        self.drone_sheet_id = drone_sheet_id or os.getenv('DRONE_FLEET_SHEET_ID')
        self.mission_sheet_id = mission_sheet_id or os.getenv('MISSIONS_SHEET_ID')
        
        self.pilot_sheet_name = os.getenv('PILOT_ROSTER_SHEET_NAME', 'Pilot Roster')
        self.drone_sheet_name = os.getenv('DRONE_FLEET_SHEET_NAME', 'Drone Fleet')
        self.mission_sheet_name = os.getenv('MISSIONS_SHEET_NAME', 'Missions')
        
        self.service = None
        self.enabled = False
        
        # Only initialize if credentials are available
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')

        # Priority: Streamlit secrets → env
        if SECRETS:
            self.credentials_json = json.dumps(SECRETS.get("gcp_service_account", {}))
            self.pilot_sheet_id = pilot_sheet_id or SECRETS.get("PILOT_ROSTER_SHEET_ID")
            self.drone_sheet_id = SECRETS.get("DRONE_FLEET_SHEET_ID")
            self.mission_sheet_id = SECRETS.get("MISSIONS_SHEET_ID")
        else:
            self.credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
            self.pilot_sheet_id = pilot_sheet_id or os.getenv('PILOT_ROSTER_SHEET_ID')
            self.drone_sheet_id = os.getenv('DRONE_FLEET_SHEET_ID')
            self.mission_sheet_id = os.getenv('MISSIONS_SHEET_ID')

    
    def _initialize_service(self, credentials_json: Optional[str] = None):
        """Initialize the Google Sheets API service."""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        if credentials_json:
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=SCOPES
            )
        
        self.service = build('sheets', 'v4', credentials=credentials)
    
    def read_sheet(self, spreadsheet_id: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Read data from a Google Sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet
        
        Returns:
            DataFrame with the data or None if failed
        """
        if not self.enabled or not self.service:
            return None
        
        try:
            range_name = f'{sheet_name}!A:Z'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # First row is headers
            headers = values[0]
            rows = values[1:]
            normalized_rows = []
            for row in rows:
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                elif len(row) > len(headers):
                    row = row[:len(headers)]
                normalized_rows.append(row)

            df = pd.DataFrame(normalized_rows, columns=headers)
            return df
        
        except HttpError as e:
            print(f"Error reading sheet: {e}")
            return None
    
    def write_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        data: pd.DataFrame
    ) -> bool:
        """
        Write data to a Google Sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet
            data: DataFrame to write
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.service:
            return False
        
        try:
            # Convert DataFrame to list of lists
            safe_data = data.fillna("")
            values = [safe_data.columns.tolist()] + safe_data.values.tolist()
            
            body = {'values': values}
            
            # Clear existing data first
            range_name = f'{sheet_name}!A:Z'
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            # Write new data
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
        
        except HttpError as e:
            print(f"Error writing to sheet: {e}")
            return False
    
    def sync_pilots_from_sheets(self, pilot_service) -> bool:
        """
        Sync pilot data from Google Sheets to local CSV.
        
        Args:
            pilot_service: PilotService instance
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.pilot_sheet_id:
            return False
        
        df = self.read_sheet(self.pilot_sheet_id, self.pilot_sheet_name)
        if df is None:
            return False
        
        # Save to CSV
        df.to_csv(pilot_service.csv_path, index=False)
        pilot_service.load_pilots()
        return True
    
    def sync_pilots_to_sheets(self, pilot_service) -> bool:
        """
        Sync pilot data from local CSV to Google Sheets.
        
        Args:
            pilot_service: PilotService instance
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.pilot_sheet_id:
            return False
        
        data = [pilot.to_dict() for pilot in pilot_service.get_all_pilots()]
        df = pd.DataFrame(data)
        return self.write_sheet(self.pilot_sheet_id, self.pilot_sheet_name, df)
    
    def sync_drones_from_sheets(self, drone_service) -> bool:
        """
        Sync drone data from Google Sheets to local CSV.
        
        Args:
            drone_service: DroneService instance
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.drone_sheet_id:
            return False
        
        df = self.read_sheet(self.drone_sheet_id, self.drone_sheet_name)
        if df is None:
            return False
        
        # Save to CSV
        df.to_csv(drone_service.csv_path, index=False)
        drone_service.load_drones()
        return True
    
    def sync_drones_to_sheets(self, drone_service) -> bool:
        """
        Sync drone data from local CSV to Google Sheets.
        
        Args:
            drone_service: DroneService instance
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.drone_sheet_id:
            return False
        
        data = [drone.to_dict() for drone in drone_service.get_all_drones()]
        df = pd.DataFrame(data)
        return self.write_sheet(self.drone_sheet_id, self.drone_sheet_name, df)

    def sync_missions_from_sheets(self, mission_service) -> bool:
        """
        Sync mission data from Google Sheets to local CSV.

        Args:
            mission_service: MissionService instance

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.mission_sheet_id:
            return False

        df = self.read_sheet(self.mission_sheet_id, self.mission_sheet_name)
        if df is None:
            return False

        # Save to CSV
        df.to_csv(mission_service.csv_path, index=False)
        mission_service.load_missions()
        return True
    
    def sync_missions_to_sheets(self, mission_service) -> bool:
        """
        Sync mission data from local CSV to Google Sheets.
        
        Args:
            mission_service: MissionService instance
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.mission_sheet_id:
            return False
        
        data = [mission.to_dict() for mission in mission_service.get_all_missions()]
        df = pd.DataFrame(data)
        return self.write_sheet(self.mission_sheet_id, self.mission_sheet_name, df)
