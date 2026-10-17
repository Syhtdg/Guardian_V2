"""
카메라/영상에서 YOLO 로 불·연기를 찾아 Guardian 백엔드로 보냅니다.

사용 예
  python detect.py                         # config.yaml 설정대로 실행
  python detect.py --source test.mp4       # 영상 파일로 시험
  python detect.py --test-alert            # 모델 없이 서버 연결만 확인 (가짜 감지 1건 전송)

흐름
  프레임 읽기 → YOLO 추론 → 최근 N 프레임 중 K 번 이상 잡히면 확정
  → /ai/result 로 전송 (스냅샷 포함) → 쿨다운 동안 같은 종류는 다시 보내지 않음
  카메라가 끊기거나 서버 전송이 실패하면 /ai/error 로 보고하고 다시 연결을 시도합니다.
"""
from __future__ import annotations

import argparse
import base64
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import requests
import yaml

HERE = Path(__file__).parent


# ───────────────────────── 설정 ─────────────────────────

def load_config(path: Path) -> dict:
    if not path.exists():
        example = HERE / "config.example.yaml"
        sys.exit(f"설정 파일이 없습니다: {path}\n{example.name} 을 config.yaml 로 복사해서 값을 채우세요.")
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg.get("server", {}).get("api_key"):
        sys.exit("config.yaml 의 server.api_key 가 비어 있습니다 (backend-main/.env 의 AI_API_KEY 와 같은 값).")
    return cfg


def parse_source(src):
    """'0' 같은 숫자는 웹캠 번호로."""
    if isinstance(src, int):
        return src
    s = str(src).strip()
    return int(s) if s.isdigit() else s


# ───────────────────────── 서버 전송 ─────────────────────────

class Reporter:
    def __init__(self, cfg: dict):
        s = cfg["server"]
        self.base = s["url"].rstrip("/")
        self.timeout = s.get("timeout_sec", 5)
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": s["api_key"], "Content-Type": "application/json"})
        cam = cfg["camera"]
        self.camera = {
            "cameraId": cam.get("id"),
            "location": cam.get("location", "위치 미지정"),
        }
        if cam.get("latitude") is not None and cam.get("longitude") is not None:
            self.camera["latitude"] = float(cam["latitude"])
            self.camera["longitude"] = float(cam["longitude"])
        # 공공 CCTV 처럼 http(s) 로 보는 영상이면 주소를 함께 보내 대시보드에서 실시간 영상을 띄울 수 있게 합니다.
        # rtsp:// 주소는 아이디·비밀번호가 들어 있을 수 있어 보내지 않습니다.
        src = str(cam.get("source", ""))
        if src.startswith(("http://", "https://")):
            self.camera["streamUrl"] = src
        self.pending: deque[dict] = deque(maxlen=20)  # 전송 실패한 감지 (서버 복구 후 재전송)
        self._last_error_sent: dict[str, float] = {}

    def _post(self, path: str, payload: dict) -> int:
        """HTTP 상태 코드를 돌려줍니다 (연결 실패는 0). 서버 오류·연결 실패만 재시도합니다."""
        status = 0
        for attempt in range(3):
            try:
                r = self.session.post(self.base + path, json=payload, timeout=self.timeout)
                status = r.status_code
                if status < 500:
                    if status >= 400:
                        print(f"  [서버 거부 {status}] {r.text[:200]}")
                    return status
                print(f"  [서버 응답 {status}] 재시도 {attempt + 1}/3")
            except requests.RequestException as e:
                status = 0
                print(f"  [서버 연결 실패] {e.__class__.__name__}: 재시도 {attempt + 1}/3")
            time.sleep(0.5 * (2 ** attempt))
        return status

    @staticmethod
    def _retryable(status: int) -> bool:
        # 연결 실패·서버 오류·API 키 오류는 나중에 다시 보낼 가치가 있음. 400/413(잘못된 값)은 버림.
        return status == 0 or status >= 500 or status == 401

    def send_result(self, type_ko: str, confidence: float, bbox, image_b64: str | None) -> bool:
        payload = {
            "type": type_ko,
            "confidence": round(float(confidence) * 100, 1),
            "bbox": [round(float(v), 1) for v in bbox] if bbox is not None else None,
            **self.camera,
        }
        if image_b64:
            payload["image"] = image_b64
        payload = {k: v for k, v in payload.items() if v is not None}
        status = self._post("/ai/result", payload)
        if status in (200, 201):
            return True
        if self._retryable(status):
            self.pending.append(payload)
            print(f"  → 전송 실패, 보관 ({len(self.pending)}건 대기)")
        return False

    def flush_pending(self):
        while self.pending:
            status = self._post("/ai/result", self.pending[0])
            if self._retryable(status):
                return
            self.pending.popleft()
            if status in (200, 201):
                print("  → 보관했던 감지 결과 재전송 완료")

    def send_error(self, error_type: str, message: str, raw: dict | None = None, throttle_sec: float = 60):
        """같은 종류 오류는 throttle_sec 마다 한 번만 보고."""
        now = time.time()
        if now - self._last_error_sent.get(error_type, 0) < throttle_sec:
            return
        self._last_error_sent[error_type] = now
        payload = {"errorType": error_type, "message": message[:2000], **{k: self.camera[k] for k in ("cameraId", "location")}}
        if raw:
            payload["rawData"] = raw
        self._post("/ai/error", payload)


