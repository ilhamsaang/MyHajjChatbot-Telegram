import logging
import os
import sqlite3
import geocoder
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import socket
import shutil
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

# State untuk ConversationHandler
TEMPAT, LATITUDE, LONGITUDE, EDIT_DATA, EDIT_TEMPAT, EDIT_LATITUDE, EDIT_LONGITUDE = range(7)

# Inisialisasi objek logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
bot_token = os.getenv('BOT_TOKEN_ADMIN')
if not os.path.exists('cari_tempat&keperluan.db'):
    # Jika belum ada, maka membuat koneksi ke database dan tabel
    conn = sqlite3.connect('cari_tempat&keperluan.db')
    cursor = conn.cursor()

    # Membuat tabel "Host"
    cursor.execute('''
        CREATE TABLE Host (
            id_host INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            hostusername VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    ''')

    # Membuat tabel "admin"
    cursor.execute('''
        CREATE TABLE admin (
            id_admin INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    ''')

    # Membuat tabel "fuzzy"
    cursor.execute('''
        CREATE TABLE fuzzy (
            id_fuzzy INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            tempat TEXT NOT NULL,
            latitude INTEGER NOT NULL,
            longitude INTEGER NOT NULL,
            like INTEGER NOT NULL,
            dislike INTEGER NOT NULL,
            last_like TEXT,
            last_dislike TEXT
        );
    ''')

    # Commit perubahan dan tutup koneksi
    conn.commit()
    conn.close()

    print("Basis data dan tabel berhasil dibuat!")
else:
    print("Basis data sudah ada. Tidak perlu membuat lagi.")
database_file = 'cari_tempat&keperluan.db'
DELETE_ADMIN = range(1)
# Fungsi untuk membuat backup database
def create_backup(update, context):
    if 'host' in context.user_data:
        backup_file = 'cari_tempat&keperluan_backup.db'
        shutil.copy2(database_file, backup_file)
        update.message.reply_text("Backup berhasil.")
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

# Fungsi untuk melakukan recovery database
def perform_recovery(update, context):
    if 'host' in context.user_data:
        recovery_file = 'cari_tempat&keperluan_recovery.db'
        database_file = 'cari_tempat&keperluan.db'
        backup_file = 'cari_tempat&keperluan_backup.db'

        # Copy file backup ke file recovery
        shutil.copy2(backup_file, recovery_file)

        conn_recovery = sqlite3.connect(recovery_file)
        cursor_recovery = conn_recovery.cursor()

        conn_database = sqlite3.connect(database_file)
        cursor_database = conn_database.cursor()

        try:
            # Dapatkan daftar tabel dalam file backup
            cursor_recovery.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor_recovery.fetchall()

            # Mulai pemulihan tabel satu per satu
            for table in tables:
                table_name = table[0]

                # Dapatkan data dari file recovery
                cursor_recovery.execute(f"SELECT * FROM {table_name};")
                data_recovery = cursor_recovery.fetchall()

                # Bersihkan data pada tabel utama sebelum melakukan pemulihan
                cursor_database.execute(f"DELETE FROM {table_name};")
                conn_database.commit()

                # Masukkan data dari file recovery ke tabel utama
                for row in data_recovery:
                    placeholders = ', '.join(['?' for _ in range(len(row))])
                    cursor_database.execute(f"INSERT INTO {table_name} VALUES ({placeholders});", row)
                    conn_database.commit()

            conn_recovery.close()
            conn_database.close()

            update.message.reply_text("Pemulihan menggunakan data dari backup berhasil.")
        except sqlite3.Error as e:
            # Jika terjadi kesalahan saat pemulihan, batalkan perubahan pada file recovery dan database utama
            conn_recovery.rollback()
            conn_database.rollback()
            conn_recovery.close()
            conn_database.close()
            update.message.reply_text("Terjadi kesalahan saat melakukan pemulihan: {}".format(str(e)))
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

