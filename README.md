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


Note :
- report berjalan tiap 2 jam, 01:00, 03:00 dan seterusnya

- report Zabbix dilakukan terlebih dahulu, jadi jika Zabbix reportnya tidak berjalan, maka kafka dan uptime tidak akan berjalan 

- jika ada perubahan yang ingin dilakukan, sampaikan ke pemilik, terima kasih