from aiohttp import BasicAuth, ClientSession
from fastapi import HTTPException

from app.config import settings

BASE_URL = "https://api.github.com"


async def get(*, endpoint: str) -> dict | None:
    """Performs GET request to given endpoint of GitHub API. 

    Returns requested data or None if the data wasn't found.
    """
    async with _default_client() as session:
        async with session.get(endpoint) as response:
           return await _handle_response(response)
            

def _default_client():
    """Creates default client session for requests to GitHub API.

    If GITHUB_USERNAME and GITHUB_TOKEN environment variables are set, 
    then creates authenticated session, which has greater hourly rate limit.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    auth = (
        BasicAuth(settings.github_username, settings.github_token)
        if settings.github_username and settings.github_token
        else None
    )
    return ClientSession(base_url=BASE_URL, auth=auth, headers=headers)


async def _handle_response(response):
    """If request was successful, returns response content. If it wasn't, 
       throws HTTPException with appropriate message and code 503. 
    """
    if response.status == 200:
        return await response.json()
    elif response.status == 404:
        return None
   
    match response.status:
        case 401:
            message = "Bad credentials to GitHub API."
        case 403:
            limit_reached = response.headers['X-RateLimit-Remaining'] == '0'
            message = (
                "Exceeded rate limit to GitHub API."
                if limit_reached
                else "Too many unsuccesful authentication attempts to GitHub API."
            )
        case _:
            message = "Unknown error occured while connecting to GitHub API."
    raise HTTPException(status_code=503, detail=message)