# Fungsi untuk memulai bot dan menampilkan tombol keyboard
def start(update, context):
    Jalan = "📍"
    button_tambah_data = KeyboardButton('Tambah Data', resize_keyboard=True, one_time_keyboard=True)
    button_edit_data = KeyboardButton('Edit Data', resize_keyboard=True, one_time_keyboard=True)
    button_help = KeyboardButton('Help', resize_keyboard=True, one_time_keyboard=True)
    button_helphost = KeyboardButton('Bantuan host', resize_keyboard=True, one_time_keyboard=True)
    button_display_admin = KeyboardButton('Display admin', resize_keyboard=True, one_time_keyboard=True)
    button_logout = KeyboardButton('Logout',resize_keyboard=True, one_time_keyboard=True)
    button_logout_host = KeyboardButton('Keluar host', resize_keyboard=True, one_time_keyboard=True)
    button_cancel = KeyboardButton('/cancel', resize_keyboard=True, one_time_keyboard=True)
    if 'username' in context.user_data:
        reply_markup = ReplyKeyboardMarkup([[button_tambah_data, button_edit_data, button_cancel], [button_help, button_logout], [KeyboardButton(Jalan + " Nama Jalan", resize_keyboard=True, one_time_keyboard=True)]], resize_keyboard=True)
    elif 'host' in context.user_data:
        reply_markup = ReplyKeyboardMarkup([[button_tambah_data, button_edit_data, button_cancel], [button_display_admin, button_helphost, button_logout_host], [KeyboardButton(Jalan + " Nama Jalan", resize_keyboard=True, one_time_keyboard=True)]], resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardMarkup([[button_help], [KeyboardButton(Jalan + " Nama Jalan", resize_keyboard=True, one_time_keyboard=True)]], resize_keyboard=True)
    update.message.reply_text('Silakan pilih aksi:', reply_markup=reply_markup)

# Fungsi untuk memulai proses penambahan data
def start_tambah_data(update, context):
    if 'username'in context.user_data or 'host' in context.user_data:
        update.message.reply_text("Masukkan nama tempat:")
        return TEMPAT
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

# Fungsi untuk menerima input nama tempat
def input_tempat(update, context):
    context.user_data['tempat'] = update.message.text
    update.message.reply_text("Masukkan latitude:")
    return LATITUDE

# Fungsi untuk menerima input latitude
def input_latitude(update, context):
    try:
        context.user_data['latitude'] = float(update.message.text)
        update.message.reply_text("Masukkan longitude:")
        return LONGITUDE
    except ValueError:
        update.message.reply_text("Masukkan angka untuk latitude. Contoh: -6.12345")
        return LATITUDE

# Fungsi untuk menerima input longitude dan menyimpan data ke tabel fuzzy
def input_longitude(update, context):
    try:
        context.user_data['longitude'] = float(update.message.text)

        # Menyimpan data ke database SQLite
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO fuzzy (tempat, latitude, longitude, `like`, `dislike`) VALUES (?, ?, ?, ?, ?)",
                       (context.user_data['tempat'], context.user_data['latitude'],
                        context.user_data['longitude'], 0, 0))
        conn.commit()
        conn.close()

        update.message.reply_text('Data berhasil ditambahkan!')
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Masukkan angka untuk longitude. Contoh: 106.78901")
        return LONGITUDE

# Fungsi untuk menampilkan pesan bantuan
def help_command(update, context):
    help_text = "Bot Commands:\n" \
                "/login - Login dengan username dan password contohnya kirim pesan /login username password \n" \
                "/logout - Keluar dari akun"
    update.message.reply_text(help_text)

def help_host_command(update, context):
    helphost_text = "Bot Commands:\n" \
                "/login - Login dengan username dan password contohnya kirim pesan /login username password\n" \
                "/register - Mendaftar akun admin baru contohnya kirim pesan /register username password\n" \
                "/display_data - menampilkan id dan username admin\n" \
                "/delete_admin - menghapus akun admin contohnya kirim pesan /delete_admin id\n" \
                "/backup - menyalin database\n" \
                "/recovery - mengubah database menggunakan data backup\n" \
                "/logout - Keluar dari akun"
    update.message.reply_text(helphost_text)

