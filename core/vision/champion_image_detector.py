class ChampionImageDetector:
    def detect(self, roi):
        """
        roi: 잘린 챔피언 이미지 (numpy array)
        return: 감지 결과
        예) "Ahri"
        """
        if roi is None:
            return None

        # TODO: 나중에 템플릿 매칭 / 특징 비교 / 분류 모델 넣기
        return "unknown"