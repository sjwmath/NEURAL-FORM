# 데이터 구조와 연결

공식 NEMAR THINGS-EEG2 v1.1.1에서 다음 항목을 가져오도록 구성했습니다.

- `sub-01/ses-01/eeg/sub-01_ses-01_task-test_eeg.bdf`
- 같은 디렉터리의 `sub-01_ses-01_task-test_events.tsv`
- `stimuli/stimuli.tsv`
- `stimuli/test_images.zip`

테스트 이미지 압축 파일은 약 8.1MB, 위 EEG BDF는 약 256.6MB(표시상 약 257MB)입니다. 전체 EEG 기록을 받아 MNE가 해당 기록을 읽습니다. 여러 연구자가 동시에 내려받는 경우 전송 시간은 달라집니다.

확인한 v1.1.1 파일에서 이벤트 표에는 `onset`, `tot_img_number`가 있고, 자극 표에는 `stimulus_id`, `filename`이 있습니다. 테스트 자극 ID는 `stim-test00001` 형식이고, 이벤트의 `tot_img_number=1`은 `stim-test00001`과 연결됩니다. `filename`의 마지막 `_image` 접미사를 제거한 파일 stem과 압축을 푼 실제 이미지가 존재하는지까지 검사합니다. 다른 데이터 릴리스에서는 열 이름·ID 규칙이 달라질 수 있으며, 그 경우 임의 매핑을 하지 않고 중단합니다.

자료 확인: [NEMAR 데이터셋](https://nemar.org/dataset/nm000232?v=v1.1.1), [릴리스 파일 인덱스](https://data.nemar.org/nm000232/v1.1.1/).
