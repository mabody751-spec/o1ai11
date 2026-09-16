import json, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
assert (root/'frontend/index.html').exists()
assert (root/'backend/app/main.py').exists()
assets=list((root/'ai/assets').rglob('*'))
assert any(p.suffix=='.ort' for p in assets)
json.load(open(root/'config/models.json'))
print('NADOS AI V1 smoke test: OK')