# Fungsi untuk melakukan login
def login(update, context):
    # Mengambil input dari pengguna
    username = update.message.text.split()[1]
    password = update.message.text.split()[2]

    # Menghubungkan ke database SQLite
    conn = sqlite3.connect('cari_tempat&keperluan.db')
    cursor = conn.cursor()

    # Mengecek apakah username dan password ada dalam tabel admin
    cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    if result:
        # Jika login berhasil, simpan informasi login ke dalam user_data
        context.user_data['username'] = username
        update.message.reply_text("Login berhasil!")
    else:
        update.message.reply_text("Login gagal!")

    # Menutup koneksi ke database SQLite
    conn.close()

    # Memanggil kembali fungsi start untuk memperbarui tampilan tombol
    start(update, context)

def loginhost(update, context):
        # Mengambil input dari pengguna
        host = update.message.text.split()[1]
        password = update.message.text.split()[2]

        # Menghubungkan ke database SQLite
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()

        # Mengecek apakah username dan password ada dalam tabel host
        cursor.execute("SELECT * FROM Host WHERE hostusername = ? AND password = ?", (host, password))
        result = cursor.fetchone()

        if result:
            # Jika login berhasil, simpan informasi login ke dalam user_data
            context.user_data['host'] = host
            update.message.reply_text("Login Host berhasil!")
        else:
            update.message.reply_text("Login Host gagal!")

        # Menutup koneksi ke database SQLite
        conn.close()

        # Memanggil kembali fungsi start untuk memperbarui tampilan tombol
        start(update, context)

# Fungsi untuk melakukan register
def register(update, context):
    if 'host' in context.user_data:
        # Mengambil input dari pengguna
        username = update.message.text.split()[1]
        password = update.message.text.split()[2]

        # Menghubungkan ke database SQLite
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()

        # Mengecek apakah username sudah terdaftar
        cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result:
            update.message.reply_text("Username sudah terdaftar!")
        else:
            # Jika username belum terdaftar, daftarkan pengguna baru ke dalam tabel admin
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            update.message.reply_text("Registrasi berhasil!")

        # Menutup koneksi ke database SQLite
        conn.close()

        # Memanggil kembali fungsi start untuk memperbarui tampilan tombol
        start(update, context)
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

def delete_admin(update, context):
    if 'host' in context.user_data:
        user_data = context.user_data

        # Dapatkan ID admin yang ingin dihapus dari pesan pengguna
        args = context.args
        if len(args) == 0:
            update.message.reply_text("Penggunaan: /delete_admin <ID>")
            return DELETE_ADMIN
        row_id = int(args[0])

        # Koneksi ke database SQLite (ganti 'nama_database.db' dengan nama database Anda)
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()

        # Hapus baris dengan ID yang diberikan dari tabel admin
        cursor.execute("DELETE FROM admin WHERE id_admin=?", (row_id,))

        # Commit perubahan dan tutup koneksi
        conn.commit()
        conn.close()

        update.message.reply_text(f"Admin dengan ID {row_id} berhasil dihapus.")
        return ConversationHandler.END
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Dibatalkan.")
    return ConversationHandler.END
def display_data(update, context):
    if 'host' in context.user_data:
        # Koneksi ke database SQLite (ganti 'nama_database.db' dengan nama database Anda)
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()

        # Lakukan kueri SELECT untuk mengambil data ID dan username dari tabel (ganti "nama_tabel" dengan nama tabel Anda)
        cursor.execute("SELECT id_admin, username FROM admin")

        # Ambil semua baris hasil kueri
        rows = cursor.fetchall()
        response = "Data admin:\n"
        # Tampilkan data ID dan username
        for row in rows:
            row_id, username = row
            response += f"ID: {row_id}, Username: {username}\n"

        # Tutup koneksi
        conn.close()
        update.message.reply_text(response)
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END
    # Fungsi untuk melakukan logout


