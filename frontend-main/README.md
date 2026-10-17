# Guardian 프런트엔드

화재·연기 감지 결과를 실시간으로 보여 주는 관제 대시보드입니다. 백엔드(`../backend-main`)에서 감지 결과를 받아 알림, 카드 목록, 지도 마커로 표시합니다.

## 기술 스택

- Vue 3, Vuetify 3, Vite
- Vue Router (파일 기반 라우팅), Pinia
- axios, socket.io-client
- Kakao Maps JavaScript SDK

## 화면

| 경로 | 설명 |
|---|---|
| `/login` | 로그인 |
| `/signup` | 회원가입 |
| `/find_ID` | 아이디 찾기 (가입 이메일로 발송) |
| `/reset_password` | 비밀번호 재설정 (이메일 인증코드) |
| `/dashboard` | 실시간 감지 알림, 감지 목록, 지도 |
| `/log` | 사용자 로그, AI 감지 로그, AI 에러 로그 |

로그인하지 않은 상태에서 `/login`, `/signup`, `/find_ID`, `/reset_password` 외의 경로에 접근하면 로그인 화면으로 이동합니다.

## 실행 방법

Node.js 18 이상이 필요하고, 백엔드가 먼저 실행 중이어야 합니다.

```bash
npm install
cp .env.example .env
npm run dev        # http://localhost:3000
```

운영용 빌드는 `npm run build`로 만들고, `npm run preview`로 확인할 수 있습니다.

## 환경변수 (`.env`)

| 이름 | 설명 | 기본값 |
|---|---|---|
| `VITE_API_URL` | 백엔드 주소 | `http://localhost:10111` |
| `VITE_KAKAO_MAP_KEY` | 카카오맵 JavaScript 키 | 없음 |
| `VITE_MAP_CENTER_LAT` | 지도 기본 중심 위도 | `35.9135` |
| `VITE_MAP_CENTER_LNG` | 지도 기본 중심 경도 | `128.8125` |

카카오맵 키는 [카카오 개발자 콘솔](https://developers.kakao.com)의 플랫폼 키에서 발급합니다. JavaScript SDK 도메인에 `http://localhost:3000`을 등록해야 지도가 표시되며, 키가 없으면 지도 영역에 안내 문구만 나타납니다. `.env`는 저장소에 올리지 않습니다.

## 폴더 구조

```
src/
├── pages/        화면 (폴더 이름이 곧 경로)
├── components/   대시보드, 로그인, 로그 테이블 등
├── layouts/      공통 레이아웃
├── router/       라우터와 로그인 가드
├── plugins/      Vuetify, axios 설정
├── utils/        토큰 저장과 만료 확인
└── assets/       이미지
public/sounds/    경보음 (fire.mp3, smoke.mp3)
```

## 동작 방식

- 로그인하면 받은 JWT를 `localStorage`에 저장하고, 모든 API 요청에 자동으로 붙입니다. 토큰이 만료되어 401이 오면 로그아웃하고 로그인 화면으로 이동합니다.
- 대시보드는 같은 토큰으로 socket.io에 연결하고, 서버가 `aiResult` 이벤트를 보내면 팝업과 경보음을 재생하며 목록과 지도 마커를 갱신합니다. 경보음은 "확인"을 누르면 멈춥니다.

## 알려진 한계

- 기상 정보는 Open-Meteo(키 불필요)에서 지도 중심 좌표의 현재 날씨를 가져옵니다. 인터넷이 안 되면 "불러오지 못했습니다"로 표시됩니다.
- "카메라 현황"은 감지·오류 기록으로 집계한 화면입니다. 카메라 등록과 실시간 접속 상태 확인, 사용자 관리 화면은 아직 구현하지 않았습니다.
- 자동 테스트가 없습니다.
