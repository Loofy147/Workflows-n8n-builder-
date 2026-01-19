"""
Google Sheets Integration Service
Provides common tools for interacting with Google Sheets in workflows.
"""
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """
    Service for interacting with Google Sheets API (via OAuth2 or Webhooks).
    """

    async def append_row(self, sheet_id: str, range_name: str, values: List[Any], token: str) -> bool:
        """
        Appends a row of data to a spreadsheet.
        """
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}:append"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "values": [values]
        }
        params = {
            "valueInputOption": "USER_ENTERED"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, params=params)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to append to Google Sheet: {e}")
            return False

    async def get_values(self, sheet_id: str, range_name: str, token: str) -> Optional[List[List[Any]]]:
        """
        Reads data from a spreadsheet.
        """
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get("values")
        except Exception as e:
            logger.error(f"Failed to read from Google Sheet: {e}")
            return None

google_sheets_service = GoogleSheetsService()