def logout(update, context):
    if 'username' in context.user_data:
        # Menghapus informasi login dari user_data
        del context.user_data['username']
        update.message.reply_text("Logout berhasil!")
    else:
        update.message.reply_text("Anda belum login admin!")

    # Memanggil kembali fungsi start untuk memperbarui tampilan tombol
    start(update, context)

def logout_host(update, context):
        if 'host' in context.user_data:
            # Menghapus informasi login dari user_data
            del context.user_data['host']
            update.message.reply_text("Logout berhasil!")
        else:
            update.message.reply_text("Anda belum login host!")

        # Memanggil kembali fungsi start untuk memperbarui tampilan tombol
        start(update, context)


def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# Fungsi untuk mendapatkan lokasi berdasarkan alamat IP
def get_location_by_ip():
    g = geocoder.ip('me')
    return g.latlng

# Fungsi untuk mendapatkan lokasi berdasarkan GPS
def get_location_by_gps(lat, lon):
    return lat, lon

def mylocation_message(update, context):
    message = update.message
    chat_id = message.chat_id

    if message.text.lower() == 'dimana saya' or 'saya dimana' or 'lokasi saya' or 'posisi saya':
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = get_location_by_gps(latitude, longitude)

            if location:
                # Kirim lokasi ke pengguna
                context.bot.send_location(chat_id=chat_id, latitude=location[0], longitude=location[1])
                context.bot.send_message(chat_id=chat_id, text="Lokasi Anda ditemukan menggunakan GPS.")
            else:
                # Tangani jika tidak dapat mendapatkan lokasi
                context.bot.send_message(chat_id=chat_id, text="Maaf, tidak dapat menemukan lokasi saat ini.")

        else:
            location = get_location_by_ip()

            if location:
                # Kirim lokasi ke pengguna
                context.bot.send_location(chat_id=chat_id, latitude=location[0], longitude=location[1])
                context.bot.send_message(chat_id=chat_id, text="Lokasi Anda ditemukan menggunakan IP. Lokasi yang diperoleh menggunakan alamat IP tidak selalu akurat. Metode untuk mendapatkan lokasi berdasarkan IP dapat memberikan perkiraan yang kasar, terutama ketika menggunakan layanan gratis atau terbatas seperti WiFi")
            else:
                # Tangani jika tidak dapat mendapatkan lokasi
                context.bot.send_message(chat_id=chat_id, text="Maaf, tidak dapat menemukan lokasi saat ini.")

def get_location(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text='Silakan kirim lokasi Anda.', request_location=True)
    context.bot.send_location(chat_id=chat_id, request_location=True)

# Fungsi untuk menangani pesan lokasi yang diterima
def location_received(update, context):
    location = update.message.location
    chat_id = update.effective_chat.id
    geolocator = Nominatim(user_agent="myGeocoder")
    address = geolocator.reverse([location.latitude, location.longitude])
    context.bot.send_message(chat_id=chat_id, text=(str(address), location.latitude, location.longitude))

def start_edit_data(update, context):
    if 'username' in context.user_data or 'host' in context.user_data:
        update.message.reply_text("Masukkan ID data yang ingin Anda edit:")
        return EDIT_DATA
    else:
        update.message.reply_text("Anda belum login. Silakan login terlebih dahulu.")
        return ConversationHandler.END

# Fungsi untuk menerima input ID data yang ingin diedit
def input_edit_data(update, context):
    try:
        edit_id = int(update.message.text)
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fuzzy WHERE id_fuzzy = ?", (edit_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            context.user_data['edit_id'] = edit_id
            update.message.reply_text(f"Data yang akan diedit:\n"
                                      f"ID: {result[0]}\n"
                                      f"Tempat: {result[1]}\n"
                                      f"Latitude: {result[2]}\n"
                                      f"Longitude: {result[3]}")
            update.message.reply_text("Masukkan nama tempat baru:")
            return EDIT_TEMPAT
        else:
            update.message.reply_text("Data dengan ID tersebut tidak ditemukan.")
            return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Masukkan angka untuk ID data yang ingin Anda edit.")
        return EDIT_DATA

