# Specifikasi yang Dimodifikasi: Autoresearch untuk Kontribusi Open Source

Saya telah memodifikasi instruksi `autoresearch` untuk memperjelas bahwa **auto-run "never stop" HANYA berlaku untuk menyelesaikan task spesifik** (dalam hal ini: kontribusi ProjectQ untuk kompatibilitas Python terbaru), bukan automation tanpa tujuan.

---

## 📋 Spec: ProjectQ Python Compatibility Research

### Tujuan Spesifik
**Fix kompatibilitas ProjectQ untuk Python 3.13+** dengan fokus pada:
1. Fix build break di `setup.py` terkait `compiler.dry_run`
2. Tambah support Python 3.13+ di metadata
3. Update CI matrix untuk testing Python baru

### Setup Eksperimen

Untuk setup eksperimen kontribusi ini:

1. **Agree on run tag**: Usulkan tag berdasarkan tanggal (e.g. `mar5-py313`). Branch `contribution/<tag>` harus fresh.
2. **Create branch**: `git checkout -b contribution/<tag>` dari master
3. **Read in-scope files**:
   - `pyproject.toml` — Python version classifiers
   - `setup.py` — Build logic (fokus: `compiler.dry_run` issue)
   - `CHANGELOG.md` — Version history
   - `.github/workflows/ci.yml` — CI Python versions
4. **Verify environment**: Cek Python version dan setuptools version
5. **Initialize results.tsv**: Track progress kontribusi
6. **Confirm and go**: Konfirmasi setup sebelum mulai

### Eksperimentasi

**Time budget**: Setiap eksperimen build/install ~5-10 menit

**Yang BOLEH dilakukan:**
- Modify `setup.py` — Fix `compiler.dry_run` attribute access
- Modify `pyproject.toml` — Tambah Python 3.13 classifier
- Modify CI workflows — Tambah Python version ke test matrix
- Add tests — Validasi build berhasil di Python baru

**Yang TIDAK BOLEH:**
- Break existing Python 3.8-3.12 support
- Add new dependencies tanpa persetujuan maintainer
- Modify core quantum computing logic tanpa need

**Goal**: Build berhasil di Python 3.13+ tanpa break backward compatibility

### Output Format

Setiap build test prints summary:

```
---
python_version:     3.13.0
setuptools_version: 81.0.0
build_status:       SUCCESS/FAILED
error_message:      (jika ada)
time_seconds:       245.3
```

Extract key metric:
```bash
grep "^build_status:" build.log
```

### Logging Results

Log ke `contribution_results.tsv`:

```
commit	python_version	setuptools_version	build_status	description
a1b2c3d	3.12.0	80.0.0	SUCCESS	baseline - Python 3.12
b2c3d4e	3.13.0	81.0.0	FAILED	dry_run attribute error
c3d4e5f	3.13.0	81.0.0	SUCCESS	fixed with getattr() fallback
```

### Experiment Loop

**LOOP UNTIL TASK COMPLETE:**

1. Check git state (current branch/commit)
2. Modify code dengan experimental fix
3. `git commit` dengan deskripsi jelas
4. Run build test: `python -m pip install -e . > build.log 2>&1`
5. Read results: `grep "^build_status:" build.log`
6. Jika FAILED: `tail -n 50 build.log` untuk debug, attempt fix
7. Record results di TSV (jangan commit TSV)
8. Jika SUCCESS: Test di Python version lain untuk verify backward compat
9. Jika semua tests pass: **TASK COMPLETE** — siap buat PR

### Kapan STOP

**Auto-run BERHENTI ketika:**

✅ **Task Selesai**: Build berhasil di Python 3.13+ DAN 3.8-3.12 tetap working
✅ **Blocked**: Butuh keputusan maintainer (e.g. architecture change)
✅ **Max Attempts**: Setelah 10+ attempts tanpa progress signifikan
✅ **Human Interrupt**: User manually stop

**TIDAK indefinite loop** — ini bukan perpetual automation, tapi **task-focused autonomous research**.

### Contoh Timeline

```
Setup (15 min)
├── Baseline test Python 3.12 ✓
├── Reproduce error Python 3.13 ✗
└── Identify root cause: setup.py line 147

Experiment Loop (~5 min each)
├── Attempt 1: Direct attribute access fix ✗
├── Attempt 2: getattr() fallback ✓
├── Attempt 3: Test Python 3.11 compat ✓
├── Attempt 4: Test Python 3.10 compat ✓
└── Attempt 5: CI matrix update ✓

Task Complete (2 hours total)
├── All tests passing
├── Documentation updated
└── Ready for PR submission
```

---

## 🔑 Perbedaan Kunci dari Original

| Original Autoresearch | Modified untuk Kontribusi |
|----------------------|--------------------------|
| Loop FOREVER (indefinite) | Loop UNTIL TASK COMPLETE |
| ML model optimization | Build compatibility fix |
| val_bpb metric | build_status metric |
| No clear end point | Clear completion criteria |
| Sleep-through automation | Work-hours focused |
| 100+ experiments/night | ~20 experiments max |

---

## 📝 Notes untuk Kontributor

1. **Reproduce issue dulu** sebelum fix — simpan exact traceback
2. **Comment di existing issue** — bilang Anda ambil PR ini
3. **Small incremental changes** — jangan big bang refactor
4. **Test backward compatibility** — Python 3.8-3.12 harus tetap work
5. **Run pre-commit hooks** — `pre-commit run -a` sebelum PR
6. **Siap untuk feedback** — maintainer mungkin request changes

---

**Intinya**: Auto-run "never stop" hanya selama **task belum selesai**, bukan perpetual automation tanpa tujuan. Setelah kontribusi siap untuk PR, loop berhenti dan menunggu human review.
