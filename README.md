Setelah di clone

1. ambil file .env untuk kredensial/konfigurasi

2. install library 
`pip install -r requirements.txt`

3. install browser Chromium yang dipakai playwright
`python -m playwright install`

4. jalankan bot
`py bot.py`

5. ada 3 cogs, Zabbix, uptime dan kafka, pastikan ter loaded Ketika bot dijalankan

6. Pastikan juga library yang diperlukan terpasang, uptime-kuma-api, playwright, matplotlib dll

7. bot hanya bekerja ketika VPN Global protect menyala, dan sudah tunneling ke 49 untuk Zabbix


Command by CLI :

1. Jalankan py bot.py dan tunggu hingga muncul pesan CLI aktif serta prompt bot>. Setelah prompt tersebut muncul, command dapat dijalankan melalui CLI bot.

2. Pada prompt bot>, ketik command help untuk mengetahui command tersedia, contoh command seperti cpu 36, server 36, atau reporting off tanpa awalan !. Jangan mengetik command bot langsung pada prompt Windows (C:\...>) karena prompt tersebut merupakan shell Windows, bukan CLI bot.

3. Command server <kode> digunakan untuk membuat grafik report server berdasarkan data 2 jam terakhir. Grafik akan langsung dikirim ke Discord melalui MAIN2_WEBHOOK_URL (inap-infra) dan tidak disimpan ke disk.

4. Laporan otomatis Zabbix, Kafka, dan Uptime Kuma dapat dikontrol melalui command reporting on, reporting off, atau reporting status pada CLI bot, maupun !reporting on, !reporting off, dan !reporting status melalui Discord.

Note :
- report berjalan tiap 2 jam, 01:00, 03:00 dan seterusnya

- report Zabbix dilakukan terlebih dahulu, jadi jika Zabbix reportnya tidak berjalan, maka kafka dan uptime tidak akan berjalan 

- jika ada perubahan yang ingin dilakukan, sampaikan ke pemilik, terima kasih