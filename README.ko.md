# 레드롭 컷

레드롭 컷은 에이전트가 편집하는 영상 편집기입니다. 원하는 컷을 말로 설명하면 에이전트가 만듭니다.

English: [README.md](./README.md)

> **포크 안내.** 이 저장소는 [storytold/filmcraft](https://github.com/storytold/filmcraft) 태그 `v0.6.0`의
> 하드 포크입니다. 어디서 갈라졌고, 무엇을 소유하지 않으며, 상류를 어떻게 흡수하는지는
> [UPSTREAM.ko.md](./UPSTREAM.ko.md)에, 기계가 읽는 핀은 [`upstream-base.json`](./upstream-base.json)에 있습니다.
> 상류 저작권 표기는 [NOTICE](./NOTICE)에 원문 그대로 두고 그 아래에 우리 줄을 추가했습니다.
> 상류의 ArtCraft 상표는 제거했고, `assets/brand/`의 레드롭 마크는 레드롭의 상표입니다.

## 무엇인가

- 순수 Rust로 만든 비선형 영상 편집기. H.264·HEVC·ProRes·AAC 코덱을 자체 구현하고, GPU 합성기가 선형 광에서 작업합니다.
- 앱의 모든 동작이 명령(command)입니다. UI·CLI·JSON 제어 채널·MCP 서버가 같은 명령을 호출하므로 에이전트가 사람과 똑같이 자르고, 다듬고, 색을 잡고, 믹스하고, 내보낼 수 있습니다.
- **Redrob Code가 내장돼 있습니다.** Agent 패널에서 Redrob Code와 대화하면 같은 명령으로 열린 프로젝트를 편집합니다. 모델 호출은 연결한 레드롭 워크스페이스에 과금되고(Help ▸ Connect to Redrob…), 편집 자체는 무료이며 계정을 묻지 않습니다. 다른 에이전트는 `redrob-cut-cli mcp`로 연결합니다([docs/agents.md](./docs/agents.md)).
- macOS·Windows·Linux 네이티브, 브라우저는 WebAssembly.

## 시작하기

```sh
cargo run --release -p filmcraft                     # 데스크톱 앱(redrob-cut, 데모 프로젝트)
cargo run --release -p filmcraft -- --control 9876   # JSON-lines 제어 서버 포함
cargo run --release -p filmcraft-cli -- commands     # 엔진 명령 전체 목록(redrob-cut-cli)
cargo run --release -p filmcraft-cli -- mcp          # MCP 서버(헤드리스)
```

Cargo 패키지 이름은 상류 동기화가 깔끔하도록 상류의 `filmcraft*`를 유지합니다. 실행 파일, 앱 ID(`ai.redrob.cut`), 설치 프로그램과 사람이 보는 모든 것은 레드롭 컷의 것입니다.

## 브랜치와 기여

- 기본 브랜치 `develop`, 릴리스 브랜치 `main`. 브랜치 이름은 `feat/ fix/ chore/ docs/ test/ refactor/ perf/ ci/ build/ sync/ hotfix/ release/` 접두사를 따르며, redrob-labs 공용 gitflow 워크플로가 검사합니다(모든 레포가 같은 목록).
- 상류 동기화는 `sync/upstream-<tag>` 브랜치로, 머지 커밋으로만 합칩니다.
- 조직 공통 규약: [redrob-labs/.github](https://github.com/redrob-labs/.github)의 CONTRIBUTING.ko.md와 FORKS.ko.md.

## 라이선스

MIT 또는 Apache-2.0 중 선택([LICENSE-MIT](./LICENSE-MIT), [LICENSE-APACHE](./LICENSE-APACHE)).
저작권 표기는 [NOTICE](./NOTICE)에 있습니다. 상류 표기 아래에 우리 표기를 추가했습니다:

```
Copyright (c) 2026 ArtCraft Team and the FilmCraft contributors.
Copyright (c) 2026-present Janghoon Lee (Redrob) and contributors
```

레드롭 이름과 마크는 이 라이선스에 포함되지 않습니다([assets/brand/README.md](./assets/brand/README.md)).
자산별 귀속은 [ATTRIBUTION.md](./ATTRIBUTION.md)에 있습니다.
