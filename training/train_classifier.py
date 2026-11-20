"""Train BUSI three-class classifier. Writes a separate research checkpoint; never overwrites production weights."""
from pathlib import Path
import argparse, csv, json, random
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms

NAMES=['Benign','Malignant','Normal']
class BUSI(Dataset):
    def __init__(self, rows, tfm): self.rows=rows; self.tfm=tfm
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i]
        with Image.open(r['image']) as im: x=im.convert('RGB')
        return self.tfm(x), int(r['label'])

def load_rows(manifest, split):
    with open(manifest, newline='',encoding='utf-8') as f: return [r for r in csv.DictReader(f) if r['split']==split]

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',default='training/manifests/busi_manifest.csv'); p.add_argument('--epochs',type=int,default=25); p.add_argument('--batch-size',type=int,default=8); p.add_argument('--image-size',type=int,default=224); p.add_argument('--lr',type=float,default=1e-4); p.add_argument('--workers',type=int,default=0); p.add_argument('--pretrained',action='store_true',help='Download ImageNet EfficientNet-B0 initialization'); p.add_argument('--output',default='backend/weights/research_busi_classifier_best.pth'); a=p.parse_args()
    torch.manual_seed(42); np.random.seed(42); random.seed(42)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); print('Device:',device)
    norm=transforms.Normalize([.485,.456,.406],[.229,.224,.225])
    train_t=transforms.Compose([transforms.Resize((a.image_size,a.image_size)),transforms.RandomHorizontalFlip(),transforms.RandomRotation(8),transforms.ToTensor(),norm])
    eval_t=transforms.Compose([transforms.Resize((a.image_size,a.image_size)),transforms.ToTensor(),norm])
    tr=BUSI(load_rows(a.manifest,'train'),train_t); va=BUSI(load_rows(a.manifest,'val'),eval_t); te=BUSI(load_rows(a.manifest,'test'),eval_t)
    if not tr or not va or not te: raise RuntimeError('Train/val/test split is empty. Run prepare_busi.py first.')
    dl=DataLoader(tr,batch_size=a.batch_size,shuffle=True,num_workers=a.workers); vl=DataLoader(va,batch_size=a.batch_size,shuffle=False,num_workers=a.workers); tl=DataLoader(te,batch_size=a.batch_size,shuffle=False,num_workers=a.workers)
    weights=models.EfficientNet_B0_Weights.DEFAULT if a.pretrained else None
    model=models.efficientnet_b0(weights=weights); model.classifier[1]=nn.Linear(model.classifier[1].in_features,3); model.to(device)
    # Class-weighted loss helps with BUSI class imbalance.
    counts=torch.bincount(torch.tensor([int(r['label']) for r in load_rows(a.manifest,'train')]),minlength=3).float(); cw=(counts.sum()/(3*counts.clamp_min(1))).to(device)
    criterion=nn.CrossEntropyLoss(weight=cw); opt=torch.optim.AdamW(model.parameters(),lr=a.lr)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); best=0.0
    for epoch in range(1,a.epochs+1):
        model.train(); loss_sum=correct=total=0
        for x,y in dl:
            x,y=x.to(device),y.to(device); opt.zero_grad(); logits=model(x); loss=criterion(logits,y); loss.backward(); opt.step(); loss_sum+=loss.item()*len(y); correct+=(logits.argmax(1)==y).sum().item(); total+=len(y)
        model.eval(); vc=vt=0; vloss=0
        with torch.no_grad():
            for x,y in vl:
                x,y=x.to(device),y.to(device); z=model(x); vloss+=criterion(z,y).item()*len(y); vc+=(z.argmax(1)==y).sum().item(); vt+=len(y)
        vacc=vc/max(vt,1); print(f'Epoch {epoch}/{a.epochs} train_loss={loss_sum/total:.4f} train_acc={correct/total:.4f} val_loss={vloss/vt:.4f} val_acc={vacc:.4f}')
        if vacc>best:
            best=vacc; torch.save({'architecture':'efficientnet_b0','num_classes':3,'class_names':NAMES,'state_dict':model.state_dict(),'image_size':a.image_size,'val_accuracy':best},out)
    # Independent test evaluation with best checkpoint.
    ck=torch.load(out,map_location=device); model.load_state_dict(ck['state_dict']); model.eval(); cm=np.zeros((3,3),dtype=int)
    with torch.no_grad():
        for x,y in tl:
            pred=model(x.to(device)).argmax(1).cpu().numpy()
            for yy,pp in zip(y.numpy(),pred): cm[int(yy),int(pp)]+=1
    acc=float(cm.trace()/max(cm.sum(),1)); print('TEST confusion matrix rows=true cols=pred [Benign,Malignant,Normal]:'); print(cm); print(f'TEST accuracy (descriptive, held-out BUSI split): {acc:.4f}')
    metrics={'class_names':NAMES,'test_confusion_matrix':cm.tolist(),'test_accuracy':acc,'best_validation_accuracy':best,'checkpoint':str(out)}
    out.with_suffix('.metrics.json').write_text(json.dumps(metrics,indent=2)); print('Saved:',out)
if __name__=='__main__': main()
