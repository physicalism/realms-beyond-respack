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
    require(ended and header[:2] == dimensions and header[2:] in ((8, 6, 0, 0, 0), (8, 2, 0, 0, 0), (4, 3, 0, 0, 0), (8, 3, 0, 0, 0)), f'Unexpected PNG dimensions or format: {path}')
    raw = zlib.decompress(packed)
    width, height = dimensions
    channels = {6: 4, 2: 3, 3: 1}[header[3]]
    stride = 1+(width*channels*header[2]+7)//8
    require(len(raw) == height*stride and all(raw[y*stride] <= 4 for y in range(height)), f'Invalid PNG image data: {path}')


def resource(kind, identifier):
    require(isinstance(identifier, str) and re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', identifier), f'Invalid resource ID: {identifier}')
    namespace, name = identifier.split(':')
    if kind == 'textures':
        require(name.startswith(('item/', 'block/')), f'Texture is outside the supported atlas directories: {identifier}')
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
            dimensions = (64, 64) if identifier.endswith('/frame_1x2v') else ((32, 64) if identifier.endswith('/ivy_crown_detailed') else ((32, 32) if identifier.endswith(('/ivy_music', '/ivy_laptop', '/ivy_pepsi')) else (16, 32)))
            png(path, dimensions)
            used.add(path)
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                require(face['texture'].startswith('#') and face['texture'][1:] in slots, 'Unresolved painting texture slot.')
    # Balcony flowers use a recoloured item-atlas texture; keep the old item ID working.
    for decoration_id in ('realm:balcony_flowers', 'realm:balcony_flowers_corner'):
        decoration = read(resource('items', decoration_id))['model']
        require(decoration['type'] == 'minecraft:model', 'Expected a model decoration item.')
        require(decoration.get('tints') == [{'type': 'minecraft:constant', 'value': 16777215}], 'Incorrect balcony flower tint.')
        resolved = model(decoration['model'])
        require(resolved.get('elements') and resolved.get('display', {}).get('fixed'), 'Missing balcony flower geometry or frame display.')
        slots = resolved['textures']
        for identifier in slots.values():
            path = resource('textures', identifier)
            png(path)
            used.add(path)
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                require(face['texture'].startswith('#') and face['texture'][1:] in slots, 'Unresolved decoration texture slot.')
    require(read(resource('items', 'realm:wall_flowers')) == read(resource('items', 'realm:balcony_flowers')), 'Legacy flower item differs from balcony flowers.')
    # Equal-probability lotus lily pads; support the original four or expanded six.
    lily_variants = read(ROOT/'assets/minecraft/blockstates/lily_pad.json')['variants']['']
    expected_lilies = {'realm:block/pond/'+name for name in ('lily_pad_plain', 'lotus_pink', 'lotus_purple', 'lotus_white', 'lotus_aqua', 'lotus_yellow')}
    active_lilies = {v['model'] for v in lily_variants}
    original_lilies = expected_lilies - {'realm:block/pond/lotus_aqua', 'realm:block/pond/lotus_yellow'}
    require(active_lilies in (original_lilies, expected_lilies), 'Expected the original four or expanded six lily pad types.')
    require(len(lily_variants) == len(active_lilies)*4, 'Expected four rotations per lily pad type.')
    require({(v['model'], v.get('y', 0)) for v in lily_variants} == {(name, angle) for name in active_lilies for angle in (0,90,180,270)}, 'Missing lily pad colour or rotation.')
    require(all(v.get('weight', 1) == 1 for v in lily_variants), 'Lily pad probabilities must be equal.')
    for identifier in expected_lilies:
        resolved = model(identifier)
        require(resolved.get('elements'), 'Missing lily pad geometry.')
        slots = resolved['textures']
        for texture_id in slots.values():
            path = resource('textures', texture_id)
            png(path, (16,16))
            used.add(path)
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                require(face['texture'].startswith('#') and face['texture'][1:] in slots, 'Unresolved lily pad texture slot.')
    # Compatibility IDs share the canonical item's model and tint.
    canonical = {entry['item_model'] for entry in banners}
    for old_id, target_id in catalogue.get('aliases', {}).items():
        require(old_id not in canonical and target_id in canonical, 'Invalid compatibility alias.')
        require(read(resource('items', old_id)) == read(resource('items', target_id)), 'Compatibility alias differs from its target.')
    # First-person lanterns inherit the same block geometry used by NEA in F5.
    lanterns = ('lantern', 'soul_lantern', 'copper_lantern', 'exposed_copper_lantern',
                'weathered_copper_lantern', 'oxidized_copper_lantern', 'waxed_copper_lantern',
                'waxed_exposed_copper_lantern', 'waxed_weathered_copper_lantern', 'waxed_oxidized_copper_lantern')
    for name in lanterns:
        item = read(resource('items', 'minecraft:'+name))['model']
        require(item['type'] == 'minecraft:select' and item['property'] == 'minecraft:display_context', 'Invalid lantern context selection.')
        require(item['fallback'] == {'type': 'minecraft:model', 'model': 'minecraft:item/'+name.removeprefix('waxed_')}, 'Lantern fallback must retain vanilla item model.')
        case, = item['cases']
        require(set(case['when']) == {'firstperson_righthand', 'firstperson_lefthand', 'thirdperson_righthand', 'thirdperson_lefthand'}, 'Lantern override must cover vanilla and Punchy hand contexts.')
        wrapper = read(resource('models', case['model']['model']))
        require(wrapper['parent'] == 'minecraft:block/'+name.removeprefix('waxed_'), 'Lantern must inherit its matching block model.')
        require('elements' not in wrapper and 'textures' not in wrapper, 'Lantern must preserve block geometry and textures.')
    # Imported furniture uses item-atlas textures and optional animated atlases.
    for name in ('magic_book_stack', 'ancient_spellbook', 'dreamcatcher', 'incense_pot',
                 'scarecrow', 'scarecrow_farm_1'):
        entry = read(resource('items', 'realm:'+name))['model']
        require(entry['type'] == 'minecraft:model', 'Expected a decoration model item.')
        resolved = model(entry['model'])
        require(resolved.get('elements') and resolved.get('display', {}).get('fixed'), 'Missing decoration geometry or frame display.')
        slots = resolved['textures']
        atlas_paths = {identifier.split(':', 1)[1].split('/', 1)[0] for identifier in slots.values()}
        require(len(atlas_paths) == 1, f'Decoration model {name} mixes block and item texture atlases.')
        for identifier in slots.values():
            if identifier.startswith('minecraft:block/'):
                continue  # vanilla block textures ship with the game
            path = resource('textures', identifier)
            dimensions = struct.unpack('>II', path.read_bytes()[16:24])
            png(path, dimensions)
            used.add(path)
            animation = path.with_suffix('.png.mcmeta')
            if animation.exists():
                require('animation' in read(animation), 'Invalid texture animation metadata.')
        for element in resolved['elements']:
            for face in element.get('faces', {}).values():
                require(face['texture'].startswith('#') and face['texture'][1:] in slots, 'Unresolved decoration texture slot.')
    # Ivy shrines: pixel-atlas models.
    # Composite/select items (the wagging tail) are walked down to their plain model leaves.
    def shrine_models(entry):
        kind = entry['type']
        if kind == 'minecraft:model': return [entry['model']]
        if kind == 'minecraft:composite': return [m for sub in entry['models'] for m in shrine_models(sub)]
        if kind == 'minecraft:select':
            require(entry.get('property') == 'minecraft:local_time' and entry.get('pattern'), 'Unsupported shrine select.')
            return [m for c in entry['cases'] for m in shrine_models(c['model'])] + shrine_models(entry['fallback'])
        raise ValueError('Invalid shrine item type.')
    for name in ('ivy_shrine', 'ivy_shrine_stone', 'lucky_ivy', 'lucky_ivy_coloured'):
      for model_id in dict.fromkeys(shrine_models(read(resource('items', 'realm:'+name))['model'])):
        resolved = model(model_id)
        require(resolved.get('display', {}).get('fixed'), 'Missing shrine frame display.')
        for identifier in resolved['textures'].values():
            path = resource('textures', identifier)
            png(path, struct.unpack('>II', path.read_bytes()[16:24]))
            used.add(path)
            animation = path.with_suffix('.png.mcmeta')
            if animation.exists():
                require('animation' in read(animation), 'Invalid texture animation metadata.')
                used.add(animation)
        for element in resolved['elements']:
            require(all(-16 <= a < b <= 32 for a, b in zip(element['from'], element['to'])), 'Shrine cuboid exceeds Java model limits.')
            require(set(element['faces']) == {'north','south','east','west','up','down'}, 'Shrine cuboid needs all six faces.')
            for face in element['faces'].values():
                require(face['texture'][1:] in resolved['textures'] and all(0 <= v <= 16 for v in face['uv']), 'Invalid shrine UVs.')
    # Stag fountain: item_display pieces; stone and water use vanilla block textures.
    for name in ('pedestal', 'stag', 'basin_ne', 'basin_nw', 'basin_se', 'basin_sw'):
        entry = read(resource('items', 'realm:stag_fountain_'+name))['model']
        require(entry['type'] == 'minecraft:model', 'Expected a fountain model item.')
        resolved = model(entry['model'])
        require(resolved.get('elements'), 'Missing fountain geometry.')
        slots = resolved['textures']
        atlas_paths = {identifier.split(':', 1)[1].split('/', 1)[0] for identifier in slots.values()}
        require(len(atlas_paths) == 1, f'Fountain model {name} mixes block and item texture atlases.')
        for identifier in slots.values():
            if identifier.startswith('minecraft:block/'):
                continue
            path = resource('textures', identifier)
            png(path, struct.unpack('>II', path.read_bytes()[16:24]))
            used.add(path)
            animation = path.with_suffix('.png.mcmeta')
            if animation.exists():
                require('animation' in read(animation), 'Invalid texture animation metadata.')
        for element in resolved['elements']:
            require(all(-16 <= a <= b <= 32 for a, b in zip(element['from'], element['to'])), 'Fountain cuboid exceeds Java model limits.')
            for face in element['faces'].values():
                require(face['texture'][1:] in slots and all(0 <= v <= 16 for v in face['uv']), 'Invalid fountain face.')
    # Override the vanilla disc 13 recording without changing other music.
    recording = ROOT/'assets/minecraft/sounds/records/13.ogg'
    audio = recording.read_bytes()
    require(audio.startswith(b'OggS') and b'\x01vorbis' in audio[:128], 'Disc 13 must use Ogg Vorbis audio.')
    used.add(recording)
    for language in ('en_us', 'en_gb'):
        names = read(ROOT/f'assets/minecraft/lang/{language}.json')
        require(names.get('item.minecraft.music_disc_13') == 'Korra Record', 'Missing custom disc name.')
        require(names.get('jukebox_song.minecraft.13') == 'The Legend of Korra - End Credits', 'Missing track description.')
    # The live flat path test and the archived 3D test use the same asset locations.
    modifier_dir = ROOT/'assets/realm/fusion/model_modifiers/blocks'
    for modifier_path in sorted(modifier_dir.glob('*path_edge_test.json')):
        modifier = read(modifier_path)
        entries = modifier.get('default_model_overrides', []) + modifier.get('append_models', [])
        for entry in entries:
            edge_model = read(resource('models', entry if isinstance(entry, str) else entry['model']))
            for sprite in edge_model['textures'].values():
                if not sprite.startswith('realm:block/path_edge_test/'):
                    continue
                path_sprite = resource('textures', sprite)
                if path_sprite not in used:
                    png(path_sprite, (32, 32) if path_sprite.stem.startswith('flat_') else (16, 16))
                    used.add(path_sprite)
                    metadata = read(path_sprite.with_suffix('.png.mcmeta'))['fusion']
                    require(metadata['render_type'] == 'cutout', 'Path edges must use cutout textures.')
    # Pack-owned textures referenced by block/item models (sizes come from the PNG header).
    def own_sprite(identifier):
        path = resource('textures', identifier)
        if path in used: return
        data = path.read_bytes()
        require(data[12:16] == b'IHDR', f'Invalid PNG: {path}')
        png(path, struct.unpack('>II', data[16:24]))
        used.add(path)
        meta = path.with_suffix('.png.mcmeta')
        if meta.exists(): read(meta)
    def own_model(identifier):
        model = read(resource('models', identifier))
        for sprite in model.get('textures', {}).values():
            if not sprite.startswith('#') and not sprite.startswith('minecraft:'): own_sprite(sprite)
    # Signs and the animated war banner: pack-owned models with their own textures.
    for sign in ('realm:blacksmith_sign', 'realm:town_clocktower_sign', 'realm:banner_stag_war_azure'):
        own_model(read(resource('items', sign))['model']['model'])
    # Lawn stones: random variants of the vanilla grass blockstate (tools/lawn-decor/gen_decor.py).
    grass = read(ROOT/'assets/minecraft/blockstates/grass_block.json')
    for variant in grass['variants']['snowy=false']:
        if variant['model'].startswith('realm:'): own_model(variant['model'])
    # Path edges and lawn tiles (tools/path-edges/gen.py): every model a Fusion modifier references.
    for modifier_path in sorted((ROOT/'assets/realm/fusion/model_modifiers/blocks').glob('*.json')):
        modifier = read(modifier_path)
        for entry in modifier.get('default_model_overrides', []) + modifier.get('append_models', []):
            own_model(entry if isinstance(entry, str) else entry['model'])
    # Wearable cosmetics (realms_beyond_cosmetics namespace).
    cosmetics = ROOT/'assets/realms_beyond_cosmetics'
    if cosmetics.exists():
        for item_path in sorted((cosmetics/'items').glob('*.json')):
            own_model(read(item_path)['model']['model'])
        for model_path in sorted((cosmetics/'models/item').glob('*.json')):
            own_model('realms_beyond_cosmetics:item/'+model_path.stem)
        wardrobe = cosmetics/'wardrobe.properties'
        if wardrobe.exists():
            require(wardrobe.read_text().strip() != '', 'Empty wardrobe.properties.')
            used.add(wardrobe)
    actual = {p for p in (ROOT/'assets').rglob('*') if p.is_file() and not any(s.startswith('.') for s in p.relative_to(ROOT).parts)}
    require(actual == used, 'Unexpected or unused assets: '+str(sorted(str(p.relative_to(ROOT)) for p in actual-used)))
    metadata = json.loads((ROOT/'pack.mcmeta').read_text())
    require(metadata['pack']['min_format'] == [97,1] and metadata['pack']['max_format'] == [97,1], 'Unexpected Minecraft resource-pack format.')
    version()
    return used


def build():
    metadata_path = ROOT/'pack.mcmeta'
    metadata = json.loads(metadata_path.read_text())
    metadata['pack']['description'] = f'§5■ §bv{version()}\n§5■ §6By Henry§r'
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
    print(f'Built {output.name}: 96 banners, Ivy paintings, balcony flowers, and lotus lily pads, {len(files)} files; SHA-256 {digest}')
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
            print('Validated all 96 banners, Ivy paintings, balcony flowers, and resource references.')
        else:
            build()
    except (ValueError, OSError, KeyError, struct.error, zlib.error) as error:
        parser.exit(1, f'Build failed: {error}\n')
