"""Switch between the original four lily pads and the experimental six."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mix', choices=('four', 'six'))
args = parser.parse_args()
data = json.loads((ROOT/'tools/lily-pad-original-four.json').read_text())
if args.mix == 'six':
    data['variants'][''] += [
        {'model': 'realm:block/pond/lotus_'+colour, 'y': angle, 'weight': 1}
        for colour in ('aqua', 'yellow') for angle in (0,90,180,270)
    ]
(ROOT/'assets/minecraft/blockstates/lily_pad.json').write_text(json.dumps(data, indent=2)+'\n')
print(f'Enabled {args.mix} equally likely lily pad types. Rebuild the pack or reload the live folder.')
