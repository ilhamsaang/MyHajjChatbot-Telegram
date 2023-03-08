import pipeline_qg

qg = pipeline_qg.pipeline()

print(
    qg("""
        Untuk mendapatkan bekal mental dan fisik yang cukup, sebelum berangkat ke tanah suci setiap jemaah haji
        dianjurkan untuk: yang pertama adalah memperbanyak istighfar, dzikir dan doa
        untuk bertaubat kepada Allah SWT dan memohon bimbingan dariNya, kemudian yang kedua yaitu 
        menyelesaikan semua masalah yang berkenaan dengan tanggung jawab pada keluarga, pekerjaan dan 
        utang-piutang, lalu yang ketiga menyambung silaturahim dengan sanak keluarga, kawan, dan masyarakat
        dengan memohon maaf dan doa restu, yang keempat adalah membiasakan pola hidup sehat agar
        mudah melakukan ibadah haji dan umrah, lalu yang terakhir adalah mempelajari manasik atau
        tata cara ibadah haji dan umrah sesuai ketentuan hukum Islam.
        """)
)
