from aiohttp import ClientSession
from fastapi import HTTPException

BASE_URL = "https://gitlab.com"


async def get(*, endpoint: str) -> dict | None:
    """Performs GET request to given endpoint of GitLab API. 

    Returns requested data or None if the data wasn't found.
    """
    async with _default_client() as session:
        async with session.get("/api/v4" + endpoint) as response:
           return await _handle_response(response)
            

def _default_client():
    """Creates default client session for requests to GitLab API.
    """
    return ClientSession(base_url=BASE_URL)


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
            message = "Bad credentials to GitLab API."
        case 429:
            message = "Exceeded rate limit to GitLab API."
        case 403:
            message = "Too many unsuccesful authentication attempts to GitLab API."
        case _:
            message = "Unknown error occured while connecting to GitLab API."
    raise HTTPException(status_code=503, detail=message)
