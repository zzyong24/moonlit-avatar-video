import json,tempfile,unittest
from pathlib import Path
from render_avatar import validate,visible,reveal
from plan_visible_lipsync import plan
class SeamTests(unittest.TestCase):
 def test_arbitrary_gesture_duration_and_exposed_seam(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'asset').touch();(p/'plan').write_text(json.dumps({'fps':25,'audioDurationSeconds':10,'seams':[{'seconds':3.2},{'seconds':7.64}]}))
   c={'production_mode':'avatar_explainer','aspectRatio':'16:9','duration':10,'gesturePlan':str(p/'plan'),'audio':str(p/'asset'),'avatar':str(p/'asset'),'srt':str(p/'asset'),'speakerWindows':[[0,10]],'hiddenSeamWindows':[[3,3.5],[7.4,7.9]]}
   validate(c,[{'start':0,'end':10}]);self.assertFalse(visible(c,3.2));self.assertTrue(visible(c,4))
   c['hiddenSeamWindows']=c['hiddenSeamWindows'][:1]
   with self.assertRaisesRegex(AssertionError,'Exposed seam'):validate(c,[{'start':0,'end':10}])
 def test_reject_gap(self):
  with self.assertRaises(AssertionError):validate({'production_mode':'avatar_explainer','aspectRatio':'16:9','duration':10},[{'start':0,'end':4},{'start':5,'end':10}])
class WindowTests(unittest.TestCase):
 def test_guard_merge_and_back_mapping(self):
  c={'duration':20,'speakerWindows':[[2,4],[4.5,6],[12,15]]}
  p=plan(c);self.assertEqual(len(p['segments']),2)
  self.assertAlmostEqual(p['packedSeconds'],8.6)
  for x in p['segments']:self.assertAlmostEqual(x['timelineEnd']-x['timelineStart'],x['packedEnd']-x['packedStart'])
 def test_reveal_never_leaks_outside_window(self):
  c={'speakerWindows':[[1,3]],'hiddenSeamWindows':[],'speakerTransitionSeconds':.4}
  self.assertEqual(reveal(c,.99),0);self.assertEqual(reveal(c,3),0)
  self.assertAlmostEqual(reveal(c,1.2),.5);self.assertEqual(reveal(c,2),1)
if __name__=='__main__':unittest.main()