# Fungsi untuk menerima input nama tempat yang ingin diedit
def input_edit_tempat(update, context):
    context.user_data['tempat'] = update.message.text
    update.message.reply_text("Masukkan latitude baru:")
    return EDIT_LATITUDE

# Fungsi untuk menerima input latitude yang ingin diedit
def input_edit_latitude(update, context):
    try:
        context.user_data['latitude'] = float(update.message.text)
        update.message.reply_text("Masukkan longitude baru:")
        return EDIT_LONGITUDE
    except ValueError:
        update.message.reply_text("Masukkan angka untuk latitude. Contoh: -6.12345")
        return EDIT_LATITUDE

# Fungsi untuk menerima input longitude yang ingin diedit dan menyimpan perubahan ke dalam database
def input_edit_longitude(update, context):
    try:
        context.user_data['longitude'] = float(update.message.text)

        # Mengupdate data di database SQLite
        conn = sqlite3.connect('cari_tempat&keperluan.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE fuzzy SET tempat = ?, latitude = ?, longitude = ? WHERE id_fuzzy = ?",
                       (context.user_data['tempat'], context.user_data['latitude'],
                        context.user_data['longitude'], context.user_data['edit_id']))
        conn.commit()
        conn.close()

        update.message.reply_text('Data berhasil diupdate!')
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Masukkan angka untuk longitude. Contoh: 106.78901")
        return EDIT_LONGITUDE

def main():
    # Inisialisasi updater dan dispatcher
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Tambahkan handler untuk perintah /start
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # Tambahkan handler untuk perintah /tambah_data
    tambah_data_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Tambah Data$'), start_tambah_data)],
        states={
            TEMPAT: [MessageHandler(Filters.text, input_tempat)],
            LATITUDE: [MessageHandler(Filters.text, input_latitude)],
            LONGITUDE: [MessageHandler(Filters.text, input_longitude)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(Filters.regex('^Batal'), cancel)],
    )
    dispatcher.add_handler(tambah_data_handler)

    # Tambahkan handler untuk perintah /edit_data
    edit_data_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Edit Data$'), start_edit_data)],
        states={
            EDIT_DATA: [MessageHandler(Filters.text, input_edit_data)],
            EDIT_TEMPAT: [MessageHandler(Filters.text, input_edit_tempat)],
            EDIT_LATITUDE: [MessageHandler(Filters.text, input_edit_latitude)],
            EDIT_LONGITUDE: [MessageHandler(Filters.text, input_edit_longitude)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(Filters.regex('^Batal'), cancel)],
    )
    dispatcher.add_handler(edit_data_handler)
    delete_admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_admin", delete_admin)],
        states={
            DELETE_ADMIN: [MessageHandler(Filters.text & ~Filters.command, delete_admin)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(Filters.regex('^Batal'), cancel)],
    )
    dispatcher.add_handler(delete_admin_conv_handler)
    # Tambahkan handler untuk perintah /login
    dispatcher.add_handler(CommandHandler('login', login))
    dispatcher.add_handler(CommandHandler('loginhost', loginhost))
    dispatcher.add_handler(CommandHandler('register', register))

    dispatcher.add_handler(CommandHandler('logout', logout))
    dispatcher.add_handler(CommandHandler('keluarhost', logout_host))

    dispatcher.add_handler(MessageHandler(Filters.regex('^📍 Nama Jalan$'), get_location))
    dispatcher.add_handler(CommandHandler('location', get_location))
    dispatcher.add_handler(MessageHandler(Filters.location, location_received))

    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Help'), help_command))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Batal'), cancel))
    dispatcher.add_handler(CommandHandler('Bantuanhost', help_host_command))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Bantuan host'), help_host_command))
    dispatcher.add_handler(CommandHandler('Displayadmin', display_data))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Display admin'), display_data))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Logout'), logout))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Keluar host'), logout_host))
    dispatcher.add_handler(CommandHandler('backup', create_backup))
    dispatcher.add_handler(CommandHandler('recovery', perform_recovery))

    # Jalankan bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
