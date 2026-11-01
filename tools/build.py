"""Validate and build Realms Beyond using Python's standard library only."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def version():
    value = (ROOT / 'tools' / 'VERSION').read_text().strip()
    require(re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', value), 'VERSION must contain a semantic version.')
    return value


def png(path, dimensions=(64, 64)):
    data = path.read_bytes()
    require(data[:8] == b'\x89PNG\r\n\x1a\n', f'Invalid PNG: {path}')
    offset, packed, header, ended = 8, bytearray(), None, False
    while offset < len(data):
        size = struct.unpack('>I', data[offset:offset+4])[0]
        kind, value = data[offset+4:offset+8], data[offset+8:offset+8+size]
        require(len(value) == size, f'Truncated PNG: {path}')
        crc = struct.unpack('>I', data[offset+8+size:offset+12+size])[0]
        require(zlib.crc32(kind+value) & 0xffffffff == crc, f'PNG checksum failure: {path}')
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', value)
        if kind == b'IDAT':
            packed.extend(value)
        if kind == b'IEND':
            ended = True
        offset += size+12
    require(ended and header[:2] == dimensions and header[2:] in ((8, 6, 0, 0, 0), (8, 2, 0, 0, 0), (4, 3, 0, 0, 0)), f'Unexpected PNG dimensions or format: {path}')
    raw = zlib.decompress(packed)
    width, height = dimensions
    channels = {6: 4, 2: 3, 3: 1}[header[3]]
    stride = 1+(width*channels*header[2]+7)//8
    require(len(raw) == height*stride and all(raw[y*stride] <= 4 for y in range(height)), f'Invalid PNG image data: {path}')


def resource(kind, identifier):
    require(isinstance(identifier, str) and re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', identifier), f'Invalid resource ID: {identifier}')
    namespace, name = identifier.split(':')
    if kind == 'textures':
        require(name.startswith('item/'), f'Banner texture is outside the item atlas directory: {identifier}')
    require('..' not in name.split('/'), 'Resource path cannot escape its namespace.')
    return ROOT / 'assets' / namespace / kind / (name + ('.png' if kind == 'textures' else '.json'))


def validate():
    catalogue = json.loads((ROOT / 'tools' / 'catalogue.json').read_text())
    expected = {(m,c,f) for m in catalogue['motifs'] for c in catalogue['dyes'] for f in catalogue['finishes']}
    banners = catalogue['banners']
    require(len(expected) == 96 and len(banners) == 96, 'The pack must contain exactly 96 banners.')
    require({(b['motif'], b['colour'], b['finish']) for b in banners} == expected, 'Missing or duplicated banner combination.')
    require(len({b['item_model'] for b in banners}) == 96, 'Duplicate item model IDs.')
    used, model_cache = set(), {}

    def read(path):
        require(path.is_file(), f'Missing resource: {path}')
        used.add(path)
        return json.loads(path.read_text())

    def model(identifier, stack=()):
        require(identifier not in stack, f'Cyclic model parent: {identifier}')
        if identifier in model_cache:
            return model_cache[identifier]
        data = read(resource('models', identifier))
        inherited = model(data['parent'], stack+(identifier,)) if 'parent' in data else {}
        merged = {**inherited, **data, 'textures': {**inherited.get('textures', {}), **data.get('textures', {})}}
        model_cache[identifier] = merged
        return merged

    for banner in banners:
        item = read(resource('items', banner['item_model']))['model']
        require(item['type'] == 'minecraft:model', 'Expected a vanilla model item.')
        require(item['tints'] == [{'type':'minecraft:constant','value':catalogue['dyes'][banner['colour']]}], 'Incorrect cloth tint.')
        resolved = model(item['model'])
        require(resolved.get('elements') and resolved.get('display', {}).get('fixed'), 'Missing banner geometry or frame display.')
        slots = resolved['textures']

        def texture(value, seen=()):
            if value.startswith('#'):
                slot = value[1:]
                require(slot not in seen and slot in slots, f'Unresolved/cyclic texture slot: {slot}')
                return texture(slots[slot], seen+(slot,))
            require(value == banner['texture'], 'Model uses an unexpected atlas.')
            path = resource('textures', value)
            if path not in used:
                png(path)
                used.add(path)

        for value in slots.values():
            texture(value)
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                texture(face['texture'])
    # Every Ivy variant shares the same frame and item-atlas requirements.
    for item_path in sorted((ROOT/'assets/realm/items').glob('painting_ivy*.json')):
        painting = read(item_path)['model']
        require(painting['type'] == 'minecraft:model', 'Expected a model painting item.')
        resolved = model(painting['model'])
        slots = resolved['textures']
        for slot, identifier in slots.items():
            path = resource('textures', identifier)
            dimensions = (64, 64) if identifier.endswith('/frame_1x2v') else ((32, 64) if identifier.endswith('/ivy_crown_detailed') else (16, 32))
            png(path, dimensions)
            used.add(path)
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                require(face['texture'].startswith('#') and face['texture'][1:] in slots, 'Unresolved painting texture slot.')
    # Compatibility IDs share the canonical item's model and tint.
    canonical = {entry['item_model'] for entry in banners}
    for old_id, target_id in catalogue.get('aliases', {}).items():
        require(old_id not in canonical and target_id in canonical, 'Invalid compatibility alias.')
        require(read(resource('items', old_id)) == read(resource('items', target_id)), 'Compatibility alias differs from its target.')
    actual = {p for p in (ROOT/'assets').rglob('*') if p.is_file() and not any(s.startswith('.') for s in p.relative_to(ROOT).parts)}
    require(actual == used, 'Unexpected or unused assets: '+str(sorted(str(p.relative_to(ROOT)) for p in actual-used)))
    metadata = json.loads((ROOT/'pack.mcmeta').read_text())
    require(metadata['pack']['min_format'] == [97,1] and metadata['pack']['max_format'] == [97,1], 'Unexpected Minecraft resource-pack format.')
    version()
    return used


def build():
    metadata_path = ROOT/'pack.mcmeta'
    metadata = json.loads(metadata_path.read_text())
    metadata['pack']['description'] = f'§5■ §bv{version()}\n§5■ §6By Henry §o(emotivist)§r'
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    files = validate() | {ROOT/'pack.mcmeta'}
    if (ROOT/'pack.png').exists():
        files.add(ROOT/'pack.png')
    destination = ROOT/'dist'
    destination.mkdir(exist_ok=True)
    output = destination/f'Realms-Beyond-v{version()}.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), (2020,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        require(archive.testzip() is None, 'ZIP integrity failure.')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n')
    print(f'Built {output.name}: 96 banners and Ivy paintings, {len(files)} files; SHA-256 {digest}')
    # Stable display-name copy for a plain white menu title.
    display_copy = destination/'Realms Beyond.zip'
    display_copy.write_bytes(output.read_bytes())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without building a ZIP.')
    args = parser.parse_args()
    try:
        if args.check:
            validate()
            print('Validated all 96 banners and resource references.')
        else:
            build()
    except (ValueError, OSError, KeyError, struct.error, zlib.error) as error:
        parser.exit(1, f'Build failed: {error}\n')
