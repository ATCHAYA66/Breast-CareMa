import os

manifest = r'd:\cancer\datasets\cbis_ddsm\CBIS-DDSM-All-doiJNLP-zzWs5zfZ.tcia'
with open(manifest, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines()]

header = {}
uids = []
in_list = False
for line in lines:
    if line == 'ListOfSeriesToDownload=':
        in_list = True
        continue
    if in_list and line:
        uids.append(line)
    elif not in_list and '=' in line:
        k, v = line.split('=', 1)
        header[k] = v

print('=== TCIA Manifest ===')
for k, v in header.items():
    print(f'  {k} = {v}')
total_uids = len(uids)
print(f'  Total Series UIDs: {total_uids}')

# Split math
e_free_gb   = 135.9
d_usable_gb = 64.0   # 74.1 GB free - 10 GB project buffer

per_series_mb = (163510.0) / total_uids   # 163.51 GB in MB
print()
print('=== Split Strategy ===')
print(f'  Avg MB per series : {per_series_mb:.2f} MB')

e_series = int((e_free_gb * 1024) / per_series_mb)
d_series = total_uids - e_series
e_size_gb = e_series * per_series_mb / 1024
d_size_gb = d_series * per_series_mb / 1024

print(f'  Series -> E:      : {e_series}  (~{e_size_gb:.2f} GB)')
print(f'  Series -> D:      : {d_series}  (~{d_size_gb:.2f} GB)')
print(f'  D: usable         : {d_usable_gb:.2f} GB')
d_ok = 'YES' if d_usable_gb >= d_size_gb else 'NO'
print(f'  D: sufficient     : {d_ok}')

# Write split manifests
def write_manifest(path, uid_list, orig_header):
    with open(path, 'w', encoding='utf-8') as f:
        for k, v in orig_header.items():
            f.write(f'{k}={v}\n')
        f.write('ListOfSeriesToDownload=\n')
        for uid in uid_list:
            f.write(uid + '\n')

e_uids = uids[:e_series]
d_uids = uids[e_series:]

e_manifest = r'd:\cancer\datasets\cbis_ddsm\manifest_part_E.tcia'
d_manifest = r'd:\cancer\datasets\cbis_ddsm\manifest_part_D.tcia'

write_manifest(e_manifest, e_uids, header)
write_manifest(d_manifest, d_uids, header)

print()
print(f'  E: manifest saved : {e_manifest}  ({len(e_uids)} UIDs)')
print(f'  D: manifest saved : {d_manifest}  ({len(d_uids)} UIDs)')
print()
print('  ORIGINAL manifest preserved at:')
print(f'  {manifest}')