# ───────────────────────── 감지 확정 로직 ─────────────────────────

class Confirmer:
    """최근 window 프레임 중 hits 번 이상 잡혀야 알림. 알림 후 cooldown 초 동안은 같은 종류를 다시 보내지 않음."""

    def __init__(self, classes, window: int, hits: int, cooldown: float):
        self.window = {c: deque(maxlen=window) for c in classes}
        self.hits = hits
        self.cooldown = cooldown
        self.last_alert = {c: -1e18 for c in classes}
        self.last_seen = {}  # 클래스별 가장 최근에 감지된 (프레임, 감지 목록)

    def update(self, cls: str, detected: bool, now: float) -> bool:
        w = self.window[cls]
        w.append(detected)
        if now - self.last_alert[cls] < self.cooldown:
            return False
        if sum(w) >= self.hits:
            self.last_alert[cls] = now
            w.clear()
            return True
        return False


def _np(x):
    return x.cpu().numpy() if hasattr(x, "cpu") else np.asarray(x)


def parse_detections(result, names: dict, conf_map: dict, min_area_ratio: float, frame_shape):
    """ultralytics Results → [(클래스 이름, conf, [x1,y1,x2,y2]), ...] (클래스별 최소 신뢰도·크기 필터 적용)"""
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return []
    h, w = frame_shape[:2]
    min_area = min_area_ratio * w * h
    out = []
    for xyxy, conf, cls in zip(_np(boxes.xyxy), _np(boxes.conf), _np(boxes.cls)):
        name = names.get(int(cls), str(int(cls)))
        if name not in conf_map or float(conf) < conf_map[name]:
            continue
        x1, y1, x2, y2 = map(float, xyxy)
        if (x2 - x1) * (y2 - y1) < min_area:
            continue
        out.append((name, float(conf), [x1, y1, x2, y2]))
    return out


COLORS = {"fire": (0, 0, 255), "smoke": (160, 160, 160)}


