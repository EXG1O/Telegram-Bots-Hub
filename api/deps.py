from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from core.settings import TOKEN

from typing import Annotated

api_key_header_auth = APIKeyHeader(name='X-API-KEY')


async def verify_api_key(api_key: Annotated[str, Depends(api_key_header_auth)]) -> str:
	if api_key != TOKEN:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

	return api_key
