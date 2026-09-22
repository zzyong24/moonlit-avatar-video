#!/usr/bin/env python3
"""Plan one packed lip-sync job for visible windows. No provider calls or billing."""
import argparse,json
from pathlib import Path
def plan(c,handle=.4):
 windows=sorted(c['speakerWindows']);merged=[]
 for start,end in windows:
  assert 0<=start<end<=c['duration']
  a=max(0,start-handle);b=min(c['duration'],end+handle)
  if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
  else:merged.append([a,b])
 packed=0;segments=[]
 for a,b in merged:
  n=b-a;segments.append({'timelineStart':a,'timelineEnd':b,'packedStart':round(packed,3),'packedEnd':round(packed+n,3),'source':'original gesture master + matching original narration; never old lip-sync'});packed+=n
 return {'status':'planned_not_submitted','handleSeconds':handle,'visibleSeconds':round(sum(b-a for a,b in windows),3),'packedSeconds':round(packed,3),'fullNarrationSeconds':c['duration'],'segments':segments,'jobCount':1,'instructions':'Cut source gestures and original audio by matching timeline interval; concatenate both in identical order. Generate once. Map output back using packedStart/packedEnd and show only speakerWindows. Handles remain hidden. Verify output duration and boundary quality before use. Recheck provider pricing at submission.'}
def main():
 a=argparse.ArgumentParser();a.add_argument('config');a.add_argument('--out',required=True);v=a.parse_args();c=json.loads(Path(v.config).read_text());Path(v.out).write_text(json.dumps(plan(c),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
