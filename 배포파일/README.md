# 배포파일 구조 정리

이 폴더는 **와일드리프트 코치 앱 실제 실행본**입니다.

## 실행 파일

### 1) 전체 실행
- `시작.py`
- 프리게임 → 추천 → 인게임 순서로 전체 앱 실행

### 2) 인게임만 실행
- `시작(중간부터).py`
- 프리게임을 건너뛰고 인게임 OCR/분석 화면만 실행

---

## 폴더 역할

### `Data/`
정적 데이터 보관용 폴더입니다.
- 챔피언
- 아이템
- 룬
- 스펠
- 한글 번역 JSON

### `core/`
실제 게임 분석/추천 핵심 로직입니다.

- `flow/`  
  단계별 실행 흐름 관리
  - `pregame_flow.py`
  - `ingame_flow.py`

- `logic/`  
  추천 판단 로직
  - 픽 추천
  - 카운터 추천
  - 빌드 추천

- `model/`  
  입력/상태 데이터 구조

- `data/`  
  JSON 로딩, 이름 변환, 매핑 관련

- `utils/`  
  문자열 정리, 출력 포맷 등 공통 유틸

- `vision/`  
  이미지 인식 전용
  - 밴픽 인식
  - ROI 추출
  - 자동 입력

### `device/`
이미지 입력 경로/스크린샷 폴더 관련 처리

### `ui/`
Tkinter 화면 구성

- `controller/`  
  버튼 클릭, 단계 전환, 실행 제어

- `view/`  
  실제 화면 위젯 구성

### `gpt/`
GPT 호출 또는 프롬프트 관련 코드가 들어가는 위치

### `server/`
서버 연동용 실험 코드 또는 확장용 폴더

---

## 실제 실행 흐름

### 전체 실행 흐름
1. `시작.py`
2. `ui/controller/coach_controller.py`
3. `ui/controller/pregame_controller.py`
4. `core/flow/pregame_flow.py`
5. 프리게임 추천 완료 후
6. `ui/controller/ingame_controller.py`
7. `core/flow/ingame_flow.py`

### 인게임 단독 실행 흐름
1. `시작(중간부터).py`
2. `ui/controller/ingame_controller.py`
3. `core/flow/ingame_flow.py`

---

## 지금 기준으로 중요한 파일

### 프리게임 핵심
- `ui/controller/pregame_controller.py`
- `ui/view/coach_view.py`
- `core/flow/pregame_flow.py`
- `core/vision/pregame_pick_detector.py`

### 인게임 핵심
- `ui/controller/ingame_controller.py`
- `ui/view/ingame_view.py`
- `core/flow/ingame_flow.py`
- `device/device_state.py`
- `device/capture.py`

---

## 정리 기준

앞으로는 아래 기준으로 유지하면 됩니다.

- 실행 파일은 `시작*.py`만 둔다
- 화면은 `ui/view`
- 클릭/단계 제어는 `ui/controller`
- 실제 추천/판단은 `core/logic`
- 단계 흐름은 `core/flow`
- 이미지 인식은 `core/vision`
- 데이터 로딩/이름 변환은 `core/data`

---

## 다음 정리 후보

1. 안 쓰는 파일 제거
2. vision 관련 파일 한 폴더로 더 정리
3. config 파일 분리
4. 경로 상수 통합
5. OCR/밴픽 ROI 설정 분리
