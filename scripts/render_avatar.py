#!/usr/bin/env python3
"""Render an explicitly directed 16:9 review using original audio and seam-safe avatar windows."""
import argparse,json,math,re,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
W,H,FPS=1280,720,25
# 颜色取自 moonlit-content-engine/references/brand-tokens.md 的深色 night 主题
ACCENT='#e0894f';PAPER='#f3f0e8';MUTED='#8c99aa';BG='#0e1a28';GREEN=ACCENT  # GREEN 仅为旧变量名兼容
def read(p):return json.loads(Path(p).read_text())
def srt(path):
 out=[]
 def sec(x):
  a,b,c=x.replace(',','.').split(':');return int(a)*3600+int(b)*60+float(c)
 for block in Path(path).read_text().strip().split('\n\n'):
  ls=block.splitlines()
  if len(ls)>2 and '-->' in ls[1]:
   a,b=ls[1].split(' --> ');out.append((sec(a),sec(b),''.join(ls[2:])))
 return out
def visible(c,t):
 # All avatar appearances, including circles, must pass the same seam mask.
 bad=any(a<=t<b for a,b in c['hiddenSeamWindows'])
 return not bad and any(a<=t<b for a,b in c['speakerWindows'])
def reveal(c,t):
 if not visible(c,t):return 0.0
 a,b=next((a,b) for a,b in c['speakerWindows'] if a<=t<b)
 d=c.get('speakerTransitionSeconds',0)
 if not d:return 1.0
 u=min(1,(t-a)/d if a>0 else 1,(b-t)/d)
 return max(0,u*u*(3-2*u))
def wrap_text(d,txt,font,width):
 tokens=re.findall(r'[A-Za-z0-9]+(?:[+./-][A-Za-z0-9]+)*|\s+|.',txt)
 lines=[];line=''
 for token in tokens:
  if line and d.textlength(line+token,font=font)>width:
   lines.append(line.strip());line=token.lstrip()
  else:line+=token
 if line.strip():lines.append(line.strip())
 return lines
def validate(c,scenes):
 assert c['production_mode']=='avatar_explainer' and c['aspectRatio']=='16:9'
 assert abs(scenes[0]['start'])<.001 and abs(scenes[-1]['end']-c['duration'])<.02
 for a,b in zip(scenes,scenes[1:]):assert abs(a['end']-b['start'])<.001
 plan=read(c['gesturePlan'])
 assert plan['fps']==FPS and abs(plan['audioDurationSeconds']-c['duration'])<.02
 for seam in plan['seams']:
  t=seam['seconds']
  for offset in [-.04,0,.04]:
   assert not visible(c,t+offset),f'Exposed seam at {t}'
 for k in ['audio','srt','avatar']:assert Path(c[k]).is_file(),c[k]
 for s in scenes:
  if s.get('asset'):assert Path(s['asset']).is_file(),s['asset']
class NativeDraw:
 def __init__(self,im,scale):self.d=ImageDraw.Draw(im);self.scale=scale
 def xy(self,v):return tuple(round(x*self.scale) for x in v)
 def text(self,xy,*args,**kw):return self.d.text(self.xy(xy),*args,**kw)
 def textlength(self,*args,**kw):return self.d.textlength(*args,**kw)/self.scale
 def line(self,xy,**kw):
  kw['width']=max(1,round(kw.get('width',1)*self.scale));return self.d.line(self.xy(xy),**kw)
 def rectangle(self,xy,**kw):return self.d.rectangle(self.xy(xy),**kw)
 def rounded_rectangle(self,xy,radius=0,**kw):return self.d.rounded_rectangle(self.xy(xy),round(radius*self.scale),**kw)
 def ellipse(self,xy,**kw):
  if 'width' in kw:kw['width']=max(1,round(kw['width']*self.scale))
  return self.d.ellipse(self.xy(xy),**kw)
