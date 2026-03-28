# 밴픽

밴픽 화면 스크린샷에서 아군/적군 픽 슬롯을 잘라 저장하는 프로젝트입니다.

## 폴더
- `dataset/raw_screens/pregame`: 원본 밴픽 이미지
- `dataset/champion/canonical`: 챔피언 기준 이미지
- `dataset/champion/pick_crop/ally_picks`: 아군 픽 슬롯 crop
- `dataset/champion/pick_crop/enemy_picks`: 적군 픽 슬롯 crop
- `dataset/debug/preview`: ROI preview

## 실행
```bash
python run.py
```

## 현재 기능
- 밴픽 원본 이미지 읽기
- ally_picks / enemy_picks ROI crop
- 원형 투명 PNG 저장
- preview 이미지 저장
