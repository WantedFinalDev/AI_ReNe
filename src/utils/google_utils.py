import os, gspread
import pandas as pd
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Literal
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


## 인증 처리 함수
def auth(credentials_file:str) -> Credentials:
    """Google API를 사용하기 위한 사용자 인증을 처리합니다.
    token.json 파일이 있는지 확인합니다. 있다면 유효하고, 없거나 만료되었다면
    credentials.json 을 사용해 사용자에게 브라우저를 통한 로그인을 요청합니다.
    로그인에 성공하면 새로운 인증 정보를 token.json 파일로 저장하고 
    Credentials 객체를 반환합니다."""
    creds : Credentials | None = None

    # creds: Optional[Credentials] = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # 유효한 인증 정보가 없으면, 사용자에게 로그인을 요청
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 다음 실행을 위해 인증 정보를 저장합니다.
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    return creds