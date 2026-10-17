"""
YOLO 불/연기 감지 모델 학습 (NVIDIA GPU 권장)

사용 예
  python train.py --data datasets/guardian/data.yaml
  python train.py --data datasets/guardian/data.yaml --model yolo11m.pt --epochs 150 --batch 16

학습이 끝나면 가장 좋은 가중치를 weights/guardian_best.pt 로 복사합니다.
detect.py 는 기본으로 이 파일을 씁니다.
"""
import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Guardian YOLO 학습")
    ap.add_argument("--data", required=True, help="convert_aihub.py 가 만든 data.yaml")
    ap.add_argument("--model", default="yolo11s.pt",
                    help="시작 가중치. n(가장 빠름) < s < m < l (정확도↑, 속도↓). 기본 yolo11s.pt")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=float, default=-1, help="-1 이면 GPU 메모리에 맞춰 자동")
    ap.add_argument("--device", default="0", help="GPU 번호 (CPU 는 cpu)")
    ap.add_argument("--workers", type=int, default=4, help="Windows 에서 오류 나면 0 으로")
    ap.add_argument("--patience", type=int, default=25, help="이만큼 좋아지지 않으면 조기 종료")
    ap.add_argument("--name", default="guardian")
    ap.add_argument("--resume", action="store_true", help="끊긴 학습 이어서 (runs/.../last.pt 를 --model 로)")
    args = ap.parse_args()

    from ultralytics import YOLO
    import torch

    if args.device != "cpu" and not torch.cuda.is_available():
        print("[경고] CUDA GPU 를 찾지 못했습니다. README 의 'PyTorch GPU 설치' 를 확인하세요. CPU 로 진행합니다.")
        args.device = "cpu"
    elif args.device != "cpu":
        print(f"GPU: {torch.cuda.get_device_name(int(args.device.split(',')[0]))}")

    batch = int(args.batch) if args.batch >= 1 else args.batch
    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        project="runs",
        name=args.name,
        exist_ok=False,
        resume=args.resume,
        # 불·연기는 좌우가 바뀌어도 같고 색이 중요하므로 색 변화(hsv_h)는 약하게
        fliplr=0.5,
        hsv_h=0.01,
        hsv_s=0.5,
        hsv_v=0.4,
        mosaic=1.0,
        close_mosaic=10,
        plots=True,
    )

    save_dir = Path(model.trainer.save_dir)
    best = save_dir / "weights" / "best.pt"
    if best.exists():
        out = Path(__file__).parent / "weights" / "guardian_best.pt"
        out.parent.mkdir(exist_ok=True)
        shutil.copy2(best, out)
        print(f"\n가장 좋은 모델: {best}\n복사본: {out}")

        metrics = YOLO(str(best)).val(data=args.data, imgsz=args.imgsz, device=args.device, plots=False)
        names = metrics.names
        print("\n검증 결과 (mAP50 / mAP50-95)")
        print(f"  전체 : {metrics.box.map50:.3f} / {metrics.box.map:.3f}")
        for i, c in enumerate(metrics.box.ap_class_index):
            print(f"  {names[int(c)]:5}: {metrics.box.ap50[i]:.3f} / {metrics.box.ap[i]:.3f}")
        print(f"\n그래프와 예측 예시는 {save_dir} 폴더에 있습니다 (results.png, val_batch*_pred.jpg).")


if __name__ == "__main__":  # Windows 에서 멀티프로세싱 오류 방지
    main()
