import hashlib
import importlib.metadata
import json
from pathlib import Path
import zipfile

archive = Path('/tmp/monitoring-alfworld-tasks.zip')
with zipfile.ZipFile(archive) as z:
    files = sorted(n for n in z.namelist() if n.endswith('game.tw-pddl'))
    print(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                      'games':len(files),'first_names':files[:8],
                      'last_names':files[-4:],'uncompressed_bytes':sum(i.file_size for i in z.infolist())},indent=2))
    selections=[]
    for split in ['train', 'valid_seen', 'valid_unseen']:
        matches=[name for name in files if '/' + split + '/' in name]
        if matches:
            selections.append(matches[0])
    if not selections:
        selections=files[:1]
    for name in selections:
        dst=Path('/tmp/monitoring-alfworld-games')/name
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(z.read(name))
        data=json.loads(dst.read_text())
        print(json.dumps({'selected':str(dst),'keys':list(data),'content_preview':str(data)[:1500]},indent=2))
print(json.dumps({name:importlib.metadata.version(name) for name in ['alfworld','textworld','fast-downward-textworld','numpy']},indent=2))
import textworld
print('TEXTWORLD_IMPORT_OK')
