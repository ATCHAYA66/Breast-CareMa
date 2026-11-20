import shutil, os

drives = [('C:', 'System'), ('D:', 'Project Drive'), ('E:', 'Available')]
print('=== Storage Decision Summary ===')
for d, label in drives:
    try:
        total, used, free = shutil.disk_usage(d + '\\')
        status = 'SUFFICIENT (180+ GB)' if free/(1024**3) >= 180 else ('MARGINAL (100-180 GB)' if free/(1024**3) >= 100 else 'INSUFFICIENT (<100 GB)')
        print(f'{d} ({label}): {free/(1024**3):.1f} GB free / {total/(1024**3):.1f} GB total  [{status}]')
    except Exception as e:
        print(f'{d}: not accessible ({e})')

print()
print('=== Image Download Target Candidates ===')
candidates = [
    r'd:\cancer\datasets\cbis_ddsm\images',
    r'e:\cbis_ddsm\images',
    r'e:\cancer\datasets\cbis_ddsm\images',
]
for d in candidates:
    exists = os.path.exists(d)
    if exists:
        count = sum(len(files) for _, _, files in os.walk(d))
        print(f'  {d}: EXISTS, {count} files inside')
    else:
        print(f'  {d}: does not exist yet')
