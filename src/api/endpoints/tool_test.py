import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from utils.google_utils import spreadsheet_to_dataframe, GResult, MimeType, mkfile, auth, append_datas_to_spreadsheet
import gspread
from langchain_openai import ChatOpenAI
from google.oauth2.service_account import Credentials
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException

app = FastAPI(title="Meeting Log Automation API")

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, verbose=True)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

current_path = Path(__file__).resolve()
PROJECT_ROOT = current_path.parent.parent.parent.parent
CREDENTIALS_FILE_PATH = PROJECT_ROOT / 'credentials.json'
print(CREDENTIALS_FILE_PATH)

def tool_result(result : GResult):
    return (
        f" RESULT = {result.result}\n"
        f" MESSAGE = {result.message}\n"
        f" ID = {result.id}\n"
        f" NAME = {result.file}\n"
        f" LINK = {result.link}"
        )

def read_transcript_from_path(file_path: str):
    """ 로컬 경로에서 텍스트 파일을 읽습니다. """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except FileNotFoundError as e:
        print(f"해당 파일을 찾을 수 없습니다: {e}")
        return None
    except Exception as e:
        print(f"파일을 로드 중 오류가 발생했습니다: {e}")
        return None



def parse_with_team_meeting(text_to_parsing: str):
    """ GPT를 이용해 회의 텍스트를 요약 및 JSON 형식으로 파싱 합니다. """

    system_prompt = """
    당신은 전문 회의록을 분석하여 Google Sheets에 입력할 데이터를 추출하는 전문 어시스턴트입니다.
    회의록을 분석하여 다음 JSON 구조에 맞춰 "전역", "AI", "언리얼"의 DONE, TO DO, ISSUE 사항을 추출해야합니다.
    - 각각 AI 팀과 언리얼 팀 별로 항목을 분리해야합니다.
    - 이미 한 일, 할 일, 이슈 사항의 분리를 명확히 해야합니다.
    - AI(서버), 언리얼(클라이언트) 팀의 업무 항목을 명확히 구분해주세요.
    - 언급된 내용이 없으면 빈 문자열("") 이나 빈 리스트([])로 채워주세요.
    - 회의 날짜를 "YYYY.MM.DD" 형식으로 추출해야 합니다.
    - AI 팀은 3명이고, 언리얼 팀은 3명인걸 명심해주세요.
    - **최대한 원본 회의록의 내용을 보존한 채**로 요약 & 파싱해야 합니다.
    - task는 작업의 핵심만 담아서 작업의 **키워드만 나열**하는 식으로, **최대한 간결하게 작성**해야 합니다.
    - "name" 키의 값은 고정입니다. 변경하지 마세요.

    반드시 다음 JSON 형식으로만 응답해야 합니다:
    {{
    "global": {{
        "일자": "회의록에 적힌 일자",
        "구분": "전역",
        "DONE": "팀원 전체가 완료한 일 요약",
        "TO DO": "팀원 전체가 해야 할 일 요약",
        "ISSUE": "팀원 전체의 이슈 사항 요약"
    }},
    "ai_team": {{
        "일자": "회의록에 적힌 일자",
        "구분": "AI",
        "DONE": [
        {{"name": "업무 1", "task": "완료한 작업 내용"}},
        {{"name": "업무 2", "task": "완료한 작업 내용"}},
        {{"name": "업무 3", "task": "완료한 작업 내용"}}
        ],
        "TO DO": [
        {{"name": "업무 1", "task": "해야할 작업 내용"}},
        {{"name": "업무 2", "task": "해야할 작업 내용"}},
        {{"name": "업무 3", "task": "해야할 작업 내용"}}
        ],
        "ISSUE": [
        {{"name": "이슈 1", "task": "발생한 이슈 내용"}},
        {{"name": "이슈 2", "task": "발생한 이슈 내용"}},
        {{"name": "이슈 3", "task": "발생한 이슈 내용"}}
        ]
    }},
    "unreal_team": {{
        "일자": "회의록에 적힌 일자",
        "구분": "언리얼",
        "DONE": [
        {{"name": "업무 1", "task": "완료한 작업 내용"}},
        {{"name": "업무 2", "task": "완료한 작업 내용"}},
        {{"name": "업무 3", "task": "완료한 작업 내용"}}
        ],
        "TO DO": [
        {{"name": "업무 1", "task": "해야할 작업 내용"}},
        {{"name": "업무 2", "task": "해야할 작업 내용"}},
        {{"name": "업무 3", "task": "완료한 작업 내용"}}
        ],
        "ISSUE": [
        {{"name": "이슈 1", "task": "발생한 이슈 내용"}},
        {{"name": "이슈 2", "task": "발생한 이슈 내용"}},
        {{"name": "이슈 3", "task": "완료한 작업 내용"}}
        ]
    }}
    }}
    """

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_prompt),
            ('user', '{content}')
        ]
    )

    chain = chat_prompt | llm | JsonOutputParser()
    response = chain.invoke({
        "content": text_to_parsing
    })

    #print(response)
    return response

