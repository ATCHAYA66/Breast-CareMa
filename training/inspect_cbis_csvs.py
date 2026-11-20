import csv
from collections import Counter, defaultdict

artifact_base = r'C:\Users\Nivek Nachimuthu\.gemini\antigravity\brain\6d8d94f9-6fce-4c2a-a8c9-968e00ad7b32\.user_uploaded'

files = {
    'calc_train': (artifact_base + r'\media_1795091223872_db005639.csv', 'calc'),
    'mass_train': (artifact_base + r'\media_1795091223893_f4203a21.csv', 'mass'),
    'calc_test':  (artifact_base + r'\media_1795091223538_87ac3ab2.csv', 'calc'),
    'mass_test':  (artifact_base + r'\media_1795091223830_9438cb3c.csv', 'mass'),
}

totals = defaultdict(int)
all_patients = set()
train_patients = set()
test_patients = set()

for split_name, (path, abntype) in files.items():
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    is_train = 'train' in split_name
    pathology = Counter(r['pathology'] for r in rows)
    patients = set(r['patient_id'] for r in rows)
    print(f'{split_name}: {len(rows)} rows | patients: {len(patients)} | {dict(pathology)}')

    if is_train:
        train_patients |= patients
    else:
        test_patients |= patients
    all_patients |= patients

    totals[split_name + '_rows'] = len(rows)
    totals[split_name + '_benign'] = pathology.get('BENIGN', 0) + pathology.get('BENIGN_WITHOUT_CALLBACK', 0)
    totals[split_name + '_malignant'] = pathology.get('MALIGNANT', 0)

overlap = train_patients & test_patients
print()
print(f'Total unique patients in TRAIN: {len(train_patients)}')
print(f'Total unique patients in TEST:  {len(test_patients)}')
print(f'Total unique patients overall:  {len(all_patients)}')
print(f'PATIENT OVERLAP (train & test): {len(overlap)} -- should be 0')

total_rows = sum(totals[k] for k in totals if k.endswith('_rows'))
total_benign = sum(totals[k] for k in totals if k.endswith('_benign'))
total_malignant = sum(totals[k] for k in totals if k.endswith('_malignant'))
print()
print(f'TOTAL RECORDS: {total_rows}')
print(f'Total Benign (incl. without callback): {total_benign}')
print(f'Total Malignant: {total_malignant}')

# Check image path format
print()
print('=== Image path format samples ===')
for split_name, (path, abntype) in files.items():
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    r = rows[0]
    print(f'{split_name}:')
    print(f'  image file path  : {r.get("image file path", "N/A")}')
    print(f'  cropped file path: {r.get("cropped image file path", "N/A")}')