class Painter:
 def __init__(self,c,scenes):
  self.scale=c.get('renderWidth',1920)/W;self.size=(round(W*self.scale),round(H*self.scale))
  self.c=c;self.scenes=scenes;self.caps=srt(c['srt']);self.fonts={n:ImageFont.truetype(c['font'],round(n*self.scale)) for n in [16,18,20,22,24,26,28,30,32,36,40,44,48,64,72]};self.assets={};self.static={};self.bilingual=read(c['bilingualCaptions']) if c.get('bilingualCaptions') else None
  for s in scenes:
   if s.get('asset'):self.assets[s['asset']]=Image.open(s['asset']).convert('RGB')
 def text(self,d,xy,text,size=28,fill=PAPER):d.text(xy,str(text),font=self.fonts[size],fill=fill)
 def contain(self,im,img,box):
  x,y,w,h=[round(v*self.scale) for v in box];a=img.copy();a.thumbnail((w,h),Image.Resampling.LANCZOS);im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2))
 def frame(self,t,avatar):
  s=next((s for s in self.scenes if s['start']<=t<s['end']),self.scenes[-1]);u=t-s['start'];v=min(1,u/1.2);p=(t-s['start'])/(s['end']-s['start']);idx=self.scenes.index(s);host=s.get('speaker')=='host';show=visible(self.c,t)
  im=Image.new('RGB',self.size,BG);d=NativeDraw(im,self.scale)
  for x in range(0,W,80):d.line((x,0,x,H),fill='#132236')
  self.text(d,(50,24),'月明水清深',20);self.text(d,(1020,26),'AI 协作组织',18,MUTED)
  self.text(d,(50,88),s['eyebrow'],16,GREEN);self.text(d,(50,124),s['title'],40);self.text(d,(50,183),s['accent'],28,GREEN)
  bw=830 if host else 1140;top=255
  typ=s.get('visual','asset' if s.get('asset') else 'list')
  if typ=='hook':
   for j,(label,val) in enumerate([('个人产出',.25+.68*min(1,u/3)),('组织协作',.25)]):
    y=300+j*110;self.text(d,(60,y),label,28);d.rounded_rectangle((240,y,800,y+34),8,fill='#1f3249');d.rounded_rectangle((240,y,240+560*val,y+34),8,fill=GREEN if j==0 else '#8c99aa')
   self.text(d,(60,545),'瓶颈在交接，不在账号数量',30)
  elif typ=='numbers':
   for j,(val,label) in enumerate(zip(['3','5','近 100 万','约 1500'],['工程师','个月','行代码','合并 PR'])):
    x=55+j*285;self.text(d,(x,300+int(10*(1-v))),val,48,GREEN);self.text(d,(x,370),label,24,MUTED)
   d.line((55,435,1170,435),fill='#2c405a',width=2);self.text(d,(55,477),'起初仍被“看不见环境”卡住',32)
  elif typ=='stack':
   for j,x in enumerate(['业务目标','共享上下文','执行工具','评估反馈','权限审计']):
    y=247+j*65;active=j<=int(min(.999,p)*5);d.rounded_rectangle((70,y,1110,y+48),8,fill='#2b3a52' if active else '#172739');self.text(d,(92,y+5),x,26,GREEN if active else MUTED)
  elif typ=='tools':
   self.text(d,(70,275),'全部预载',28);self.text(d,(700,275),'按需发现',28)
   for j in range(20):
    x=70+(j%5)*90;y=345+(j//5)*44;d.rounded_rectangle((x,y,x+72,y+24),5,fill='#24364d')
   self.text(d,(70,555),'100+ 工具 · 额外 5–7 万 Token',24,MUTED)
   d.rounded_rectangle((700,340,1130,475),12,fill='#2b3a52');self.text(d,(735,380),'Tool Search',40,GREEN);self.text(d,(700,525),'只加载当前任务所需工具',26)
  elif typ=='eval':
   for j,(a,b) in enumerate([('成本','每个已合并 PR / 评审 / 告警'),('质量','回滚率 / F1'),('恢复','恢复时间')]):
    y=265+j*100;d.rectangle((65,y,71,y+62),fill=GREEN if p>(j/4) else '#2a3c54');self.text(d,(92,y),a,30);self.text(d,(270,y+4),b,26,MUTED)
  elif typ=='audit':
   self.text(d,(65,270),'调用链：谁发起 · 谁授权 · 调了什么',32)
   for j,x in enumerate(['身份可确认','调用可追溯','权限可收回']):self.text(d,(65,350+j*65),x,30,GREEN if j<=int(p*3) else MUTED)
   self.text(d,(700,340),'自主程度',26);d.line((710,495,1150,350),fill='#2c405a',width=8);q=(math.sin(p*math.pi)*.85);d.ellipse((700+440*q,485-145*q,720+440*q,505-145*q),fill=GREEN)
  elif typ=='minimal':
   for j,x in enumerate(['选一条高频任务','写清目标与输入','接工具，建验收','把失败原因回写']):
    y=262+j*72;active=j<=int(p*4);self.text(d,(65,y),f'{j+1:02d}',26,GREEN if active else MUTED);self.text(d,(140,y),x,32,PAPER if active else MUTED)
  elif typ=='closing':
   for j,x in enumerate(['人的判断 → 系统记住','一次失败 → 流程改进','个人经验 → 组织能力']):self.text(d,(60,290+j*90),x,32,GREEN if j==2 else PAPER)
  elif s.get('asset'):
   box=(55,245,820 if host else 1140,350)
   if s.get('visual')=='product':
    box=(60,245,590,350);self.text(d,(705,300),'作品 ID 一路传递',32,GREEN)
    for j,x in enumerate(['证据与版本不断链','审核状态持续保留','平台数据回到下一轮']):self.text(d,(705,375+j*62),x,26)
   self.contain(im,self.assets[s['asset']],box)
   # A quiet progress rail marks continued explanation without modifying evidence.
   d=NativeDraw(im,self.scale);d.rectangle((55,603,55+int(1130*p),606),fill=GREEN)
  else:
   for j,x in enumerate(s.get('items',[])):self.text(d,(70,280+j*95),x,32,GREEN if j==int(p*len(s.get('items',[]))) else PAPER)
  if show and avatar is not None:
   before=im.copy()
   if host:
    self.contain(im,avatar,(942,83,288,512));d=NativeDraw(im,self.scale);d.line((917,95,917,590),fill='#2c405a',width=2)
   else:
    unit=avatar.width/288;side=round(142*self.scale);face=avatar.crop(tuple(round(v*unit) for v in (40,15,250,225))).resize((side,side));mask=Image.new('L',(side,side));ImageDraw.Draw(mask).ellipse((0,0,side-1,side-1),fill=255);im.paste(face,(round(1070*self.scale),round(82*self.scale)),mask);d=NativeDraw(im,self.scale);d.ellipse((1068,80,1214,226),outline=GREEN,width=3)
  if show and avatar is not None and self.c.get('speakerTransitionSeconds'):
   im=Image.blend(before,im,reveal(self.c,t))
  d=NativeDraw(im,self.scale)
  if self.bilingual:
   for cue in self.bilingual:
    if cue['start']<=t<cue['end']:
     zh=wrap_text(d,cue['zh'],self.fonts[24],1150);en=wrap_text(d,cue['en'],self.fonts[18],1150)
     assert len(zh)<=2 and len(en)<=2,'Caption exceeds bilingual safe area'
     height=len(zh)*29+len(en)*23+9;y=H-8-height
     d.rectangle((32,y-4,1248,H),fill='#0a1420')
     for line in zh:
      tw=d.textlength(line,font=self.fonts[24]);self.text(d,((W-tw)/2,y),line,24);y+=29
     y+=5
     for line in en:
      tw=d.textlength(line,font=self.fonts[18]);self.text(d,((W-tw)/2,y),line,18,MUTED);y+=23
     break
  else:
   for a,b,txt in self.caps:
    if a<=t<b:
     lines=wrap_text(d,txt,self.fonts[24],1150);y=H-12-29*len(lines)
     for line in lines:
      tw=d.textlength(line,font=self.fonts[24]);self.text(d,((W-tw)/2,y),line,24);y+=29
     break
  if self.c.get('chapters'):
   d.rectangle((0,0,W,65),fill=BG);chap=self.c['chapters'];cw=1180/len(chap)
   for j,ch in enumerate(chap):
    x=50+j*cw;frac=max(0,min(1,(t-ch['start'])/(ch['end']-ch['start'])))
    d.rounded_rectangle((x,18,x+cw-4,54),6,fill='#182a40')
    if frac>0:d.rectangle((x,18,x+(cw-4)*frac,54),fill='#9b4f2c')
    tw=d.textlength(ch['label'],font=self.fonts[16]);self.text(d,(x+(cw-4-tw)/2,26),ch['label'],16)
  else:d.rectangle((0,H-4,int(W*t/self.c['duration']),H),fill=GREEN)
  self.text(d,(50,224),'月明水清深 · '+s.get('sourceLabel','概念演示'),16,MUTED);self.text(d,(1100,64),'AI 合成演示',16,MUTED)
  return im

def main():
 a=argparse.ArgumentParser();a.add_argument('config');a.add_argument('--out',required=True);a.add_argument('--duration',type=float);a.add_argument('--frames-dir');v=a.parse_args();c=read(v.config);scenes=read(c['scenes']);validate(c,scenes);p=Painter(c,scenes);duration=min(v.duration or c['duration'],c['duration']);total=math.ceil(duration*FPS)
 decode_w,decode_h=round(288*p.scale),round(512*p.scale)
 out=Path(v.out);out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():raise FileExistsError(out)
 decode=subprocess.Popen(['ffmpeg','-v','error','-i',c['avatar'],'-vf',f'fps=25,scale={decode_w}:{decode_h}:flags=lanczos','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 encode=subprocess.Popen(['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s',f'{p.size[0]}x{p.size[1]}','-r','25','-i','-','-i',c['audio'],'-map','0:v','-map','1:a:0','-t',str(duration),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-preset','fast','-c:a','copy','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 last=None
 try:
  for i in range(total):
   raw=decode.stdout.read(decode_w*decode_h*3)
   if len(raw)==decode_w*decode_h*3:last=Image.frombytes('RGB',(decode_w,decode_h),raw)
   elif visible(c,i/FPS):raise ValueError('Avatar ends during a visible speaker window')
   else:last=None
   im=p.frame(i/FPS,last);encode.stdin.write(im.tobytes())
   if v.frames_dir and (i%250==0 or any(abs(i/25-s['start'])<.02 for s in scenes)):
    q=Path(v.frames_dir);q.mkdir(exist_ok=True,parents=True);im.save(q/f'{i:05d}.jpg')
   if i%500==0:print(f'{i}/{total}',flush=True)
  encode.stdin.close();code=encode.wait()
  if code:raise RuntimeError('ffmpeg encode failed')
 finally:
  decode.stdout.close();decode.terminate();decode.wait()
  if encode.poll() is None:
   encode.kill();encode.wait()
 print(str(out),flush=True)
if __name__=='__main__':main()
