"""
CBIS-DDSM Post-Download Validator and Image Index Builder
Scans both download destinations and builds a combined image index CSV.

Usage: python training/validate_cbis_download.py
"""
import os, csv, hashlib
from pathlib import Path

# ─── Configuration ─────────────────────────────────────────────────────────────
# Primary images (Part 1 - E: via junction)
IMAGES_PRIMARY  = Path(r'd:\cancer\datasets\cbis_ddsm\images')
# Overflow images (Part 2 - D:)
IMAGES_OVERFLOW = Path(r'd:\cancer\datasets\cbis_ddsm\images_overflow')
# CSV files
CSV_DIR         = Path(r'd:\cancer\datasets\cbis_ddsm\csv')
# Output index
INDEX_OUT       = Path(r'd:\cancer\datasets\cbis_ddsm\dicom_index.csv')

def count_dcm(folder):
    """Recursively count .dcm files in a folder."""
    total = 0
    total_bytes = 0
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.dcm'):
                total += 1
                total_bytes += os.path.getsize(os.path.join(root, f))
    return total, total_bytes

def build_series_index(folder):
    """Build a dict: SeriesInstanceUID -> list of dcm paths."""
    index = {}
    for root, dirs, files in os.walk(folder):
        dcms = [f for f in files if f.lower().endswith('.dcm')]
        if dcms:
            # TCIA folder structure: <CaseName>/<StudyUID>/<SeriesUID>/<slice>.dcm
            parts = Path(root).parts
            series_uid = parts[-1]  # last folder = SeriesInstanceUID
            index[series_uid] = [os.path.join(root, f) for f in sorted(dcms)]
    return index

def main():
    print("=" * 60)
    print("CBIS-DDSM Post-Download Validation")
    print("=" * 60)

    # Count files in both locations
    print("\n[1] Counting DICOM files...")
    p_count, p_bytes = count_dcm(IMAGES_PRIMARY)
    o_count, o_bytes = count_dcm(IMAGES_OVERFLOW)
    total_count = p_count + o_count
    total_gb    = (p_bytes + o_bytes) / (1024**3)

    print(f"  Primary   (E: via junction): {p_count:,} files  ({p_bytes/(1024**3):.2f} GB)")
    print(f"  Overflow  (D:)             : {o_count:,} files  ({o_bytes/(1024**3):.2f} GB)")
    print(f"  TOTAL                      : {total_count:,} files  ({total_gb:.2f} GB)")

    if total_count == 0:
        print("\n  *** No DICOM files found. Download has not completed yet. ***")
        return

    # Build series index from both locations
    print("\n[2] Building SeriesInstanceUID index...")
    idx_primary  = build_series_index(IMAGES_PRIMARY)
    idx_overflow = build_series_index(IMAGES_OVERFLOW)

    # Merge (primary first, overflow second, flag duplicates)
    merged = {}
    for uid, paths in idx_primary.items():
        merged[uid] = {'location': 'primary', 'paths': paths}
    for uid, paths in idx_overflow.items():
        if uid in merged:
            print(f"  WARNING: Duplicate series {uid} in both locations!")
        else:
            merged[uid] = {'location': 'overflow', 'paths': paths}

    print(f"  Total unique series found: {len(merged):,}")

    # Cross-check against manifests
    print("\n[3] Cross-checking against split manifests...")
    manifest_e = Path(r'd:\cancer\datasets\cbis_ddsm\manifest_part_E.tcia')
    manifest_d = Path(r'd:\cancer\datasets\cbis_ddsm\manifest_part_D.tcia')

    expected_uids = set()
    for mf in [manifest_e, manifest_d]:
        if mf.exists():
            with open(mf) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('1.3.'):
                        expected_uids.add(line)

    found_uids   = set(merged.keys())
    missing_uids = expected_uids - found_uids
    extra_uids   = found_uids - expected_uids

    print(f"  Expected series (from manifests): {len(expected_uids):,}")
    print(f"  Found series                     : {len(found_uids):,}")
    print(f"  Missing series                   : {len(missing_uids):,}")
    if extra_uids:
        print(f"  Extra (annotation) series        : {len(extra_uids):,}")

    if missing_uids:
        missing_file = Path(r'd:\cancer\datasets\cbis_ddsm\missing_series.txt')
        with open(missing_file, 'w') as f:
            for uid in sorted(missing_uids):
                f.write(uid + '\n')
        print(f"  Missing UIDs written to: {missing_file}")

    # Save combined index CSV
    print("\n[4] Saving combined DICOM index...")
    with open(INDEX_OUT, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['series_uid', 'location', 'num_files', 'first_file'])
        for uid, info in sorted(merged.items()):
            writer.writerow([uid, info['location'], len(info['paths']), info['paths'][0]])
    print(f"  Index saved to: {INDEX_OUT}")

    # Summary
    print("\n" + "=" * 60)
    if len(missing_uids) == 0:
        print("RESULT: DOWNLOAD COMPLETE - All series present")
    else:
        pct = 100 * (1 - len(missing_uids)/len(expected_uids))
        print(f"RESULT: INCOMPLETE - {pct:.1f}% downloaded, {len(missing_uids):,} series missing")
        print("ACTION: Reload the split manifests in NBIA DR to resume")
    print("=" * 60)

if __name__ == '__main__':
    main()