def parse_with_mentoring(text_to_parsing: str):
    """ GPT를 이용해 멘토링 회의 텍스트를 요약 및 JSON 형식으로 파싱 합니다. """

    system_prompt = """
    당신은 전문 멘토링 회의록을 분석하여 Google Sheets에 입력할 데이터를 추출하는 전문 어시스턴트입니다.
    회의록을 분석하여 다음 JSON 구조에 맞춰 멘토링  DONE, TO DO, ISSUE 사항을 추출해야합니다.
    해당 회의록은 두명의 멘토가 현재 프로젝트 진행 현황을 듣고 피드백 사항과 해야할 일을 알려주는 회의록입니다.
    - 각각 AI 팀과 언리얼 팀 별로 항목을 분리해야합니다.
    - 이미 한 일, 할 일, 이슈 사항의 분리를 명확히 해야합니다.
    - AI(서버), 언리얼(클라이언트) 팀의 업무 항목을 명확히 구분해주세요.
    - 언급된 내용이 없으면 빈 문자열("") 이나 빈 리스트([])로 채워주세요.
    - 회의 날짜를 "YYYY.MM.DD" 형식으로 추출해야 합니다.
    - **최대한 원본 회의록의 내용을 보존한 채**로 요약 & 파싱해야 합니다.
    - task는 작업의 핵심만 담아서 작업의 **키워드만 나열**하는 식으로, **최대한 간결하게** 작성해야 합니다.
    - "name" 키의 값은 고정입니다. 변경하지 마세요.

    반드시 다음 JSON 형식으로만 응답해야 합니다:
    {{
    "mentoring": {{
        "일자": "회의록에 적힌 일자",
        "구분": "멘토링",
        "DONE": [
        {{"name": "AI", "task": "AI 팀에서 현재 완료한 작업 내용"}},
        {{"name": "언리얼", "task": "언리얼 팀에서 현재 완료한 작업 내용"}}
        ],
        "TO DO": [
        {{"name": "AI", "task": "AI 팀의 멘토링을 통해 정해진 해야할 일"}},
        {{"name": "언리얼", "task": "언리얼 팀의 멘토링을 통해 정해진 해야할 일"}}
        ],
        "ISSUE": [
        {{"name": "AI, "task": "AI 팀의 멘토링 중 나온 이슈 내용"}},
        {{"name": "언리얼", "task": "언리얼 팀의 멘토링 중 나온 이슈 내용"}}
        ]
    }},
    }}
    """

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system_prompt),
            ('user', '{content}')
        ]
    )

    chain = chat_prompt | llm | JsonOutputParser()
    response = chain.invoke({
        "content": text_to_parsing
    })

    #print(response)
    return response


def format_for_team_tasks(task_list: list):
    """
    [{'name': '이름', 'task': '할일'}, ...] 형태의 리스트를
    '- (이름) 할일\n- (이름) 할일' 형태의 문자열로 변환합니다.
    """
    if not task_list: return ""

    formatted_lines = []
    for idx, item in enumerate(task_list):
        name = item.get('name', '').strip()
        task = item.get('task', '').strip()

        if name or task:
            line = f"- ({name}) {task}"
            formatted_lines.append(line)

    return "\n".join(formatted_lines)        

