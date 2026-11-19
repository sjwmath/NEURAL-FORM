# NEURAL FORM

**FlyVis와 THINGS-EEG2의 이미지별 신경 표상 구조를 비교하는 탐색 연구**입니다.

NEURAL FORM의 장기 관심사는 EEG 기반 시각 심상 연구입니다. 첫 구현은 재현 가능한 기반을 만들기 위해 사람이 이미지를 **보는 동안**의 EEG와 초파리 시각계 모델의 반응을 같은 이미지로 비교합니다. 이 데이터와 분석은 심상 해독을 검증하지 않으며, 초파리의 주관적 경험을 측정하지 않습니다.

## 연구 질문

> 같은 시각 자극 집합을 처리할 때, 초파리 시각계 모델과 사람의 EEG에서 계산한 이미지 간 표상 거리 구조는 얼마나 비슷한가?

```text
같은 이미지 ──→ FlyVis BoxEye → FlyVis 뉴런 반응 ──┐
                                                   ├→ 이미지별 RDM → Spearman RSA
같은 이미지 ──→ 참가자 EEG → EEG 특징 벡터 ───────┘
```

## 진행 상태

| 항목 | 상태 |
|---|---|
| 데이터 출처·자극 매핑 조사 | THINGS-EEG2 v1.1.1 메타데이터 열과 파일 규칙 확인 |
| 파이프라인 코드·실행 스크립트 | 작성 및 Python 문법 확인 |
| 실제 FlyVis 추론 | 미실행: 의존성과 pretrained 모델 준비 필요 |
| 실제 EEG 전처리·RSA 결과 | 미실행: 전체 분석 실행 전 |

따라서 현재 저장소는 **실험 가능한 최소 구현 초안**입니다. 검증되지 않은 RSA 수치나 결과 그림은 포함하지 않습니다. 설치·첫 실행 오류와 실제 결과를 확인한 뒤 실행 로그와 결과를 추가합니다.

## 빠른 시작 (Windows)

1. Python **3.9–3.12**를 준비합니다.
2. 이 폴더에서 PowerShell을 열고 아래 명령을 실행합니다.

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\run.ps1 -Install
   ```

   또는 `run.bat`을 더블 클릭합니다. 설치 과정은 인터넷 연결이 필요합니다. 모델이 없으면 공식 FlyVis pretrained 모델도 내려받습니다.
3. 첫 실행은 EEG 파일(약 257MB), 메타데이터, 테스트 이미지(약 8MB)를 내려받고 FlyVis 사전학습 모델이 없으면 공식 모델 다운로드도 진행합니다. 모델은 한 번만 내려받으며 인터넷 연결과 추가 저장 공간이 필요합니다. 받은 파일은 `data/`에 캐시됩니다. 이후 기본 실행은 다음과 같습니다.

   ```powershell
   .\run.ps1
   ```

4. 결과는 `results/reports/rsa_result.json`, `results/figures/rdm_comparison.png`에 저장됩니다.

Windows에서 FlyVis 의존성이 설치되지 않으면 README의 WSL2 경로를 사용하세요. FlyVis 공식 문서는 Linux에서 Python 3.9–3.12를 테스트했다고 안내하며, 네이티브 Windows 지원을 보장하지 않습니다. WSL2 Ubuntu를 이미 설치한 경우, 프로젝트 저장소를 WSL 경로에서 열고 다음처럼 실행할 수 있습니다.

   ```bash
   cd /mnt/c/path/to/NEURAL-FORM
   bash run.sh
   ```

## 실험 범위와 방법

- 참가자 01, 세션 01, 테스트 세션을 사용합니다. 전체 EEG 파일을 한 번 내려받지만, 코드에서는 실제 `events.tsv`와 `stimuli.tsv`를 통해 매칭된 테스트 이미지 일부만 분석합니다.
- THINGS-EEG2 v1.1.1 이벤트의 `tot_img_number`를 자극 표의 `stimulus_id` 및 `filename`과 실제 파일명에 대조합니다. 대응 열이나 파일이 일치하지 않으면 중단합니다.
- EEG는 1–40 Hz 필터, 평균 참조, 50–180 ms epoch, 반복 시행 평균을 사용합니다. 자극 간격 약 200 ms의 RSVP에서 다음 자극과 겹치는 시간을 줄이기 위한 초기 설정이며, 특징은 epoch 내 채널별 평균입니다.
- FlyVis의 공식 `BoxEye` 렌더링 및 사전학습 `flow/0000/000` 네트워크를 사용합니다. 정지 이미지를 20 프레임 반복 노출하고 후반 프레임의 뉴런 출력을 평균합니다. 이 정지 이미지 설정은 optic-flow 모델의 공식 벤치마크 조건이 아니라 본 프로젝트의 탐색 설정입니다.
- 두 특징 행렬의 이미지별 상관거리 RDM을 만든 뒤, 이미지 라벨 순열검정으로 두 RDM 간 Spearman 상관을 비교합니다.

이미지 5장은 파이프라인 확인용입니다. RDM의 쌍 개수는 `N(N−1)/2`뿐이라 유의성 검정이나 생물학적 결론에 충분하지 않습니다. 최소 100장 이상과 참가자·세션 간 재현성, 사전 등록된 시간창/특징 정의가 후속 단계입니다.

## 명령

```powershell
.\run.ps1 -Install                 # 가상환경과 의존성 설치 후 실행
.\run.ps1 -Images 20               # 이미지 수 확대
.\run.ps1 -Images 100 -Permutations 4999
```

원본 데이터는 캐시됩니다. `data/`를 지우면 다시 내려받습니다. FlyVis 모델은 FlyVis 기본 캐시 위치에 저장됩니다.

## 공식 자료

- [FlyVis 문서: 설치](https://turagalab.github.io/flyvis/install/)
- [FlyVis 문서: custom stimuli](https://turagalab.github.io/flyvis/examples/07_flyvision_providing_custom_stimuli/)
- [FlyVis 논문](https://www.nature.com/articles/s41586-024-07939-3)
- [THINGS-EEG2 NEMAR 페이지](https://nemar.org/dataset/nm000232?v=v1.1.1)
- [THINGS-EEG2 OSF](https://osf.io/3jk45/)

라이선스·데이터 사용 조건은 원 출처의 최신 안내를 따르세요. 코드 실행 전 `docs/METHODOLOGY.md`와 `docs/LIMITATIONS.md`도 읽어 주세요.
