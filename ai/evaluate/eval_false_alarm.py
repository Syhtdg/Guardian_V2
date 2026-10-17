"""
학습에 쓰지 않은 사진으로 '이미지 단위' 감지율과 오탐률을 잽니다. (mAP 로는 알 수 없는 운영 기준 점검)

  양성   : 변환된 val 세트에서 불·연기 박스가 있는 사진
  음성 1 : 불·연기가 없는 평범한 사진 (--normal-dir, 예: Validation/[원천]무관씬)
  음성 2 : 구름·안개·조명 등 헷갈리는 사진 (--lookalike-dir, 학습 세트에 들어가지 않은 것만 사용)

사용 예
  python evaluate/eval_false_alarm.py --normal-dir "D:/aihub/Validation/[원천]무관씬" \\
         --lookalike-dir "D:/aihub/Training/[원천]유사씬_13" --n 2000

음성 폴더를 주지 않으면 해당 항목은 건너뜁니다. 주의: 음성 2 는 학습에 쓰인 영상과 같은 영상에서
나온 사진일 수 있어 오탐률이 실제보다 낮게 나올 수 있습니다.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

from ultralytics import YOLO

AI = Path(__file__).resolve().parent.parent
THRESHOLDS = [(0.25, 0.25), (0.5, 0.45), (0.6, 0.55), (0.7, 0.65), (0.8, 0.75)]  # (불, 연기)


def run(model, paths, device):
    """사진마다 클래스별 최고 신뢰도를 돌려줍니다."""
    out = []
    for i in range(0, len(paths), 64):
        batch = [str(p) for p in paths[i:i + 64]]
        for r in model.predict(batch, conf=0.20, imgsz=640, device=device, verbose=False):
            best = {}
            for c, s in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
                name = model.names[int(c)]
                best[name] = max(best.get(name, 0.0), s)
            out.append(best)
    return out


def sample(paths, n, rng):
    paths = list(paths)
    rng.shuffle(paths)
    return paths[:n]


def main():
    ap = argparse.ArgumentParser(description="이미지 단위 감지율·오탐률 측정")
    ap.add_argument("--weights", default=str(AI / "weights/guardian_best.pt"))
    ap.add_argument("--dataset", default=str(AI / "datasets/guardian"), help="convert_aihub.py 가 만든 폴더")
    ap.add_argument("--normal-dir", help="평범한 음성 사진 폴더")
    ap.add_argument("--lookalike-dir", action="append", default=[], help="헷갈리는 음성 사진 폴더 (여러 번 지정 가능)")
    ap.add_argument("--n", type=int, default=2000, help="그룹마다 쓸 사진 수")
    ap.add_argument("--device", default="0")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    ds = Path(args.dataset)
    model = YOLO(args.weights)

    pos = []
    for p in (ds / "labels/val").glob("*.txt"):
        cls = {line.split()[0] for line in p.read_text().splitlines() if line.strip()}
        if cls:
            pos.append((ds / "images/val" / (p.stem + ".jpg"), cls))
    pos = sample(pos, args.n, rng)

    groups = {"양성": run(model, [p for p, _ in pos], args.device)}
    neg_normal = neg_look = None
    if args.normal_dir:
        neg_normal = sample(Path(args.normal_dir).glob("*.jpg"), args.n, rng)
        groups["평범한 음성"] = run(model, neg_normal, args.device)
    if args.lookalike_dir:
        used = {p.stem for sub in ("train", "val") for p in (ds / "images" / sub).glob("*.jpg")}
        cand = [p for d in args.lookalike_dir for p in Path(d).glob("*.jpg") if p.stem not in used]
        neg_look = sample(cand, args.n, rng)
        groups["헷갈리는 음성"] = run(model, neg_look, args.device)
    print("사진 수:", {k: len(v) for k, v in groups.items()})

    print(f"\n{'기준(불/연기)':<18}{'양성 감지':>10}{'불 재현':>9}{'연기 재현':>10}", end="")
    for k in groups:
        if k != "양성":
            print(f"{k + ' 오탐':>16}", end="")
    print()
    for tf, ts in THRESHOLDS:
        hit = lambda b: b.get("fire", 0) >= tf or b.get("smoke", 0) >= ts  # noqa: E731
        res = groups["양성"]
        f_ok = [b.get("fire", 0) >= tf for b, (_, c) in zip(res, pos) if "0" in c]
        s_ok = [b.get("smoke", 0) >= ts for b, (_, c) in zip(res, pos) if "1" in c]
        row = f"불>={tf} 연기>={ts}".ljust(18)
        row += f"{sum(map(hit, res)) / len(res):>10.1%}{sum(f_ok) / max(1, len(f_ok)):>9.1%}{sum(s_ok) / max(1, len(s_ok)):>10.1%}"
        for k, v in groups.items():
            if k != "양성":
                row += f"{sum(map(hit, v)) / len(v):>16.1%}"
        print(row)


if __name__ == "__main__":
    main()
