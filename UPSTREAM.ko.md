# 상류: storytold/filmcraft

이 저장소는 [storytold/filmcraft](https://github.com/storytold/filmcraft)의 **하드 포크**로, 상류의
릴리스 태그 하나까지의 전체 히스토리를 그대로 담고 있습니다. 패치 스택도, 미러도 아닙니다.

English: [UPSTREAM.md](./UPSTREAM.md)

## 포크 지점

| | |
|---|---|
| 상류 태그 | `v0.6.0` |
| 상류 커밋 | `2ff3f5e` — 2026-10-10, `Release prep: 0.6.0 and a Linux riscv64 release build (#830)` |
| 상류 기본 브랜치 | `main` |
| 우리의 장기 브랜치 | `develop`(기본), `main`(릴리스) |

기계가 읽는 기록은 [`upstream-base.json`](./upstream-base.json)입니다. 히스토리를 공유하므로
`git merge-base develop upstream/main`이 실제로 존재하고, 상류 동기화는 재생이 아닌 평범한 3-way 머지입니다.

## 패치 스택이 아니라 머지된 트리인 이유

이 포크가 바꾸는 것은 국소적이지 않습니다. 브랜드를 교체하고, 레드롭 계정 레이어를 넣고, 우리 에이전트
엔진을 기본으로 삼고, UI 테마를 레드롭 디자인 시스템으로 옮깁니다. 첫 번에 수십 개 파일이고 점점 늘어납니다.
패치 스택은 깨끗한 체크아웃에 몇 개 파일만 얹을 때 맞는 모양이고, 여기서는 매번 커지는 충돌 면을 되풀이할 뿐
얻는 것이 없습니다.

## 이 포크가 소유하지 않는 것

상류 `NOTICE`와 그 `docs/brand/LICENSE-brand.txt`는 `docs/brand/` 아래의
ArtCraft 이름·워드마크·마크가 ArtCraft Team의 상표이며 MIT OR Apache-2.0에 포함되지 **않고**, 포크와 변형본은
이를 제거해야 한다고 명시합니다. 그래서 제거했습니다. `upstream-base.json`은 이 접두사를 `proprietaryPrefixes`에 두고
`proprietaryReplaced: true`로 표시합니다. `scripts/check_upstream_boundary.py`는 그 파일이 상류와 바이트가 같으면,
`scripts/check_brand.py`는 그 접두사 아래 파일이 다시 생기면 실패합니다(상류 동기화가 되살리면 머지에서 지웁니다).

FilmCraft 앱 아이콘은 코드와 같은 라이선스의 원작이었고, 라이선스가 아니라 제품 정체성 때문에 교체했습니다.
이제 모든 아이콘은 `assets/brand/`의 레드롭 디자인 시스템 원본(`SHA256SUMS`로 고정)에서 `packaging/brand-assets.sh`가
만듭니다.

### 바꾼 것과 일부러 둔 것

사람이 보거나 설치하는 것은 모두 레드롭 필름의 것입니다: 이름, 앱 ID `ai.redrob.film`, 실행 파일 `redrob-film`과
`redrob-film-cli`, 설치 프로그램, 데이터 폴더, 로그 파일, MCP 서버 이름, 링크, 아이콘, About·홈 화면의 로크업,
브랜드 색(redrob-ui에서 생성한 `redrob_tokens`). `scripts/check_brand.py`가 이를 지킵니다.

레드롭 이름으로 바꾸되, 기존 파일과 설정이 계속 동작하도록 옛 표기는 계속 **읽습니다**(그런 읽기 경로는 코드에
`// legacy:` 표시가 있고, 표시 없는 잔존은 `scripts/check_brand.py`가 실패시킵니다):

- 크레이트 이름: `filmcraft` → `redrob-film-app`, `filmcraft-*` → `redrob-film-*`, `effectcraft-*` →
  `redrob-effects-*`(모듈 경로·로그 타깃 `redrob_film_*`/`redrob_effects_*` 포함). `tools/rename_crates.py`가
  멱등하게 수행하며 `tools/merge_effectcraft.py`가 호출하므로 상류 동기화 뒤에도 충돌 대신 다시 이름을 바꿉니다.
- 프로젝트 파일: `.fcproj` → `.rfilm`(이펙트 사이드카 `<이름>.rfilm.effects.json`), 이펙트 프로젝트 `.ecproj` → `.rfx`,
  XML 사본 `.ecprojx` → `.rfxx`, XML 루트 `<EffectCraftProject>` → `<RedrobEffectsProject>`. 옛 파일은 명령줄,
  열기 대화상자, 최근 항목, 미디어 브라우저, 감시 폴더, 가져오기, 템플릿, 복구에서 그대로 열리고, 자동 저장 회전과
  스키마 백업도 옛 파일을 포함합니다. 옛 표기로 쓰는 곳은 없습니다.
- MIME `application/x-redrob-film`·`application/x-redrob-effects`(macOS UTType, Linux shared-mime-info, .desktop).
  옛 확장자도 glob으로 함께 선언합니다.
- MCP 리소스 URI `redrob-film://document|commands`, `redrob-effects://…`. 옛 URI도 읽힙니다.
- 환경 변수 `REDROB_FILM_*`/`REDROB_EFFECTS_*`. 사용자용 변수는 옛 이름으로 폴백합니다: `FILMCRAFT_DATA_DIR`,
  `FILMCRAFT_CONFIG_DIR`, `FILMCRAFT_CONTROL_PORT`, `FILMCRAFT_CPU_COMPOSITE`, `EFFECTCRAFT_CONFIG_DIR`,
  `EFFECTCRAFT_FONT_DIRS`. 테스트 전용 변수(`*_BLESS`, `*_UI_SNAPSHOT_DIR`, `*_FUZZ_*`, 모델 경로)는 이름만 바꿨습니다.
- MKV `WritingApp`은 `redrob-film`입니다.

파일에 저장되어 다시 읽을 때 비교되는 것은 상류 그대로 둡니다:

- 프로젝트·프리셋·템플릿 파일의 `filmcraft.*` 형식 ID(`"format": "filmcraft.project"`), OTIO 메타데이터 네임스페이스
  `filmcraft`, 프로젝트 설정에 저장되는 렌더러 이름, 인터체인지가 다시 읽는 AAF 태그 이름과 XMP `CreatorTool` 표시.
  하위 크레이트의 스레드 이름과 임시 파일 접두사도 짧은 `filmcraft-` 단어를 유지합니다(크레이트 이름이 아닙니다).
- 내장 디코더 이름(`FilmCraft H.264` 등), 하위 크레이트의 테스트 데이터와 코드 주석. 앱이 내보낸 파일에 적는 이름(MP4
  인코더 태그, MXF·AAF·OMF 식별 정보, 자막·LUT 헤더, 프로젝트 `generator`)과 사람이 읽는 메시지는 레드롭 필름의 것입니다.
- `docs/` 아래 상류 문서(`docs/agents.md` 제외). 상류를 설명하는 문서입니다.

상류의 `release.yml`은 유지하지 않고 제거했습니다. 상류 자체의 `craft-common-actions` 저장소에 있는 재사용
워크플로를 상류의 서명 시크릿으로 호출하기 때문입니다. 우리 릴리스 워크플로는 이 조직의 시크릿 기준으로 작성합니다.

## 상류 흡수

상류 **태그**를 따릅니다. 동기화 브랜치는 `sync/upstream-<tag>`이고 `develop`으로 PR을 열며,
**머지 커밋으로만 머지하고 스쿼시하지 않습니다.** 스쿼시는 머지 베이스를 없애 다음 동기화가 이미 가져온
작업을 되풀이하게 만듭니다.

```sh
git fetch upstream --tags
git checkout -b sync/upstream-vX.Y.Z develop
git merge vX.Y.Z          # 충돌은 손으로. 우리가 바꾼 이름은 우리 것, 그 주변은 상류 것
cargo build --release && cargo test && python3 scripts/check_upstream_boundary.py
```

그리고 같은 PR에서 `upstream-base.json`의 `base`, `baseTag`, `baseDate`, `baseSubject`,
`lastSyncedUpstream`을 갱신합니다.

## 귀속

[`NOTICE`](./NOTICE)의 상류 저작권 줄은 원문 그대로 두고 그 아래에 우리 줄을 추가했습니다. 두 라이선스 전문
([`LICENSE-MIT`](./LICENSE-MIT), [`LICENSE-APACHE`](./LICENSE-APACHE))은 바꾸지 않았습니다. 자산별 귀속은
[`ATTRIBUTION.md`](./ATTRIBUTION.md)에 이어집니다.
