# 방법론

## 표상 비교

각 이미지 i에 대해 FlyVis의 뉴런 활동 특징 `F_i`와 EEG 특징 `E_i`를 만듭니다. 각 특징 공간 안에서 이미지 쌍 간 correlation distance를 계산해 `R_F`, `R_E`를 얻고, 상삼각 원소의 Spearman 상관을 요약합니다. EEG 채널과 FlyVis 세포는 일대일로 대응시키지 않습니다.

## FlyVis → EEG 매핑

추가 학습 목표는 `F_i → E_i`입니다. 즉, 이미지 자극과 FlyVis 반응을 입력으로 받아 인간 EEG 채널 특징을 예측합니다. 첫 baseline은 선형 kernel ridge regression입니다. 고차원 FlyVis 세포 특징을 직접 거대한 가중치 행렬로 풀지 않고, 이미지 수 크기의 dual kernel 행렬을 풉니다.

- 5-fold 분할 단위는 이미지 ID입니다. 같은 이미지의 여러 EEG 시행은 fold 분할 전에 평균하므로 반복 시행이 train/test에 나뉘지 않습니다.
- 각 fold의 FlyVis feature 평균·표준편차 및 EEG target 평균·표준편차는 학습 이미지에서만 계산합니다.
- `alpha=1.0`을 첫 실행에 고정하고, train-fold 평균 EEG 예측을 baseline으로 둡니다.
- 평가 지표는 EEG 채널별 Pearson 상관 평균, 채널별 R² 평균, MSE입니다. 교차검증 예측을 함께 저장해 이후 분석을 확인할 수 있게 합니다.
- 현재 파일럿은 데이터셋이 지정한 test 이미지 200개 중 선택한 부분집합에서 내부 이미지 CV를 합니다. 이는 공식 benchmark test가 아니며, 점수는 모델 탐색에만 사용합니다. 후속 성능 주장은 별도 학습 이미지 pool과 사전 지정 독립 holdout으로 검증해야 합니다.

## 입력과 전처리

- 자극 이미지: grayscale, 64×64, [0,1] 정규화. FlyVis BoxEye(공식 예제의 extent=15, kernel_size=13)에 전달합니다.
- FlyVis: 사전학습 flow 네트워크, CPU. 반복 정지 노출 후 마지막 절반 프레임의 activity 평균을 특징으로 사용합니다. 모델의 내부 레이어 의미나 특정 cell type을 추가로 주장하지 않습니다.
- EEG: MNE로 BDF를 읽고 EEG 채널만 선택, 평균 참조, 1–40 Hz 필터를 적용합니다. 이벤트 onset을 기준으로 50–180 ms를 추출하고 채널별 시간 평균을 특징으로 삼습니다. 이미지별 반복 시행은 평균합니다. 자극 간격이 약 200 ms인 RSVP이므로, 첫 버전은 다음 자극이 들어오기 전 창만 사용합니다.
- 통계: EEG RDM의 이미지 인덱스를 함께 섞는 양측 이미지 라벨 순열검정. RDM edge별 독립 순열은 하지 않습니다. 기본 999회, p값은 add-one 보정입니다.

## 주의할 구현 한계

정지 이미지 반복 입력은 공식 FlyVis custom-stimuli 예제의 동영상/광수용체 경로를 이용하는 단순화입니다. 망막 적응, 자극 지속시간, 네트워크 초기 상태, EEG latency 선택에 따라 결과가 달라집니다. 후속 분석에서는 여러 시간창, 사전 정의된 세포군, 시각 자극 temporal dynamics를 민감도 분석해야 합니다.
