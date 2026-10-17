"""
val 세트를 영상(같은 영상에서 나온 프레임 묶음) 순서대로 모델에 넣고, detect.py 의 확정 로직(Confirmer)을
그대로 적용해 설정별로 '첫 알림까지 걸린 프레임 수'와 '오경보 횟수'를 비교합니다.

  mAP 는 사진 한 장 단위 점수라 "최근 N프레임 중 K번 잡히면 알림"인 실제 동작과 다릅니다.
  이 스크립트는 실제 알림 로직 기준으로 설정(연기 신뢰도, 확정 횟수)을 고를 때 씁니다.

사용 예
  python evaluate/eval_video_sim.py                 # val 전체 (수천~만 장, 수 분~수십 분)
  python evaluate/eval_video_sim.py --limit 300     # 영상마다 앞 300프레임만 (빠른 점검)

모델 추론 결과는 --cache 파일에 저장해 두고 다시 쓰므로, 설정만 바꿔 재실행할 때는 몇 초면 끝납니다.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

AI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI))

from detect import Confirmer  # noqa: E402


def collect(args):
    from ultralytics import YOLO

    model = YOLO(args.weights)
    ds = Path(args.dataset)
    groups = collections.defaultdict(list)
    for p in (ds / "images/val").glob("*.jpg"):
        m = re.match(r"(.+?)(\d+)$", p.stem)
        if m:
            groups[m.group(1)].append((int(m.group(2)), p))

    data = {}
    for g, frames in sorted(groups.items()):
        frames.sort()
        frames = frames[: args.limit] if args.limit else frames
        rec = []
        for i in range(0, len(frames), 64):
            chunk = frames[i:i + 64]
            results = model.predict([str(p) for _, p in chunk], conf=0.05, imgsz=640, device=args.device, verbose=False)
            for (n, p), r in zip(chunk, results):
                best = {"fire": 0.0, "smoke": 0.0}
                for c, s in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
                    name = model.names[int(c)]
                    best[name] = max(best[name], s)
                lbl = ds / "labels/val" / (p.stem + ".txt")
                cls = {ln.split()[0] for ln in lbl.read_text().splitlines() if ln.strip()} if lbl.exists() else set()
                rec.append([n, best["fire"], best["smoke"], "0" in cls, "1" in cls])
        data[g] = rec
        print(f"  {g}: {len(rec)}프레임", flush=True)
    return data


def simulate(data, conf_f, conf_s, window=10, hits=4, cooldown=900):
    rows = []
    for g, rec in data.items():
        confirmer = Confirmer(["fire", "smoke"], window, hits, cooldown)
        alerts = {"fire": [], "smoke": []}
        for idx, (_, f, s, _gf, _gs) in enumerate(rec):
            for cls, conf, thr in (("fire", f, conf_f), ("smoke", s, conf_s)):
                if confirmer.update(cls, conf >= thr, float(idx)):
                    alerts[cls].append(idx)
        for cls, gi in (("fire", 3), ("smoke", 4)):
            present = [i for i, r in enumerate(rec) if r[gi]]
            first_gt = present[0] if present else None
            # 정답 박스가 있는 프레임에서 150프레임 넘게 떨어진 알림은 오경보로 셉니다
            false_alerts = [a for a in alerts[cls] if not any(abs(a - p) <= 150 for p in present[::5])]
            first_alert = alerts[cls][0] if alerts[cls] else None
            rows.append((g, cls, len(rec), len(present), first_gt, first_alert, len(false_alerts)))
    return rows


def summarize(rows, cls):
    with_gt = [r for r in rows if r[1] == cls and r[3] > 0]
    detected = [r for r in with_gt if r[5] is not None]
    delays = sorted(r[5] - r[4] for r in detected)
    median = delays[len(delays) // 2] if delays else None
    false_alerts = sum(r[6] for r in rows if r[1] == cls)
    total = sum(r[2] for r in rows if r[1] == cls)
    return (f"정답이 있는 영상 {len(with_gt)}개 중 감지 {len(detected)}개, "
            f"첫 알림 지연 중앙값 {median}프레임, 오경보 {false_alerts}회 (전체 {total}프레임)")


def main():
    ap = argparse.ArgumentParser(description="영상 단위 알림 시뮬레이션")
    ap.add_argument("--weights", default=str(AI / "weights/guardian_best.pt"))
    ap.add_argument("--dataset", default=str(AI / "datasets/guardian"))
    ap.add_argument("--cache", default=str(AI / "evaluate/.frame_conf_cache.json"))
    ap.add_argument("--limit", type=int, default=0, help="영상마다 앞쪽 N프레임만 (0=전체)")
    ap.add_argument("--device", default="0")
    ap.add_argument("--fire", type=float, default=0.5, help="불 신뢰도 기준")
    ap.add_argument("--smoke", type=float, nargs="+", default=[0.45, 0.40, 0.35, 0.30, 0.25], help="비교할 연기 신뢰도 기준들")
    ap.add_argument("--hits", type=int, nargs="+", default=[3, 4, 5, 6], help="비교할 확정 횟수들 (10프레임 중)")
    args = ap.parse_args()

    cache = Path(args.cache)
    if cache.exists():
        data = json.loads(cache.read_text())
        print(f"저장된 추론 결과를 사용합니다: {cache}")
    else:
        print("모델로 프레임별 신뢰도를 계산합니다...")
        data = collect(args)
        cache.write_text(json.dumps(data))

    print("\n=== 연기 신뢰도 기준별 (확정: 10프레임 중 4회) ===")
    for s in args.smoke:
        rows = simulate(data, args.fire, s)
        print(f"\n[불>={args.fire} 연기>={s}]")
        print("  불  :", summarize(rows, "fire"))
        print("  연기:", summarize(rows, "smoke"))

    print(f"\n=== 확정 횟수별 (불 {args.fire}, 연기 {args.smoke[0]}) ===")
    for h in args.hits:
        rows = simulate(data, args.fire, args.smoke[0], hits=h)
        print(f"  {h}회 연기:", summarize(rows, "smoke"))


if __name__ == "__main__":
    main()
