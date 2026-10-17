"""detect.py 확정 로직 테스트.  실행: python -m unittest test_detect -v"""
import unittest
from types import SimpleNamespace

import numpy as np

import detect


class FakeBoxes:
    def __init__(self, rows):
        self.xyxy = np.array([r[0] for r in rows], dtype=float).reshape(-1, 4)
        self.conf = np.array([r[1] for r in rows], dtype=float)
        self.cls = np.array([r[2] for r in rows], dtype=float)

    def __len__(self):
        return len(self.conf)


class FakeReporter:
    def __init__(self):
        self.sent = []

    def send_result(self, type_ko, conf, bbox, image):
        self.sent.append((type_ko, conf, bbox, image))


CFG = {
    "detection": {"conf": {"fire": 0.5}, "min_box_area_ratio": 0},
    "model": {"class_names": {"fire": "불"}},
    "snapshot": {"enabled": True, "draw_boxes": True},
}
NAMES = {0: "fire"}
HIT = [([10, 10, 60, 60], 0.9, 0)]


def run(frames, window=4, hits=2):
    """frames: 프레임마다 감지 행 목록(빈 리스트면 미감지)"""
    confirmer = detect.Confirmer(["fire"], window, hits, cooldown=60)
    reporter = FakeReporter()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    for i, rows in enumerate(frames):
        predict = lambda _f, rows=rows: SimpleNamespace(boxes=FakeBoxes(rows) if rows else None)  # noqa: E731
        detect.process_frame(img, predict, NAMES, CFG, confirmer, reporter, now=float(i))
    return reporter.sent


class ConfirmTest(unittest.TestCase):
    def test_confirms_on_current_hit(self):
        sent = run([HIT, HIT])
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], "불")

    def test_ignores_single_flicker(self):
        self.assertEqual(run([HIT, [], [], []]), [])

    def test_confirm_with_empty_current_frame_does_not_crash(self):
        # 이전 버전: 확정 순간 현재 프레임이 비어 있으면 ValueError 로 알림이 유실됐다.
        # hits=2 라 두 번째 hit 프레임에서 확정되지만, hits=3 + 중간 공백이면 마지막이 hit 이다.
        # 여기서는 Confirmer 가 현재 프레임이 비어도 True 를 돌려주는 상황을 직접 만든다.
        confirmer = detect.Confirmer(["fire"], 4, 2, cooldown=60)
        reporter = FakeReporter()
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        hit = lambda _f: SimpleNamespace(boxes=FakeBoxes(HIT))  # noqa: E731
        none = lambda _f: SimpleNamespace(boxes=None)  # noqa: E731
        detect.process_frame(img, hit, NAMES, CFG, confirmer, reporter, now=0.0)
        confirmer.window["fire"].append(True)  # 누적 hit 2 가 되도록 윈도우를 채워 둔다
        confirmer.window["fire"].append(False)
        # 미감지 프레임: update 가 False 를 append 한 뒤 sum >= 2 이면 True → last_seen 사용
        detect.process_frame(img, none, NAMES, CFG, confirmer, reporter, now=1.0)
        self.assertEqual(len(reporter.sent), 1)
        self.assertEqual(reporter.sent[0][2], [10.0, 10.0, 60.0, 60.0])

    def test_cooldown_blocks_repeat(self):
        sent = run([HIT] * 6)
        self.assertEqual(len(sent), 1)


if __name__ == "__main__":
    unittest.main()
