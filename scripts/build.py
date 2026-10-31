from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / "builds" / "Realm-Resource-Pack-v0.4.0.zip"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
files = [ROOT / "pack.mcmeta", *sorted((ROOT / "assets").rglob("*"))]
files = [p for p in files if p.is_file() and not any(part.startswith(".") for part in p.relative_to(ROOT).parts)]
for path in files:
    if path.suffix == ".json" or path.name == "pack.mcmeta":
        json.loads(path.read_text())
for path in (ROOT / "assets/realm/items").glob("*.json"):
    model = json.loads(path.read_text())["model"]["model"]
    namespace, location = model.split(":")
    assert (ROOT / f"assets/{namespace}/models/{location}.json").is_file(), model
for path in (ROOT / "assets/realm/models").rglob("*.json"):
    for texture in json.loads(path.read_text()).get("textures", {}).values():
        if texture.startswith("#"):
            continue
        namespace, location = texture.split(":")
        assert (ROOT / f"assets/{namespace}/textures/{location}.png").is_file(), texture
with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(ROOT))
with zipfile.ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
print(f"Built {OUTPUT.name}: {len(files)} files; JSON and resource references validated")
