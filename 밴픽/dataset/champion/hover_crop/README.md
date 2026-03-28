# 밴픽 프로젝트

## 목적
와일드리프트 밴픽 화면에서
- 챔피언 슬롯 crop
- 역할 아이콘 crop
- UI 상태 구분
을 위한 데이터셋과 파이프라인 구성

## 시작 방법

### 1. 폴더 생성
```bash
python tools/make_folders.py
```

### 2. 원본 이미지 넣기
`dataset/raw_screens/pregame` 폴더에 밴픽 화면 스크린샷 넣기

### 3. 실행
```bash
python run.py
```

### 4. 결과 확인
- ROI 미리보기: `dataset/debug/preview`
- 잘라낸 슬롯 결과:
  - `dataset/champion/hover_crop`
  - `dataset/champion/pick_crop`
  - `dataset/champion/ban_crop`
  - `dataset/role/crop`
