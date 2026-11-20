"""Train a compact binary U-Net on BUSI masks. Multiple masks for an image are unioned."""
from pathlib import Path
import argparse,csv,json,random
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import Dataset,DataLoader

class BUSIMasks(Dataset):
 def __init__(self,rows,size): self.rows=rows; self.size=size
 def __len__(self): return len(self.rows)
 def __getitem__(self,i):
  r=self.rows[i]; im=Image.open(r['image']).convert('L').resize((self.size,self.size),Image.Resampling.BILINEAR); x=np.asarray(im,dtype=np.float32)/255.
  mask=np.zeros((self.size,self.size),dtype=np.uint8)
  if r.get('masks'):
   for mp in r['masks'].split(';'):
    if mp and Path(mp).exists():
     m=np.asarray(Image.open(mp).convert('L').resize((self.size,self.size),Image.Resampling.NEAREST)); mask=np.maximum(mask,(m>0).astype(np.uint8))
  return torch.from_numpy(x[None]),torch.from_numpy(mask.astype(np.float32)[None])
class Block(nn.Module):
 def __init__(self,ci,co): super().__init__(); self.net=nn.Sequential(nn.Conv2d(ci,co,3,padding=1),nn.BatchNorm2d(co),nn.ReLU(inplace=True),nn.Conv2d(co,co,3,padding=1),nn.BatchNorm2d(co),nn.ReLU(inplace=True))
 def forward(self,x): return self.net(x)
class UNet(nn.Module):
 def __init__(self):
  super().__init__(); self.e1=Block(1,32); self.e2=Block(32,64); self.e3=Block(64,128); self.pool=nn.MaxPool2d(2); self.mid=Block(128,256); self.u3=nn.ConvTranspose2d(256,128,2,2); self.d3=Block(256,128); self.u2=nn.ConvTranspose2d(128,64,2,2); self.d2=Block(128,64); self.u1=nn.ConvTranspose2d(64,32,2,2); self.d1=Block(64,32); self.out=nn.Conv2d(32,1,1)
 def forward(self,x):
  a=self.e1(x); b=self.e2(self.pool(a)); c=self.e3(self.pool(b)); z=self.mid(self.pool(c)); z=self.d3(torch.cat([self.u3(z),c],1)); z=self.d2(torch.cat([self.u2(z),b],1)); z=self.d1(torch.cat([self.u1(z),a],1)); return self.out(z)
def rows(path,split):
 with open(path,newline='',encoding='utf-8') as f:return [r for r in csv.DictReader(f) if r['split']==split]
def dice_loss(logits,target):
 p=torch.sigmoid(logits); dims=(1,2,3); inter=(p*target).sum(dims); return 1-((2*inter+1)/(p.sum(dims)+target.sum(dims)+1)).mean()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--manifest',default='training/manifests/busi_manifest.csv'); ap.add_argument('--epochs',type=int,default=30); ap.add_argument('--batch-size',type=int,default=4); ap.add_argument('--size',type=int,default=256); ap.add_argument('--workers',type=int,default=0); ap.add_argument('--output',default='backend/weights/research_busi_unet_best.pth'); a=ap.parse_args()
 torch.manual_seed(42); np.random.seed(42); random.seed(42); dev=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); print('Device:',dev)
 tr=BUSIMasks(rows(a.manifest,'train'),a.size); va=BUSIMasks(rows(a.manifest,'val'),a.size); te=BUSIMasks(rows(a.manifest,'test'),a.size)
 if not tr or not va or not te: raise RuntimeError('Empty split; run prepare_busi.py first.')
 dl=DataLoader(tr,batch_size=a.batch_size,shuffle=True,num_workers=a.workers); vl=DataLoader(va,batch_size=a.batch_size,num_workers=a.workers); tl=DataLoader(te,batch_size=a.batch_size,num_workers=a.workers)
 model=UNet().to(dev); opt=torch.optim.AdamW(model.parameters(),lr=1e-3); bce=nn.BCEWithLogitsLoss(); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); best=-1
 for ep in range(1,a.epochs+1):
  model.train(); ls=0
  for x,y in dl:
   x,y=x.to(dev),y.to(dev); opt.zero_grad(); z=model(x); loss=bce(z,y)+dice_loss(z,y); loss.backward(); opt.step(); ls+=loss.item()
  model.eval(); ds=[]
  with torch.no_grad():
   for x,y in vl:
    z=torch.sigmoid(model(x.to(dev)))>.5; y=y.to(dev); dims=(1,2,3); d=(2*(z*y).sum(dims)+1)/((z.float()).sum(dims)+y.sum(dims)+1); ds.extend(d.cpu().tolist())
  score=float(np.mean(ds)); print(f'Epoch {ep}/{a.epochs} loss={ls/max(len(dl),1):.4f} val_dice={score:.4f}')
  if score>best: best=score; torch.save({'architecture':'compact_unet','state_dict':model.state_dict(),'image_size':a.size,'threshold':0.5,'best_val_dice':best},out)
 ck=torch.load(out,map_location=dev); model.load_state_dict(ck['state_dict']); model.eval(); ds=[]
 with torch.no_grad():
  for x,y in tl:
   z=torch.sigmoid(model(x.to(dev)))>.5; y=y.to(dev); dims=(1,2,3); d=(2*(z*y).sum(dims)+1)/(z.float().sum(dims)+y.sum(dims)+1); ds.extend(d.cpu().tolist())
 print(f'TEST Dice (held-out BUSI split): {float(np.mean(ds)):.4f}; checkpoint={out}')
 metrics={'architecture':'compact_unet','test_dice':float(np.mean(ds)),'best_val_dice':best,'checkpoint':str(out)}
 out.with_suffix('.metrics.json').write_text(json.dumps(metrics,indent=2)); print('Saved metrics:',out.with_suffix('.metrics.json'))
if __name__=='__main__':main()
