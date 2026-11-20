import os, shutil

print('=== NBIA Data Retriever Check ===')

for name in ['NBIADataRetriever', 'nbia-data-retriever', 'nbia']:
    found = shutil.which(name)
    print(f'  which({name}): {found}')

locations = [
    r'C:\Program Files\NBIA Data Retriever\NBIADataRetriever.exe',
    r'C:\Program Files (x86)\NBIA Data Retriever\NBIADataRetriever.exe',
    r'C:\Program Files\NBIA Data Retriever',
    r'C:\Program Files (x86)\NBIA Data Retriever',
]
for loc in locations:
    exists = os.path.exists(loc)
    status = 'EXISTS' if exists else 'not found'
    print(f'  {loc}: {status}')

for pf in [r'C:\Program Files', r'C:\Program Files (x86)']:
    if os.path.exists(pf):
        try:
            items = [x for x in os.listdir(pf) if 'nbia' in x.lower() or 'tcia' in x.lower() or 'retriever' in x.lower()]
            if items:
                print(f'  Found in {pf}: {items}')
        except Exception as e:
            print(f'  Could not list {pf}: {e}')

start_menu = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
if os.path.exists(start_menu):
    for root, dirs, files in os.walk(start_menu):
        for f in files:
            if 'nbia' in f.lower() or 'tcia' in f.lower():
                print(f'  Start Menu entry: {os.path.join(root, f)}')

print()
print('=== Java Check ===')
java = shutil.which('java')
print(f'  java: {java}')

manifest = r'd:\cancer\datasets\cbis_ddsm\CBIS-DDSM-All-doiJNLP-zzWs5zfZ.tcia'
print()
print('=== Manifest File Check ===')
exists = os.path.exists(manifest)
print(f'  Exists: {exists}')
if exists:
    print(f'  Size: {os.path.getsize(manifest):,} bytes')
