
import re
import logging
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, PicklePersistence
from pipeline_qa import TaskPipeline
from fuzzywuzzy import fuzz
import nltk

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')



qa_pipeline = TaskPipeline()

doa_contexts = {
    "bacaan niat umrah":
        """
        <lafadz>نَوَيْتُ العُمْرَةَ وَأَحْرَمْتُ بِهَا لِلهِ تَعَالَى, Nawaitul 'umrata wa ahramtu bihi lillahi ta'ala</lafadz>, <terjemahan>saya berniat melaksanakan ibadah umrah karena Allah Ta’ala</terjemahan>, <audio>Niat umrah dan Ihram.mp3</audio>. 
        """,
    "bacaan niat umrah secara singkat":
        """
        <lafadz>لَبَّيْكَ اللَّهُمَّ بعُمْرَة, Labbaika allahumma umrah</lafadz>, <terjemahan>Saya memenuhi panggilanMu Ya Allah dengan berumrah</terjemahan>, <audio></audio>. 
        """,
    "bacaan talbiyah":
        """
        <lafadz>لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ، لَبَّيْكَ لاَ شَرِيْكَ لَكَ لَبَّيْكَ، إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ لاَ شَرِيْكَ لَكَ, Labbaika allahumma labbaika labbaika la sharika laka labbaika innal hamda wan-ni’mata laka wal-mulk laa syariikalaka</lafadz>, 
        <terjemahan>Aku datang memenuhi panggilan-Mu ya Allah, aku datang Aku penuhi panggilan-Mu ya Allah, tiada sekutu bagi-Mu, aku penuhi panggilan-Mu, Sesungguhnya segala puji, nikmat dan kerajaan hanyalah kepunyaan-Mu, tiada sekutu bagi-Mu</terjemahan>, <audio></audio>.
        """,
    "bacaan shalawat kepada Nabi Muhammad SAW":
        """
        <lafadz>اللّٰهُمَّ صَلِّ وَسَلِّمْ عَلٰى سَيِّدِنَا مُحَمَّدٍ وَعَلٰى اٰلِ سَيِّدِنَا مُحَمَّد, Allahumma shalli wa sallim ‘alaa sayyidina Muhammadin wa ‘alaa aali sayyidina Muhammadin</lafadz>, 
        <terjemahan>Ya Allah limpahkanlah rahmat dan salam kepada Nabi Muhammad SAW dan keluarganya</terjemahan>, <audio></audio>.
        """,
    "bacaan doa penutup sholawat atau sesudah shalawat Nabi":
        """

        """,
    "bacaan doa penutup sholawat atau sesudah shalawat Nabi secara singkat":
        """
        <lafadz>اللّٰهُمَّ إِنَّا نَسْأَلُكَ رِضَاكَ وَالْجَنَّةَ وَ نَعُوْذُبِكَ مِنْ سَخَطِكَ وَالنَّارِ. رَبَّنَا اٰتِنَا فِى الدُّنْيَا حَسَنَةً وَفِى اْلٰاخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ, Allahumma inna nas aluka ridhaaka wal jannata wa na’uudzubika min sakhaatika wannaar. Rabbanaa aatinaa fiddunyaa hasanataw wa fil aakhirati hasanataw waqinaa adzaabannaar</lafadz>, 
        <terjemahan>Ya Allah, sesungguhnya kami memohon keridhaan-Mu dan surga, kami berlindung kepadaMu dari kemurkaan-Mu dan siksa neraka. Wahai tuhan kami berikanlah kami kebaikan di dunia dan kebaikan di akhirat, dan hindarkan kami dari siksa api neraka</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat dhuhur qashar jama’ taqdim":
        """
        <lafadz>أُصَلِّى فَرْضَ الْظُهْرِ رَكْعَتَيْنِ مَجْمُوْعًا بِالْعَصْرِ جَمْعَ تَقْدِيْمٍ قَصْرًا ِللهِ تَعَالَى, Ushallii fardol dhuhri rak ataini majmuu an bilashri jam a taqdiimin qashran lillahi ta ala</lafadz>, 
        <terjemahan>Sengaja aku shalat dhuhur empat raka’at menghadap kiblat, dijamak takdim qashar dengan ‘ashar karena Allah Ta’ala</terjemahan>, <audio></audio>. 
        """,
    "bacaan niat sholat ashar qashar jama' taqdim":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الظُّهْرِ رَكَعَتَيْنِ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْعَصْرِ جَمْعَ تَقْدِيْمٍ قَصْرَا للهِ تَعَالَى, Ushallii fardol ashri rak ataini majmuu an bidhuhri jam a taqdiimin qashran lillahi ta ala</lafadz>, 
        <terjemahan>Saya niat shalat fardhu ashar dua rakaat di-jama’ taqdîm dengan dhuhur sambil diqashar karena Allah Ta’ala</terjemahan>, <audio></audio>
        """,
    "bacaan niat sholat maghrib qashar jama' taqdim":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعِشَاءِ رَكَعَتَيْنِ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْمَغْرِبِ جَمْعَ تَقْدِيْمٍ قَصْرَا للهِ تَعَالَى, Ushallii fardhal isyaai rakataini qasran majmuuan illa maghribi lillaahi ta ala</lafadz>, 
        <terjemahan>Sengaja aku shalat isya empat rakaat menghadap kiblat, dijamak takdim qashar dengan maghrib karena Allah Ta’ala</terjemahan>, <audio></audio>
        """,
    "bacaan niat shalat dhuhur qashar jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الظُّهْرِ رَكَعَتَيْنِ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْعَصْرِ جَمْعَ تَأْخِيْرٍ قَصْرَا للهِ تَعَالَى, Usalli fardaz zuhri rakataini mustaqbilal qiblati majmuan bil aṣri jam a ta khirin qasran lillahi ta ala</lafadz>, 
        <terjemahan>Sengaja aku shalat zhuhur empat raka’at menghadap kiblat, dijamak takhir qashar dengan ashar karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat ashar qashar jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعَصْرِ رَكَعَتَيْنِ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالظُّهْرِ جَمْعَ تَأْخِيْرٍ قَصْرَا للهِ تَعَالَى, Usalli farda al asri rakataini mustaqbilal qiblati majmu an bid duhri jam a ta khirin qasran lillahi ta ala</lafadz>, 
        <terjemahan>Sengaja aku shalat ashar empat raka’at menghadap kiblat, dijamak takhir qashar dengan zhuhur karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat maghrib qashar jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعِشَاءِ رَكَعَتَيْنِ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْمَغْرِبِ جَمْعَ تَأْخِيْرٍ قَصْرَا للهِ تَعَالَى, Usalli farda al ishai rakataini mustaqbilal qiblati majmu an bil maghribi jam a ta khirin qasran lillahi ta ala</lafadz>,
        <terjemahan>Sengaja aku shalat ‘isya empat raka’at menghadap kiblat, dijamak takhir qashar dengan maghrib karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat dhuhur jama' taqdim":
        """
        <lafadz>أُصَلِّي فَرْضَ الظُّهْرِأربع رَكعَاتٍ مَجْمُوْعًا مع العَصْرِ اَدَاءً للهِ تَعَالى, Usalli farda az zuhri arba a rak atin mustaqbilal qiblati majmu an bil  asri jam a taqdimin lillahi ta ala</lafadz>, 
        <terjemahan>Sengaja aku shalat zhuhur empat raka’at menghadap kiblat, dijamak takdim dengan ‘ashar karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat ashar jama' taqdim":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعَصْرِ أَرْبَعَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالظُّهْرِ جَمْعَ تَقْدِيْمٍ للهِ تَعَالَى, Usalli farda al asri arba a rak atin mustaqbilal qiblati majmu an bid duhri jam a taqdimin lillahi ta ala</lafadz>,
        <terjemahan>Sengaja aku shalat ‘ashar empat raka’at menghadap kiblat, dijamak takdim dengan zhuhur karena Allah Ta’ala</terjemahan>.
        """,
    "bacaan niat shalat maghrib jama' taqdim":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْمَغْرِبِ ثَلاَثَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْعِشَاءِ جَمْعَ تَقْدِيْمٍ للهِ تَعَالَى, Usalli farda al maghribi shalasha rak atin mustaqbilal qiblati majmu an bil isha i jam a taqdimin lillahi ta ala.</lafadz>,
        <terjemahan>Sengaja aku shalat maghrib tiga raka’at menghadap kiblat, dijamak takdim dengan ‘Isya karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat isya' jama' taqdim":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعِشَاءِ ثَلاَثَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْمَغْرِبِ جَمْعَ تَقْدِيْمٍ للهِ تَعَالَى, Usalli farda al isha i arba a rak atin mustaqbilal qiblati majmu an bil maghribi jam a taqdimin lillahi ta ala</lafadz>,
        <terjemahan>Sengaja aku shalat ‘Isya empat raka’at menghadap kiblat, dijamak takdim dengan maghrib karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat dhuhur jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الظُّهْرِ أَرْبَعَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْعَصْرِ جَمْعَ تَأْخِيْرٍ للهِ تَعَالَى, Usalli farda az zuhri arba a rak atin mustaqbilal qiblati majmu an bil asri jam a ta khirin lillahi ta ala</lafadz>,
        <terjemahan>Sengaja aku shalat zhuhur empat raka’at menghadap kiblat, dijamak Ta'khir dengan Ashar karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat ashar jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْعَصْرِ أَرْبَعَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالظُّهْرِ جَمْعَ تَأْخِيْرٍ للهِ تَعَالَى, Usalli farda al asri arba a rak atin mustaqbilal qiblati majmu an bid duhri jam a ta khirin lillahi ta ala</lafadz>,
        <terjemahan>Sengaja aku shalat ‘ashar empat raka’at menghadap kiblat, dijamak Ta'khir dengan zhuhur karena Allah Ta’ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat maghrib jama' takhir":
        """
        <lafadz>أُصَلِّيْ فَرْضَ الْمَغْرِبِ ثَلاَثَ رَكَعَاتٍ مُسْتَقْبِلَ الْقِبْلَةِ مَجْمُوْعًا بِالْعِشَاءِ جَمْعَ تَأْخِيْرٍ للهِ تَعَالَى, Usalli farda al maghribi shalasha rakatin mustaqbilal qiblati majmu an bil isha i jam a ta khirin lillahi ta ala</lafadz>,
        <terjemahan>Aku sengaja salat fardu maghrib 3 rakaat yang dijama' dengan isyak, dengan jamak takhir, fardu karena Allah Ta'aala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat isya' jama' takhir":
        """
        <lafadz>اُصَلّى فَرْضَ العِسَاءِ اَرْبَعَ رَكَعَاتٍ جَمْعًا تَأخِيْرًا مَعَ المَغْرِبِ فَرْضًا للهِ تََعَالَى, Ushollii fardlul isyaa i arba a raka aatin majmuu an ma al magribi Jam a ta khiirinin adaa an lillaahi ta aalaa</lafadz>,
        <terjemahan>Aku berniat salat isya' empat rakaat yang dijama' dengan magrib, dengan jamak takhir, fardhu karena Allah Ta'aala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat jenazah untuk laki-laki":
        """
        <lafadz>أُصَلَّى على هَذَا المَيِّتِ أَرْبَعَ تَكبِيرَاتٍ فَرضَ كِفَايَةِ إِمَامًا  مَأْمُومَا رَكْعَتَيْنِ اللَّهِ تَعَالَى اللَّهُ أَكْبَرُ, Ushalli ala hadzal mayyiti arba a takbiratin fardhu kifayati (imaman/ma muman) lillahi Ta ala</lafadz>,
        <terjemahan>Saya berniat sholat untuk mayat ini empat takbir karena menjalankan fardhu kifayah sebagai (imam/makmum) karena Allah Ta'ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat jenazah untuk perempuan":
        """
        <lafadz>أَصَلِّي على هَذِهِ المَيْتَةِ أَرْبَعَ تَكبِيرَاتٍ فَرضَ كِفَايَةِ إِمَامًا مَأْمُوماً رَكْعَتَيْنِ اللَّهِ تَعَالَى اللَّهُ أَكْبَرُ, Ushalli ala hadzihil mayyitati arba a takbiratin fardhu kifayati (imaman/ma muman) lillahi Taaala</lafadz>,
        <terjemahan>Saya berniat sholat untuk mayat ini empat takbir karena menjalankan fardhu kifayah sebagai (imam/makmum) karena Allah Ta'ala. Allah Mahabesar</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat jenazah untuk anak laki-laki":
        """
        <lafadz>بِسْمِ اللهِ الرَّحْمَنِ الرَّحِيْمِ  أُصَلِّيْ عَلَى هَذَا المَيِّتِ الطِّفْلِ أَرْبَعَ تَكْبِيْرَاتٍ فَرْضَ الْكِفَايَةِ إِمَامًا مَأْمُوْمًا لِلّٰهِ تَعَالَى اللهُ أَكْبَرُ, Usholli ala hadzihil mayyiti thifli arba a takbiratin fardhol kifayatai imaman/ma muman lillahi ta ala</lafadz>,
        <terjemahan>Saya niat sholat atas jenazah ini empat kali takbir fardu kifayah, sebagai imam/makmum hanya karena Allah Ta'ala</terjemahan>, <audio></audio>.
        """,
    "bacaan niat shalat jenazah untuk anak perempuan":
        """
        <lafadz>اُصَلِّى عَلَى هَذِهِ الْمَيِّتَةِ اَبَعَ تَكْبِرَاتٍ َرْضَ كِفَايَةِ اِمَامًا مَأْمُوْمًا ِللهِ تَعَالَى, Usholli alaa hadzihil mayyitati thifli arba a takbiratatin fardhol kifayatai imaman/ma muman lillahi ta ala</lafadz>,
        <terjemahan>Saya niat sholat atas jenazah anak perempuan ini empat kali takbir fardu kifayah, sebagai imam makmum hanya karena Allah Ta'ala</terjemahan>, <audio></audio>.
        """,
    "bacaan doa shalat jenazah untuk laki-laki takbir ketiga singkat":
        """
        <lafadz>اَللهُمَّ اغْفِرْلَهُ وَارْحَمْهُ وَعَافِهِ وَاعْفُ عَنْهُ, Allahhummaghfir lahu warhamhu wa aafihi wa fuanhu</lafadz>,
        <terjemahan>Ya Allah ampunilah dia, berilah rahmat dan sejahtera dan maafkanlah dia</terjemahan>, <audio></audio>
        """,
    "bacaan doa shalat jenazah untuk perempuan takbir ketiga atau ke 3 secara singkat":
        """
        <lafadz>اَللَّهُمَّ اغْفِرْلَهَا وَارْحَمْهَا وَعَافِهَا وَاعْفُ عَنْهَا, Allahhummaghfir laha warhamha wa aafiha wa fuanha</lafadz>,
        <terjemahan>Ya Allah ampunikah dia, berilah rahmat dan sejahtera dan maafkanlah dia</terjemahan>, <audio></audio>
        """,
    "bacaan doa shalat jenazah untuk anak laki-laki takbir ketiga atau ke 3":
        """
        <lafadz>أللَّهُمَّ ارْحَمْهُ وَعَافِهِ وَاكْرِمْ نُزُوْلَهُ وَوَسِعْ مَدْخَلَهُ بِرَحْمَتِكَ يَااَرْحَمَ الرَّحِمِيْنَ, Allahummarhamhu wa afih wakrim nuzulahu wawasi madkholahu birohmatika ya arhamarrahimin</lafadz>,
        <terjemahan>Ya Allah Kasih sayangilah anak ini selamatkanlah dia muliakanlah kedatangannya luaskanlah tempatnya dengan kasih sayang-Mu wahai yang Paling Maha Pengasih lagi Maha Penyayang</lafadz>, <audio></audio>
        """,
    "bacaan doa shalat jenazah untuk anak perempuan takbir ketiga atau ke 3":
        """
        <lafadz>اللَّهُمَّ ارْحَمْهَا وَاعْفُ عَنْهَا، وَكَرِّمْ نُزُلَهَا وَوَسِّعْ مَدْخَلَهَا بِرَحْمَتِكَ يَا أَرْحَمَ الرَّاحِمِينَ
        """,

}

penjelasan_contexts = {
    "Sejarah Haji":
        """
        Haji adalah salah satu dari lima Rukun Islam, dan menjadi ibadah yang sangat penting dalam agama Islam. 
        Haji dilakukan setiap tahun selama bulan Dzulhijjah, bulan terakhir dalam kalender Hijriyah, oleh umat Islam 
        yang mampu dan mampu melakukan perjalanan ke kota suci Mekkah di Arab Saudi.
        """,
    "Manasik Haji":
        """
        Manasik haji adalah serangkaian ritual yang dilakukan oleh jemaah haji sebagai bagian dari ibadah haji. 
        Ini termasuk tahalul, yakni memotong rambut; tawaf, yakni mengelilingi Ka'bah tujuh kali; dan sa'i, 
        yakni berjalan tujuh kali antara bukit Safa dan Marwah.
        """,
    "Hikmah haji dan umrah":
        """
        Hikmah disyariatkan haji dan umrah adalah untuk memakmurkan Ka’bah,dan ibadah haji dilaksanakan 
        dalam bulan-bulan haji (Syawal, DzulQa’dah,dan DzulHijjah), sedangkan ibadah umrah dapat dilaksanakan kapan saja 
        dalam setahun, tidak terikat dengan waktu. Menurut Qadi Husin dari kalangan syafi’iyah, ibadah haji lebih 
        utamanya ibadah, karena ibadah haji (termasuk umrah) meliputi harta dan badan. Menurut al-Halimy, haji mencakup 
        makna semua ibadah, karena orang yang berhaji, seakan-akan dia melaksanakan puasa, shalat, i’tikaf, zakat, 
        berjuang dan berperang di jalan Allah.Tentang keutamaan orang melaksanakan haji dan umrah adalah sebagai berikut: 
        Yang pertama, orang berhaji dan umrah adalah tamu Allah, dan do’anya mustajabah. Nabi Muhammad SAW bersabda: "Dari Anas bin Malik, Rasulullah SAW bersabda: Orang-orang 
        yang melaksanakan haji dan umrah adalah tentara Allah, Allah akan memberikan terhadap apa yang meraka minta, akan menerima apa yang mereka doakan, 
        akan mengganti terhadap apa yang mereka infakkan dengan sejuta dirham". Nabi Muhammad SAW bersabda: "Orang-orang yang melaksanakan haji dan umrah adalah tentara Allah, 
        jika mereka berdo’a diterima oleh Allah, dan jika mereka minta ampun, diampuni oleh Allah" (HR. al-Nasa’i dan Ibnu Hibban). Yang kedua adalah ibadah haji dan umrah adalah 
        jihad di jalan Allah, "diriwayatkan dari Aisyah RA, ia bertanya : Wahai Rasulullah, apakah wanita wajib berjihad? Rasulullah SAW menjawab: Iya. Dia wajib berjihad tanpa ada 
        peperangan di dalamnya, yaitu dengan haji dan umrah." (HR. Ibnu Majah), Yang ketiga adalah ibadah 
        Haji dan umrah adalah pelebur dosa. Dalam hadits yang lain Nabi menjelaskan : "Dari Abi Hurairah r.a. 
        sesungguhnya Rasulullah SAW bersabda: Antara ibadah umrah dengan ibadah umrah yang lain adalah menghapus dosa, 
        dan haji mabrur tidak ada balasan baginya kecuali surga." (HR. Bukhari dan Muslim). Kemudian Nabi 
        juga menjelaskan : "Diampuni orang yang berhaji dan orang yang dimintai ampunan oleh orang yang 
        berhaji.". Haji membersihkan jiwa, mengembalikan diri manusia pada kesucian dan keikhlasan, 
        mengantarkan pada kehidupan yang baru, meningkatkan nilai-nilai kemanusiaan, menguatkan cita-cita dan berbaik 
        sangka kepada Allah SWT. Haji menguatkan iman, membantu pembaharuan perjanjian kepada Allah, membantu untuk 
        bertaubat yang ikhlas dan jujur, membersihkan jiwa, menyebarluaskan syiar-syiar agama. Yang keempat yaitu, 
        ibadah haji dan umrah adalah menghapus kefakiran dan dosa. "Diriwayatkan dari Ibnu Abbas RA, 
        Rasulullah SAW bersabda: Ikutkanlah umrah kepada haji, karena keduanya dapat menghilangkan kemiskinan dan 
        dosa-dosa seperti pembakaran menghilangkan karat besi, emas, dan perak. dan tidak ada pahala bagi haji yang 
        mabrur kecuali surga." (HR. An-Nasa’i).Yang kelima adalah, mendapat pahala sampai hari qiyamah bila 
        meninggal (mati) saat mengerjakan ibadah haji atau umrah. Kemudian yang keenam adalah, melaksanakan ibadah umrah 
        pada bulan Ramadhan sebanding dengan ibadah haji. Nabi Muhammad SAW bersabda: "jika tiba bulan Ramadhan 
        berumrahlah, karena ibadah umrah pada bulan Ramadhan seperti ibadah haji.".
        """,
}


def calculate_similarity_score(user_message, keyword):
    return fuzz.ratio(user_message, keyword)


def choose_context(user_message, context_dict, threshold=70):
    best_score = 0
    best_context = None
    for keyword, context in context_dict.items():
        score = fuzz.partial_ratio(user_message, keyword)
        if score > best_score:
            best_score = score
            best_context = context
    if best_score < threshold:
        return None
    return best_context


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Doa", callback_data='doa')],
        [InlineKeyboardButton("Penjelasan", callback_data='penjelasan')],
        [InlineKeyboardButton("Batal", callback_data='cancel')],  # Menambahkan tombol 'Batal'
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Halo! Saya adalah bot Muslim. Silakan pilih salah satu opsi berikut:', reply_markup=reply_markup)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    choice = query.data

    if choice == 'cancel':  # Menambahkan pilihan 'cancel'
        cancel(update, context)
    else:
        context.user_data['choice'] = choice

        if choice == 'doa':
            if update.callback_query.message.text != 'Anda telah memilih opsi "Doa". Silakan ajukan pertanyaan Anda:':
                update.callback_query.edit_message_text(text='Anda telah memilih opsi "Doa". Silakan ajukan pertanyaan Anda:')
        else:
            keyboard = [[InlineKeyboardButton(context, callback_data='penjelasan_' + context)] for context in penjelasan_contexts.keys()]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if update.callback_query.message.text != 'Anda telah memilih opsi "Penjelasan". Silakan pilih topik yang ingin Anda ketahui:':
                update.callback_query.edit_message_text(text='Anda telah memilih opsi "Penjelasan". Silakan pilih topik yang ingin Anda ketahui:', reply_markup=reply_markup)


def topic_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    topic = query.data.replace('penjelasan_', '')
    context.user_data['penjelasan_topik'] = topic

    update.callback_query.edit_message_text(text=f"Anda telah memilih topik '{topic}'. Silakan ajukan pertanyaan Anda:")


def start_doa(update: Update, context: CallbackContext) -> None:
    context.user_data['choice'] = 'doa'
    update.message.reply_text("Doa apa yang ingin Anda cari?")


def doa_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Anda memilih opsi "Doa". Silakan ajukan pertanyaan Anda:')
    context.user_data['choice'] = 'doa'
    if 'penjelasan_topik' in context.user_data:
        del context.user_data['penjelasan_topik']  # Hapus topik penjelasan saat berpindah ke doa


def penjelasan_command(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton(context, callback_data='penjelasan_' + context)] for context in penjelasan_contexts.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Anda telah memilih opsi "Penjelasan". Silakan pilih topik yang ingin Anda ketahui:', reply_markup=reply_markup)
    context.user_data['choice'] = 'penjelasan'  # Atur pilihan pengguna ke penjelasan


def cancel(update: Update, context: CallbackContext) -> None:
    if update.callback_query is not None:
        # Ini adalah callback query
        query = update.callback_query
        query.answer()
        query.edit_message_text('Anda telah membatalkan permintaan. Terima kasih!')
    else:
        # Ini adalah command
        update.message.reply_text('Anda telah membatalkan permintaan. Terima kasih!')

    context.user_data.clear()


def extract_info_from_context(context):
    lafadz_matches = re.findall(r"<lafadz>\s*(.*?)\s*</lafadz>", context)
    translation_matches = re.findall(r"<terjemahan>\s*(.*?)\s*</terjemahan>", context)
    audio_path_matches = re.findall(r"<audio>(.*?)</audio>", context)
    return lafadz_matches, translation_matches, audio_path_matches


def answer_question(update: Update, context: CallbackContext) -> None:
    print(f"Debug: penjelasan_topik = {context.user_data.get('penjelasan_topik')}")
    message = update.message.text.lower().strip()
    print(f"Message: {message}")

    if not context.user_data.get("choice"):
        update.message.reply_text("Mohon pilih 'doa' atau 'penjelasan' terlebih dahulu sebelum mengajukan pertanyaan.")
        return

    if context.user_data["choice"] == "doa":
        best_context = choose_context(message, doa_contexts)
        print(f"Best context: {best_context}")
        if best_context is None:
            update.message.reply_text("Maaf, saya tidak dapat menemukan doa yang Anda cari.")
            return
        lafadz, translations, audio_paths = extract_info_from_context(best_context)
        for i in range(len(lafadz)):
            arabic, arab_latin = lafadz[i].split(', ', 1)
            answer = f"{arabic}\n\n({arab_latin})\n\nTerjemahan: {translations[i]}"
            update.message.reply_text(answer)
    elif context.user_data["choice"] == "penjelasan":  # Penjelasan
        if 'penjelasan_topik' not in context.user_data:
            update.message.reply_text("Mohon pilih topik terlebih dahulu.")
            return
        best_context = penjelasan_contexts.get(context.user_data['penjelasan_topik'], None)
        if not best_context:
            update.message.reply_text("Maaf, konten penjelasan untuk topik ini belum tersedia.")
            return
        if best_context.strip() == "":
            update.message.reply_text("Maaf, konten penjelasan untuk topik ini kosong.")
            return
        print(f"Best context: {best_context}")
        answer = qa_pipeline({"question": message, "context": best_context})
        if answer.strip() == "":
            update.message.reply_text("Maaf, saya tidak dapat menemukan jawaban untuk pertanyaan Anda.")
            return
        update.message.reply_text(answer)


def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    pp = PicklePersistence(filename='userdata')
    updater = Updater("5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU", persistence=pp, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("doa", doa_command))
    dispatcher.add_handler(CommandHandler("penjelasan", penjelasan_command))
    dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^doa$|^penjelasan$'))
    dispatcher.add_handler(CallbackQueryHandler(topic_click, pattern='^penjelasan_'))
    dispatcher.add_handler(CallbackQueryHandler(cancel, pattern='^cancel$'))  # Merubah ini menjadi CallbackQueryHandler
    dispatcher.add_handler(CommandHandler("cancel", cancel))  # Tambahkan baris ini
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer_question))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