def update_daily_team_meeting_to_sheet(response: dict) -> str:
    try:
        creds = auth(credentials_file=CREDENTIALS_FILE_PATH)    
        path_name = 'Daily Mentoring Notes(언리얼 트랙 & AI 트랙 융합_6조)'
        sheet_name = 'Notes' 
        
        # 1. Spreadsheet 파일 찾기 혹은 생성
        file_result = mkfile(creds, path_name, MimeType.spreadsheet)
        if not file_result.id:
            return {"error": "스케줄 파일을 찾거나 생성할 수 없습니다."}
            
        # 2. 데이터 가공 (List of Lists 생성)
        # 시트 컬럼 순서 [일자, 구분(팀명), DONE, TO DO, ISSUE]
        rows_to_add = []
        
        # (1) Global 데이터 처리
        g_data = response.get('global', {})
        rows_to_add.append([
            g_data.get('일자', ''),
            '전역', # 구분
            g_data.get('DONE', ''),
            g_data.get('TO DO', ''),
            g_data.get('ISSUE', '')
        ])
        
        # (2) AI Team 데이터 처리
        ai_data = response.get('ai_team', {})
        rows_to_add.append([
            ai_data.get('일자', ''),
            'AI', # 구분
            format_for_team_tasks(ai_data.get('DONE', [])),
            format_for_team_tasks(ai_data.get('TO DO', [])),
            format_for_team_tasks(ai_data.get('ISSUE', []))
        ])
        
        # (3) Unreal Team 데이터 처리
        ur_data = response.get('unreal_team', {})
        rows_to_add.append([
            ur_data.get('일자', ''),
            '언리얼', # 구분
            format_for_team_tasks(ur_data.get('DONE', [])),
            format_for_team_tasks(ur_data.get('TO DO', [])),
            format_for_team_tasks(ur_data.get('ISSUE', []))
        ])

        # 3. 시트에 데이터 추가 요청
        results = append_datas_to_spreadsheet(creds, file_result.id, sheet_name, rows_to_add)
        
        return tool_result(results)
    
    except Exception as e:
        import traceback
        return f"Error in update_daily_report_to_sheet: {str(e)}\n{traceback.format_exc()}"
    
def update_daily_mentoring_to_sheet(response: dict) -> str:
    try:
        creds = auth(credentials_file=CREDENTIALS_FILE_PATH)    
        path_name = 'Daily Mentoring Notes(언리얼 트랙 & AI 트랙 융합_6조)'
        sheet_name = 'Notes' 
        
        # 1. Spreadsheet 파일 찾기 혹은 생성
        file_result = mkfile(creds, path_name, MimeType.spreadsheet)
        if not file_result.id:
            return {"error": "스케줄 파일을 찾거나 생성할 수 없습니다."}
            
        # 2. 데이터 가공 (List of Lists 생성)
        # 시트 컬럼 순서 [일자, 구분(팀명), DONE, TO DO, ISSUE]
        rows_to_add = []

        # 멘토링 데이터 처리
        mentoring_data = response.get('mentoring', {})
        rows_to_add.append([
            mentoring_data.get('일자', ''),
            '멘토링', # 구분
            format_for_team_tasks(mentoring_data.get('DONE', [])),
            format_for_team_tasks(mentoring_data.get('TO DO', [])),
            format_for_team_tasks(mentoring_data.get('ISSUE', []))
        ])
        

        # 3. 시트에 데이터 추가 요청
        results = append_datas_to_spreadsheet(creds, file_result.id, sheet_name, rows_to_add)
        
        return tool_result(results)
    
    except Exception as e:
        import traceback
        return f"Error in update_daily_report_to_sheet: {str(e)}\n{traceback.format_exc()}"
    
# @app.post("/upload-meeting-log")
# async def upload_meeting_log(file: UploadFile = File(...)):
#     """
#     회의록 텍스트 파일을 업로드 하면 요약 후 포맷팅하여 구글 시트에 업로드합니다.
#     """

#     # 1. 파일 확장자 검사
#     if not file.filename.endswith(".txt"):
#         raise HTTPException(status_code=400, detail="")

if __name__ == "__main__":
    team_meeting = read_transcript_from_path("data/2025_11_19_회의록.txt")
    print(team_meeting)
    response = parse_with_team_meeting(team_meeting)
    print(response)
    result = update_daily_team_meeting_to_sheet(response)
    print(result)

    mentoring = read_transcript_from_path("data/2025_11_19_멘토링.txt")
    print(mentoring)
    response = parse_with_mentoring(mentoring)
    print(response)
    result = update_daily_mentoring_to_sheet(response)
    print(result)



