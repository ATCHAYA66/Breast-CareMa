"""Create leakage-aware BUSI manifests and merged binary masks without altering source data."""
from pathlib import Path
import argparse, csv, random, re
from collections import defaultdict

CLASSES = {"benign": 0, "malignant": 1, "normal": 2}

def locate_root(p: Path) -> Path:
    candidates = [p, p / "Dataset_BUSI_with_GT"]
    candidates += list(p.glob("**/Dataset_BUSI_with_GT"))
    for c in candidates:
        if all((c / k).is_dir() for k in CLASSES): return c
    raise FileNotFoundError("Could not find benign/malignant/normal folders. Extract BUSI into datasets/BUSI/Dataset_BUSI_with_GT")

def key_for(img: Path) -> str:
    s = img.stem
    s = re.sub(r"_mask(?:_\d+)?$", "", s, flags=re.I)
    return s

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data', default='datasets/BUSI'); ap.add_argument('--out', default='training/manifests'); ap.add_argument('--seed', type=int, default=42); args=ap.parse_args()
    root=locate_root(Path(args.data).resolve()); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows=[]
    for cls, label in CLASSES.items():
        folder=root/cls
        for img in sorted(folder.glob('*.png')):
            if '_mask' in img.stem.lower(): continue
            base=img.stem
            masks=sorted(folder.glob(base+'_mask*.png'))
            rows.append({'image':str(img.resolve()),'class_name':cls,'label':label,'group':base,'masks':';'.join(str(x.resolve()) for x in masks)})
    if not rows: raise RuntimeError(f'No source images found under {root}')
    # Split by original image ID. All masks remain attached to their image and cannot leak across splits.
    rng=random.Random(args.seed); splitmap={}
    for cls in CLASSES:
        subset=[r for r in rows if r['class_name']==cls]; rng.shuffle(subset)
        n=len(subset); n_test=max(1,round(n*.15)); n_val=max(1,round(n*.15))
        for i,r in enumerate(subset): splitmap[r['group']]='test' if i<n_test else ('val' if i<n_test+n_val else 'train')
    fields=['image','class_name','label','group','masks','split']
    with (out/'busi_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: r['split']=splitmap[r['group']]; w.writerow(r)
    print(f'Dataset root: {root}\nImages: {len(rows)}')
    for split in ('train','val','test'):
        counts={c:sum(1 for r in rows if splitmap[r['group']]==split and r['class_name']==c) for c in CLASSES}
        print(f'{split}: {counts} (total {sum(counts.values())})')
    print(f'Manifest: {out / "busi_manifest.csv"}')

if __name__=='__main__': main()
