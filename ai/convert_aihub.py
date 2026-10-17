"""
AI Hub 등 공공 화재/산불 데이터셋 라벨(JSON) → YOLO 학습 형식으로 변환

지원 형식
  1) AI Hub 이미지별 JSON  : {"image": {...}, "annotations": [{"bbox": [x1,y1,x2,y2], "polygon": [...], "class": "01"}, ...]}
  2) COCO 하나짜리 JSON    : {"images": [...], "annotations": [...], "categories": [...]}

사용 예
  # 1. 라벨 구조와 클래스 코드부터 확인
  python convert_aihub.py --labels D:/aihub/라벨링데이터 --inspect

  # 2. class_map.yaml 을 고친 뒤 변환
  python convert_aihub.py --images D:/aihub/원천데이터 --labels D:/aihub/라벨링데이터 --out datasets/guardian

결과
  datasets/guardian/
    images/train, images/val, labels/train, labels/val
    data.yaml            ← train.py 에 넘기는 파일
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("pyyaml 이 필요합니다:  pip install pyyaml")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CLASSES = ["fire", "smoke"]  # YOLO 클래스 번호 0, 1
BBOX_FORMAT = "xyxy"  # AI Hub 는 [x1,y1,x2,y2]. --bbox-format xywh 로 바꿀 수 있음


# ───────────────────────── 읽기 ─────────────────────────

def read_json(path: Path):
    # AI Hub 파일은 가끔 BOM 이 붙은 UTF-8 이거나 CP949 입니다.
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(path, encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 형식 오류: {path} ({e})") from e
    raise ValueError(f"인코딩을 알 수 없음: {path}")


def first(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in (None, ""):
            return d[k]
    return default


def norm_class(v) -> str:
    """'1' / 1 / '01' 모두 '01' 로 맞춤. 이름이면 소문자 공백제거."""
    if isinstance(v, (int, float)):
        return f"{int(v):02d}"
    s = str(v).strip()
    if s.isdigit():
        return f"{int(s):02d}"
    return s.lower().replace(" ", "")


def to_xyxy(ann: dict, img_w: int | None, img_h: int | None):
    """annotation 하나에서 [x1,y1,x2,y2] 픽셀 박스를 뽑습니다."""
    box = first(ann, "bbox", "box", "bounding_box", "Bbox", "BBOX")
    if isinstance(box, dict):  # {"x":..,"y":..,"w":..,"h":..} 형태
        x, y = float(first(box, "x", "x1", "left", default=0)), float(first(box, "y", "y1", "top", default=0))
        if "x2" in box:
            return [x, y, float(box["x2"]), float(box["y2"])]
        return [x, y, x + float(first(box, "w", "width", default=0)), y + float(first(box, "h", "height", default=0))]
    if isinstance(box, (list, tuple)) and len(box) == 2 and all(isinstance(p, (list, tuple)) for p in box):
        (x1, y1), (x2, y2) = box  # [[x1,y1],[x2,y2]]
        return [float(x1), float(y1), float(x2), float(y2)]
    if isinstance(box, (list, tuple)) and len(box) == 4:
        x1, y1, a, b = map(float, box)
        if BBOX_FORMAT == "xywh":
            return [x1, y1, x1 + a, y1 + b]
        return [x1, y1, a, b]

    poly = first(ann, "polygon", "points", "segmentation")
    if poly:
        pts = poly
        if isinstance(pts[0], (int, float)):  # [x1,y1,x2,y2,...] 평평한 배열
            pts = list(zip(pts[0::2], pts[1::2]))
        elif isinstance(pts[0], (list, tuple)) and pts[0] and isinstance(pts[0][0], (list, tuple)):
            pts = [p for part in pts for p in part]  # 여러 조각
        # AI Hub 라벨 일부(약 0.03%)는 polygon 에 좌표가 빠진 점([] 등)이 섞여 있어 걸러 냅니다
        pts = [p for p in pts if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not pts:
            return None
        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]
        return [min(xs), min(ys), max(xs), max(ys)]
    return None


def image_size_from_json(data: dict):
    img = first(data, "image", "images", "imageInfo", default={}) or {}
    if isinstance(img, list):
        img = img[0] if img else {}
    res = first(img, "resolution", "size", default=None)
    if isinstance(res, (list, tuple)) and len(res) >= 2:
        return int(res[0]), int(res[1])
    w, h = first(img, "width", "Width"), first(img, "height", "Height")
    if w and h:
        return int(w), int(h)
    return None, None


def image_name_from_json(data: dict, json_path: Path):
    img = first(data, "image", "images", "imageInfo", default={}) or {}
    if isinstance(img, list):
        img = img[0] if img else {}
    name = first(img, "filename", "file_name", "fileName", "FileName")
    return Path(name).name if name else json_path.stem


# ───────────────────────── 레코드 만들기 ─────────────────────────

def iter_records(labels_dir: Path):
    """(이미지 파일 이름, 이미지 w, h, [(class 원본값, [x1,y1,x2,y2])...]) 를 돌려줍니다."""
    jsons = sorted(labels_dir.rglob("*.json"))
    if not jsons:
        sys.exit(f"라벨 폴더에 JSON 이 없습니다: {labels_dir}")

    # COCO 형식(큰 JSON 하나)
    if len(jsons) <= 3:
        data = read_json(jsons[0])
        if isinstance(data, dict) and "images" in data and "categories" in data:
            yield from iter_coco(data)
            return

    for jp in jsons:
        try:
            data = read_json(jp)
        except ValueError as e:
            print("  [건너뜀]", e)
            continue
        if isinstance(data, dict) and "images" in data and "categories" in data:
            yield from iter_coco(data)
            continue
        w, h = image_size_from_json(data)
        anns = first(data, "annotations", "annotation", "objects", "shapes", default=[]) or []
        if isinstance(anns, dict):
            anns = [anns]
        objs = []
        for a in anns:
            cls = first(a, "class", "category", "label", "class_name", "category_id")
            box = to_xyxy(a, w, h)
            if cls is None or box is None:
                continue
            objs.append((norm_class(cls), box))
        yield image_name_from_json(data, jp), w, h, objs


def iter_coco(data: dict):
    cats = {c["id"]: c.get("name", str(c["id"])) for c in data["categories"]}
    by_img = defaultdict(list)
    for a in data["annotations"]:
        x, y, w, h = a["bbox"]
        by_img[a["image_id"]].append((norm_class(cats.get(a["category_id"], a["category_id"])), [x, y, x + w, y + h]))
    for im in data["images"]:
        yield Path(im["file_name"]).name, im.get("width"), im.get("height"), by_img.get(im["id"], [])


# ───────────────────────── 점검 모드 ─────────────────────────

def inspect(labels_dir: Path, limit: int):
    jsons = sorted(labels_dir.rglob("*.json"))
    print(f"JSON 파일 수: {len(jsons)}")
    if not jsons:
        return
    sample = read_json(jsons[0])
    print("\n첫 번째 파일:", jsons[0])
    text = json.dumps(sample, ensure_ascii=False, indent=2)
    print(text[:1500] + ("\n  ...(생략)" if len(text) > 1500 else ""))

    counter, boxes_per_img, no_box = Counter(), [], 0
    for i, (_, _, _, objs) in enumerate(iter_records(labels_dir)):
        if i >= limit:
            break
        boxes_per_img.append(len(objs))
        if not objs:
            no_box += 1
        counter.update(c for c, _ in objs)

    print(f"\n앞쪽 {len(boxes_per_img)}개 이미지 기준")
    print(f"  박스 없는 이미지: {no_box}")
    print("  클래스별 박스 수:")
    for c, n in counter.most_common():
        print(f"    {c!r:>12}: {n}")
    print("\n※ bbox 4개 값은 기본으로 [x1,y1,x2,y2] 로 읽습니다. [x,y,너비,높이] 라면 --bbox-format xywh 를 붙이세요.")
    print("\n→ 위 클래스 값을 class_map.yaml 의 mapping 에 fire / smoke / ignore 로 적어 주세요.")


# ───────────────────────── 변환 ─────────────────────────

def index_images(images_dir: Path):
    idx = {}
    dup = 0
    for p in images_dir.rglob("*"):
        if p.suffix.lower() in IMAGE_EXTS:
            if p.name in idx:
                dup += 1
            idx[p.name] = p
            idx.setdefault(p.stem, p)
    if dup:
        print(f"  [주의] 같은 이름의 이미지가 {dup}개 있습니다. 하나만 사용됩니다.")
    return idx


def group_key(name: str, pattern: re.Pattern):
    """같은 영상에서 나온 프레임끼리 묶는 키. 묶어서 나눠야 검증 점수가 부풀지 않습니다."""
    stem = Path(name).stem
    m = pattern.search(stem)
    return stem[: m.start()] if m else stem


def read_size(path: Path):
    try:
        import cv2  # 선택: JSON 에 해상도가 없을 때만 사용
    except ImportError:
        sys.exit("JSON 에 이미지 크기가 없어 opencv-python 이 필요합니다:  pip install opencv-python")
    img = cv2.imread(str(path))
    if img is None:
        return None, None
    h, w = img.shape[:2]
    return w, h


def convert(args):
    cmap_raw = yaml.safe_load(open(args.map, encoding="utf-8"))["mapping"]
    cmap = {norm_class(k): v for k, v in cmap_raw.items()}
    bad = {v for v in cmap.values() if v not in ("fire", "smoke", "ignore")}
    if bad:
        sys.exit(f"class_map.yaml 값은 fire / smoke / ignore 만 됩니다: {bad}")

    images_dir, labels_dir, out = Path(args.images), Path(args.labels), Path(args.out)
    print("이미지 색인 중...")
    img_idx = index_images(images_dir)
    print(f"  이미지 {len(set(img_idx.values()))}개")

    pattern = re.compile(args.group_regex)
    records, missing, unknown = [], 0, Counter()
    stats = Counter()

    for name, w, h, objs in iter_records(labels_dir):
        img_path = img_idx.get(name) or img_idx.get(Path(name).stem)
        if img_path is None:
            missing += 1
            continue
        if not w or not h:
            w, h = read_size(img_path)
            if not w:
                missing += 1
                continue
        lines = []
        for cls, (x1, y1, x2, y2) in objs:
            target = cmap.get(cls)
            if target is None:
                unknown[cls] += 1
                continue
            if target == "ignore":
                stats["ignore_box"] += 1
                continue
            # 이미지 밖으로 나간 좌표는 자르고, 너무 작은 박스는 버립니다
            x1, x2 = max(0.0, min(x1, x2)), min(float(w), max(x1, x2))
            y1, y2 = max(0.0, min(y1, y2)), min(float(h), max(y1, y2))
            if (x2 - x1) < args.min_box or (y2 - y1) < args.min_box:
                stats["tiny_box"] += 1
                continue
            cid = CLASSES.index(target)
            cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
            bw, bh = (x2 - x1) / w, (y2 - y1) / h
            lines.append(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            stats[target] += 1
        records.append((img_path, lines, group_key(img_path.name, pattern)))

    if unknown and not args.skip_unknown:
        print("\n[중단] class_map.yaml 에 없는 클래스가 있습니다:")
        for c, n in unknown.most_common():
            print(f"    {c!r}: {n}개")
        print("mapping 에 추가하거나, 무시하려면 --skip-unknown 을 붙이세요.")
        sys.exit(1)

    positives = [r for r in records if r[1]]
    negatives = [r for r in records if not r[1]]
    rng = random.Random(args.seed)
    rng.shuffle(negatives)
    keep_neg = int(len(positives) * args.neg_ratio)
    negatives = negatives[:keep_neg]
    records = positives + negatives
    if not positives:
        sys.exit("불/연기 박스가 하나도 없습니다. class_map.yaml 과 폴더 경로를 확인하세요.")

    # 영상(그룹) 단위로 train/val 분리
    groups = sorted({r[2] for r in records})
    rng.shuffle(groups)
    n_val = max(1, int(len(groups) * args.val))
    val_groups = set(groups[:n_val])

    if out.exists() and any(out.iterdir()):
        if not args.overwrite:
            sys.exit(f"출력 폴더가 비어 있지 않습니다: {out}  (덮어쓰려면 --overwrite)")
        shutil.rmtree(out)
    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    split_count, split_pos = Counter(), Counter()
    used_names = set()
    for img_path, lines, g in records:
        split = "val" if g in val_groups else "train"
        stem = img_path.stem
        # 다른 폴더에 같은 이름이 있으면 겹치지 않게
        while stem in used_names:
            stem += "_"
        used_names.add(stem)
        dst = out / "images" / split / f"{stem}{img_path.suffix.lower()}"
        if args.link:
            try:
                os.link(img_path, dst)
            except OSError:
                shutil.copy2(img_path, dst)
        else:
            shutil.copy2(img_path, dst)
        (out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        split_count[split] += 1
        if lines:
            split_pos[split] += 1

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: n for i, n in enumerate(CLASSES)},
    }
    with open(out / "data.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(data_yaml, f, allow_unicode=True, sort_keys=False)

    print("\n변환 완료")
    print(f"  이미지: train {split_count['train']} / val {split_count['val']}  (영상 그룹 {len(groups)}개 중 val {n_val}개)")
    print(f"  박스: fire {stats['fire']} / smoke {stats['smoke']}  (ignore {stats['ignore_box']}, 너무 작음 {stats['tiny_box']})")
    print(f"  배경 이미지(불·연기 없음): {len(negatives)}")
    for split in ("train", "val"):
        if split_pos[split] == 0:
            print(f"  [주의] {split} 에 불·연기 이미지가 없습니다. 영상 수가 너무 적거나 --group-regex 가 파일 이름과 맞지 않습니다.")
    if missing:
        print(f"  [주의] 이미지 파일을 못 찾은 라벨: {missing}개")
    print(f"  data.yaml: {out / 'data.yaml'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI Hub/COCO 라벨 → YOLO 형식 변환")
    ap.add_argument("--labels", required=True, help="라벨(JSON) 폴더")
    ap.add_argument("--images", help="원천(이미지) 폴더")
    ap.add_argument("--out", default="datasets/guardian", help="출력 폴더")
    ap.add_argument("--map", default=str(Path(__file__).with_name("class_map.yaml")), help="클래스 연결표")
    ap.add_argument("--val", type=float, default=0.15, help="검증 비율 (기본 0.15)")
    ap.add_argument("--neg-ratio", type=float, default=0.2, help="불·연기 없는 배경 이미지를 양성 대비 몇 배 넣을지 (기본 0.2)")
    ap.add_argument("--min-box", type=float, default=4, help="이보다 작은(픽셀) 박스는 버림")
    ap.add_argument("--group-regex", default=r"[_-]?\d+$", help="파일 이름에서 프레임 번호 부분 (같은 영상 묶기용)")
    ap.add_argument("--bbox-format", choices=["xyxy", "xywh"], default="xyxy", help="JSON bbox 4개 값의 뜻 (AI Hub 는 xyxy)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--link", action="store_true", help="복사 대신 하드링크 (같은 드라이브일 때 디스크 절약)")
    ap.add_argument("--skip-unknown", action="store_true", help="연결표에 없는 클래스는 무시")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--inspect", action="store_true", help="변환하지 않고 라벨 구조만 확인")
    ap.add_argument("--inspect-limit", type=int, default=5000)
    args = ap.parse_args(argv)
    global BBOX_FORMAT
    BBOX_FORMAT = args.bbox_format

    if args.inspect:
        inspect(Path(args.labels), args.inspect_limit)
        return
    if not args.images:
        ap.error("--images 가 필요합니다")
    convert(args)


if __name__ == "__main__":
    main()