def annotate(frame, dets):
    img = frame.copy()
    for name, conf, (x1, y1, x2, y2) in dets:
        color = COLORS.get(name, (0, 255, 255))
        p1, p2 = (int(x1), int(y1)), (int(x2), int(y2))
        cv2.rectangle(img, p1, p2, color, 3)
        label = f"{name} {conf * 100:.0f}%"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(img, (p1[0], max(0, p1[1] - th - 10)), (p1[0] + tw + 8, p1[1]), color, -1)
        cv2.putText(img, label, (p1[0] + 4, p1[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return img


def encode_snapshot(frame, max_width: int, quality: int) -> str:
    h, w = frame.shape[:2]
    if w > max_width:
        frame = cv2.resize(frame, (max_width, int(h * max_width / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


# ───────────────────────── 카메라 ─────────────────────────

def open_capture(source):
    cap = cv2.VideoCapture(source)
    if isinstance(source, str) and source.startswith("rtsp"):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 지연 줄이기
    return cap


def process_frame(frame, model_predict, names, cfg, confirmer, reporter, now=None):
    """프레임 하나 처리. 테스트하기 쉽도록 분리. 반환: (감지 목록, 알림 보낸 클래스 목록)"""
    det_cfg = cfg["detection"]
    result = model_predict(frame)
    dets = parse_detections(result, names, det_cfg["conf"], det_cfg.get("min_box_area_ratio", 0), frame.shape)
    now = time.time() if now is None else now

    alerted = []
    for cls in det_cfg["conf"]:
        cls_dets = [d for d in dets if d[0] == cls]
        if cls_dets:
            confirmer.last_seen[cls] = (frame, cls_dets)
        if confirmer.update(cls, bool(cls_dets), now):
            # 확정 시점의 프레임에 감지가 없을 수 있으므로(최근 window 누적으로 확정) 가장 최근 감지를 사용
            seen_frame, seen_dets = confirmer.last_seen.get(cls, (frame, cls_dets))
            if not seen_dets:
                continue
            best = max(seen_dets, key=lambda d: d[1])
            snap_cfg = cfg.get("snapshot", {})
            image = None
            if snap_cfg.get("enabled", True):
                shot = annotate(seen_frame, seen_dets) if snap_cfg.get("draw_boxes", True) else seen_frame
                image = encode_snapshot(shot, snap_cfg.get("max_width", 1280), snap_cfg.get("jpeg_quality", 80))
            type_ko = cfg["model"]["class_names"].get(cls, cls)
            print(f"[{time.strftime('%H:%M:%S')}] {type_ko} 감지 확정 ({best[1] * 100:.1f}%) → 서버 전송")
            reporter.send_result(type_ko, best[1], best[2], image)
            alerted.append(cls)
    return dets, alerted


def run(cfg: dict, source_override=None):
    from ultralytics import YOLO

    reporter = Reporter(cfg)
    mcfg = cfg["model"]
    weights = Path(mcfg["weights"])
    if not weights.is_absolute():
        weights = HERE / weights
    try:
        model = YOLO(str(weights))
    except Exception as e:  # noqa: BLE001
        reporter.send_error("MODEL_LOAD_FAILED", f"{weights}: {e}", throttle_sec=0)
        sys.exit(f"모델을 불러오지 못했습니다: {weights}\n{e}")

    names = {int(k): v for k, v in model.names.items()}
    missing = [c for c in cfg["detection"]["conf"] if c not in names.values()]
    if missing:
        sys.exit(f"모델에 {missing} 클래스가 없습니다. 모델 클래스: {list(names.values())}")

    min_conf = min(cfg["detection"]["conf"].values())

    device = str(mcfg.get("device", "0"))
    if device != "cpu":
        import torch

        if not torch.cuda.is_available():
            print(f"[경고] CUDA 를 쓸 수 없어 device={device} 대신 cpu 로 실행합니다. (느릴 수 있음: detection.frame_stride 를 올려 보세요)")
            device = "cpu"

    def predict(frame):
        return model.predict(frame, conf=min_conf, imgsz=mcfg.get("imgsz", 640), device=device, verbose=False)[0]

    det = cfg["detection"]
    confirmer = Confirmer(list(det["conf"]), det.get("confirm_window", 10), det.get("confirm_hits", 4), det.get("cooldown_sec", 60))
    source = parse_source(source_override if source_override is not None else cfg["camera"]["source"])
    is_file = isinstance(source, str) and Path(source).exists()
    show = cfg.get("display", {}).get("show_window", True)
    stride = max(1, int(det.get("frame_stride", 1)))

    print(f"모델: {weights.name}  클래스: {list(names.values())}")
    print(f"입력: {source}  위치: {cfg['camera'].get('location')}")
    print("감지 시작 (종료: Ctrl+C" + (" 또는 창에서 q" if show else "") + ")")

    cap, backoff, frame_no, last_flush = None, 1, 0, 0.0
    try:
        while True:
            if cap is None or not cap.isOpened():
                cap = open_capture(source)
                if not cap.isOpened():
                    msg = f"카메라를 열 수 없습니다: {source}"
                    print(f"[오류] {msg}  {backoff}초 후 재시도")
                    reporter.send_error("CAMERA_OPEN_FAILED", msg)
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    continue
                backoff = 1

            ok, frame = cap.read()
            if not ok or frame is None:
                if is_file:
                    print("영상이 끝났습니다.")
                    break
                msg = f"프레임을 읽지 못했습니다 (연결 끊김?): {source}"
                print(f"[오류] {msg}")
                reporter.send_error("CAMERA_READ_FAILED", msg)
                cap.release()
                cap = None
                time.sleep(backoff)
                continue

            frame_no += 1
            if frame_no % stride:
                continue

            try:
                dets, _ = process_frame(frame, predict, names, cfg, confirmer, reporter)
            except Exception as e:  # noqa: BLE001
                print(f"[추론 오류] {e}")
                reporter.send_error("INFERENCE_FAILED", str(e))
                continue

            if reporter.pending and time.time() - last_flush > 10:
                last_flush = time.time()
                reporter.flush_pending()

            if show:
                cv2.imshow("Guardian", annotate(frame, dets))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        if cap is not None:
            cap.release()
        if show:
            cv2.destroyAllWindows()


def make_test_frame(kind: str = "fire", seed: int | None = None):
    """시험용 합성 장면(밤 숲 + 불꽃 또는 연기)을 만듭니다. 실제 사진이 아니며 'TEST' 표시가 들어갑니다."""
    rng = np.random.default_rng(seed)
    h, w = 360, 640
    t = np.linspace(0, 1, h)[:, None, None]
    top, bottom = (np.array([62, 46, 34]), np.array([22, 26, 24])) if kind == "fire" else (np.array([150, 150, 146]), np.array([60, 68, 62]))
    img = (top * (1 - t) + bottom * t).repeat(w, axis=1).astype(np.float32)
    for _ in range(18):  # 나무 실루엣
        x, th = int(rng.integers(0, w)), int(rng.integers(90, 210))
        cv2.rectangle(img, (x, h - 75 - th), (x + int(rng.integers(7, 16)), h - 60), (12, 16, 14), -1)
        cv2.circle(img, (x + 5, h - 75 - th), int(rng.integers(22, 42)), (14, 24, 16), -1)
    cv2.rectangle(img, (0, h - 65), (w, h), (18, 22, 18), -1)
    cx, base = int(rng.integers(220, 420)), h - 68

    def blob(center, axes, color, alpha, blur):
        layer = np.zeros_like(img)
        cv2.ellipse(layer, center, axes, 0, 0, 360, color, -1)
        layer = cv2.GaussianBlur(layer, (0, 0), blur)
        a = np.clip(layer.max(axis=2, keepdims=True) / 255, 0, 1) * alpha
        return img * (1 - a) + layer * alpha

    if kind == "fire":
        img = blob((cx, base - 30), (70, 60), (20, 80, 200), 0.35, 25)
        for i in range(5):
            img = blob((cx + int(rng.integers(-7, 8)), base - 20 - i * 11), (14 - i * 2, 28 - i * 3), (30 + i * 25, 120 + i * 20, 255), 0.95, 4)
        box = [cx - 38, base - 95, cx + 38, base + 5]
    else:
        for i in range(9):
            img = blob((cx + int(rng.integers(-15, 25)) + i * 4, base - 20 - i * 19), (30 + i * 5, 20 + i * 4), (175, 175, 175), 0.55, 11)
        box = [cx - 60, base - 210, cx + 90, base]
    img = np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)
    cv2.putText(img, "TEST", (12, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    return img, [float(v) for v in box]


def test_alert(cfg: dict, kind: str = "fire"):
    """모델 없이 서버 연결·API 키·대시보드 알림을 확인합니다. (kind: fire / smoke)"""
    reporter = Reporter(cfg)
    img, box = make_test_frame(kind)
    image = encode_snapshot(annotate(img, [(kind, 0.9, box)]), 1280, 80)
    type_ko = cfg.get("model", {}).get("class_names", {}).get(kind) or ("불" if kind == "fire" else "연기")
    print(f"{reporter.base}/ai/result 로 시험 감지 1건을 보냅니다...")
    status = reporter._post("/ai/result", {"type": type_ko, "confidence": 90.0, "bbox": box, "image": image, **reporter.camera})
    if status in (200, 201):
        print("성공! 대시보드에 알림이 떴는지 확인하세요.")
    elif status == 401:
        sys.exit("API 키가 틀렸습니다. config.yaml 의 api_key 와 backend-main/.env 의 AI_API_KEY 를 똑같이 맞추세요.")
    elif status == 0:
        sys.exit(f"서버에 연결할 수 없습니다. 백엔드가 {reporter.base} 에서 실행 중인지 확인하세요.")
    else:
        sys.exit(f"실패 (HTTP {status}).")


def main():
    ap = argparse.ArgumentParser(description="Guardian 불·연기 감지기")
    ap.add_argument("--config", default=str(HERE / "config.yaml"))
    ap.add_argument("--source", help="config 의 camera.source 대신 사용 (0, rtsp://..., http(s)://...m3u8, 파일)")
    ap.add_argument("--camera-id", help="config 의 camera.id 대신 사용")
    ap.add_argument("--location", help="config 의 camera.location 대신 사용")
    ap.add_argument("--lat", type=float, help="카메라 위도 (지도 마커)")
    ap.add_argument("--lng", type=float, help="카메라 경도 (지도 마커)")
    ap.add_argument("--no-show", action="store_true", help="화면 창 띄우지 않기")
    ap.add_argument("--test-alert", nargs="?", const="fire", choices=["fire", "smoke"],
                    help="서버 연결 시험용 가짜 감지 1건 전송 (기본 fire, 연기는 --test-alert smoke)")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    cam = cfg.setdefault("camera", {})
    # 대시보드의 '공공 CCTV → AI 감시' 명령처럼 카메라 정보를 명령줄로 바꿀 수 있습니다
    if args.source is not None:
        cam["source"] = args.source
    if args.camera_id:
        cam["id"] = args.camera_id
    if args.location:
        cam["location"] = args.location
    if args.lat is not None and args.lng is not None:
        cam["latitude"], cam["longitude"] = args.lat, args.lng
    if args.no_show:
        cfg.setdefault("display", {})["show_window"] = False
    if args.test_alert:
        test_alert(cfg, args.test_alert)
        return
    run(cfg)


if __name__ == "__main__":
    main()
