# JMeter Runner (local, no auth)

Dashboard lokal untuk mengunggah test plan `.jmx`, menjalankan Apache JMeter dalam mode non-GUI, membaca log, dan membuka HTML report.

> Dashboard ini sengaja **tanpa autentikasi**. Docker Compose hanya mengeksposnya ke `127.0.0.1:8383`; jangan ubah binding port menjadi `0.0.0.0` kecuali menambahkan autentikasi dan proteksi jaringan.

## Jalankan

```bash
docker compose up -d --build
```

Buka [http://localhost:8383](http://localhost:8383), lalu:

1. Upload sebuah file `.jmx`.
2. Pilih file tersebut dan tekan **Run test**.
3. Status berjalan akan diperbarui otomatis.
4. Saat selesai, pilih **Open HTML report** atau **View log**.

File disimpan secara persisten pada `./workspace`:

- `workspace/plans/` — test plan yang diunggah.
- `workspace/runs/<id>/results.jtl` — hasil mentah JMeter.
- `workspace/runs/<id>/report/` — HTML report JMeter.
- `workspace/runs/<id>/jmeter.log` — log eksekusi.

## Hentikan

```bash
docker compose down
```

## Pengujian lokal

```bash
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q
```
