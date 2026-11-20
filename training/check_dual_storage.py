import shutil, os

print('=== Live Drive Storage ===')
drives = [('D:', 'Project Drive'), ('E:', 'Image Drive')]
results = {}
for d, label in drives:
    total, used, free = shutil.disk_usage(d + '\\')
    results[d] = {'total': total, 'used': used, 'free': free}
    total_gb = total / (1024**3)
    used_gb  = used  / (1024**3)
    free_gb  = free  / (1024**3)
    print(f'{d} ({label}):  Total={total_gb:.2f} GB  Used={used_gb:.2f} GB  Free={free_gb:.2f} GB')

d_free = results['D:']['free'] / (1024**3)
e_free = results['E:']['free'] / (1024**3)
combined = d_free + e_free
required = 163.51
buffer   = 15.0
total_needed = required + buffer

print()
print('=== Combined Capacity ===')
print(f'D: free        : {d_free:.2f} GB')
print(f'E: free        : {e_free:.2f} GB')
print(f'Combined free  : {combined:.2f} GB')
print(f'Required       : {required:.2f} GB (TCIA estimate)')
print(f'Buffer (safety): {buffer:.2f} GB')
print(f'Total needed   : {total_needed:.2f} GB')
surplus = combined - total_needed
if surplus >= 0:
    print(f'Surplus        : +{surplus:.2f} GB  [SUFFICIENT]')
else:
    print(f'Deficit        : {surplus:.2f} GB  [INSUFFICIENT]')

print()
print('=== D:\\cancer project folder sizes ===')
for item in sorted(os.listdir(r'd:\cancer')):
    p = os.path.join(r'd:\cancer', item)
    if os.path.isdir(p):
        size = sum(os.path.getsize(os.path.join(root, f))
                   for root, _, files in os.walk(p) for f in files)
        print(f'  {item}/  {size/(1024**3):.3f} GB')
    else:
        size = os.path.getsize(p)
        print(f'  {item}  {size/(1024**2):.1f} MB')

print()
print('=== E:\\ drive contents ===')
for item in sorted(os.listdir('E:\\')):
    p = os.path.join('E:\\', item)
    try:
        if os.path.isdir(p):
            size = sum(os.path.getsize(os.path.join(root, f))
                       for root, _, files in os.walk(p) for f in files)
            print(f'  {item}/  {size/(1024**3):.3f} GB')
        else:
            size = os.path.getsize(p)
            print(f'  {item}  {size/(1024**2):.1f} MB')
    except Exception as e:
        print(f'  {item}  [error: {e}]')

print()
print('=== CBIS-DDSM folder structure ===')
cbis_dir = r'd:\cancer\datasets\cbis_ddsm'
for root, dirs, files in os.walk(cbis_dir):
    dirs[:] = [d for d in dirs if '__pycache__' not in d]
    level = root.replace(cbis_dir, '').count(os.sep)
    indent = '  ' * level
    folder = os.path.basename(root)
    print(f'{indent}{folder}/')
    for f in files:
        fp = os.path.join(root, f)
        print(f'{indent}  {f}  ({os.path.getsize(fp):,} bytes)')

junction = r'd:\cancer\datasets\cbis_ddsm\images'
print()
print(f'Junction {junction}: exists={os.path.exists(junction)}')
