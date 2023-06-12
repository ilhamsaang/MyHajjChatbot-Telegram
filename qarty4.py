import logging
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext.filters import Filters
from pipeline_qa import TaskPipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

qa_pipeline = TaskPipeline()

contexts = [
    """
    Pergi ke Makkah-Madinah menjadi dambaan setiap umat Islam di seluruh penjuru dunia, sejak masa Nabi
    Adam AS., hingga kini, kita sebagai umat Nabi Muhammad SAW, dan insya Allah sampai pada hari qiyamah. Panggilan
    hati nurani yang sangat mendalam dari setiap umat Islam untuk datang ke Makkah-Madinah terlahir karena beberapa
    faktor. Pertama, pergi ke Makkah-Madinah adalah panggilan ilahi, sehingga kebesaran nikmat Allah SWT dalam bentuk
    ini tidak bisa diungkapkan dengan kata-kata. Kedua, setiap umat Islam yang datang ke Makkah-Madinah, bisa
    dipastikan untuk memfokuskan tujuannya ziarah ke makam Rasulullah SAW. Mendatangi sebidang tanah yang menjadi
    tempat Rasulullah SAW dikubur, berarti mendatangi tanah paling mulia di dunia, karena paling mulianya tanah di
    muka bumi ini adalah tanah yang mengapit jasad “insan kamil”, junjungan Nabi Muhammad SAW. Di samping itu
    melaksanakan shalat di Masjid Nabawi. untuk menuju ke masjid nabawi dapat melalui rute berikut(https://www.google.com/maps/search/?api=1&query=my+location+to+Masjid+nabawi+madinah&hl=id). melebihi seribu shalat di masjid lainnya, kecuali Masjidil Haram. Ketiga,
    Masjidil Haram adalah sebuah masjid yang menjadi kiblat dunia, itu artinya Masjidil Haram merupakan sebidang tanah 
    yang mulia di dunia sampai hari qiyamah.Keempat, di jazirah Arab banyak tempat yang mempunyai nilai sejarah
    yang sangat agung dan mustajabah. Mungkin bisa dikatakan belum sempurna hidup seseorang bila belum sampai ke
    Makkah-Madinah.
    """,
    """
    Penjelasan mengenai ketentuan umrah.\nHikmah disyariatkan haji dan umrah adalah untuk memakmurkan Ka’bah dengan 
    ibadah,dan ibadah haji dilaksanakan dalam bulan-bulan haji (Syawal, DzulQa’dah,dan DzulHijjah), sedangkan ibadah 
    umrah dapat dilaksanakan kapan saja dalam setahun, tidak terikat dengan waktu. Menurut Qadi Husin dari kalangan 
    syafi’iyah, ibadah haji lebih utamanya ibadah, karena ibadah haji (termasuk umrah) meliputi harta dan badan. 
    Menurut al-Halimy, haji mencakup makna semua ibadah, karena orang yang berhaji, seakan-akan dia melaksanakan puasa, 
    shalat, i’tikaf, zakat, berjuang dan berperang di jalan Allah.Tentang keutamaan orang melaksanakan haji dan umrah 
    adalah sebagai berikut:\n1.\tOrang berhaji dan umrah adalah tamu Allah, dan do’anya mustajabah\nNabi Muhammad SAW 
    bersabda:\"Dari Anas bin Malik, Rasulullah SAW bersabda: Orang-orang yang melaksanakan haji dan umrah adalah tentara 
    Allah, Allah akan memberikan terhadap apa yang meraka minta, akan menerima apa yang mereka doakan, akan mengganti 
    terhadap apa yang mereka infakkan dengan sejuta dirham .\"\nNabi Muhammad SAW bersabda: \"Orang-orang yang
    melaksanakan haji dan umrah adalah tentara Allah, jika mereka berdo’a diterima oleh Allah, dan jika mereka 
    minta ampun, diampuni oleh Allah (HR. al-Nasa’i dan Ibnu Hibban).\"\n2.\tIbadah haji dan umrah adalah jihad di jalan 
    Allah,\"diriwayatkan dari Aisyah RA, ia bertanya : Wahai Rasulullah, apakah wanita wajib berjihad? Rasulullah SAW 
    menjawab: Iya. Dia wajib berjihad tanpa ada peperangan di dalamnya, yaitu dengan haji dan umrah.\" (HR. Ibnu Majah).
    \n3.\tIbadah Haji dan umrah adalah pelebur dosa.\nDalam hadits yang lain Nabi menjelaskan : \"Dari Abi Hurairah r.a. 
    sesungguhnya Rasulullah SAW bersabda: Antara ibadah umrah dengan ibadah umrah yang lain adalah menghapus dosa, 
    dan haji mabrur tidak ada balasan baginya kecuali surga\" (HR. Bukhari dan Muslim). Kemudian Nabi juga menjelaskan 
    :\"Diampuni orang yang berhaji dan orang yang dimintai ampunan oleh orang yang berhaji.\" \nHaji membersihkan jiwa, 
    mengembalikan diri manusia pada kesucian dan keikhlasan, mengantarkan pada kehidupan yang baru, meningkatkan 
    nilai-nilai kemanusiaan, menguatkan cita-cita dan berbaik sangka kepada Allah SWT. Haji menguatkan iman, membantu 
    pembaharuan perjanjian kepada Allah, membantu untuk bertaubat yang ikhlas dan jujur, membersihkan jiwa, 
    menyebarluaskan syiar-syiar agama.\n4.\tIbadah haji dan umrah adalah menghapus kefakiran dan dosa.\n\"Diriwayatkan 
    dari Ibnu Abbas RA, Rsulullah SAW bersabda: Ikutkanlah umrah kepada haji, karena keduanya dapat menghilangkan 
    kemiskinan dan dosa-dosa seperti pembakaran menghilangkan karat besi, emas, dan perak. dan tidak ada pahala bagi 
    haji yang mabrur kecuali surga.\" (HR. An-Nasa’i).\n5.\tMendapat pahala sampai hari qiyamah bila meninggal (mati) 
    saat mengerjakan ibadah haji atau umrah.\n6.\tMelaksanakan ibadah umrah pada bulan Ramadhan sebanding dengan 
    ibadah haji.\n\"Nabi Muhammad SAW bersabda: jika tiba bulan Ramadhan berumrahlah, karena ibadah umrah pada bulan 
    Ramadhan seperti ibadah haji.\"
    """,
    """
    Penjelasan Tata cara bepergian untuk umrah.\nBagi orang yang mempunyai kemampuan atau keinginan untuk melaksanakan 
    ibadah umrah hendaknya memperhatikan hal-hal sebagai berikut:\n1.\tBermaksud untuk mencari ridha Allah, mendekatkan 
    diri kepada Allah, menghindari kepentingan dunia,berbangga-bangga, mencari status sosial, riya’ atau (pamer) dan 
    sum’ah (kemasyhuran/kenamaan).\n2.\tMenulis wasiyat tentang hak dan kewajiban seperti hutang-piutang, seakan-akan 
    salam perpisahan yang tidak akan kembali lagi, karena ajal di tangan Tuhan.\n3.\tMinta maaf kepada sesamanya atas 
    segala bentuk kesalahan dan kedhaliman yang perna dilakukan, bertaubat dari berbagai dosa dan maksiat, serta 
    menyesali terhadap segala kesalahan dan berniat untuk tidak melakukan kembali.\4.\tUntuk biaya dan bekal 
    melaksanakan ibadah memilih harta yang baik dan halal, karena Allah adalah baik dan tidak menerima sesuatu kecuali 
    yang baik.\n5.\tMenjahui perbuatan maksiat, jangan menyakiti orang lain walaupun dengan kata-kata, jangan berbicara 
    kotor, jangan adu domba, jangan berbohong, dan jangan bersesak-desakan karena dapat menyakiti orang lain.
    \n6.\tHendaknya memahami hukum-hukum umrah, dan tata cara pelaksanaan ibadah umrah.\n7.\tMenjaga seluruh kewajiban, 
    terutama shalat lima waktu berjama’ah pada waktunya, banyak membaca Al-Qur’an, berdzikir, berdo’a, berbuat baik 
    kepada sesamanya baik dengan perkataan atau dengan perbuatan, menolong orang yang membutuhkan, bersikap lemah 
    lembut, bersedekah kepada fakir-miskin, dan menyuruh kepada kebaikan dan melarang kemungkaran.\n8.\tMencari kawan 
    yang baik.\n9.\tHendaknya berakhlaq mulia; ikhlas, sabar, wara’, pemaaf, adil, amanah, bijaksana, tawadu’, dan 
    dermawan.
    """
]


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Selamat datang di IbadahHajibot! Silakan ajukan pertanyaan Anda:',
                              reply_markup=ForceReply())


def choose_context(message):
    vectorizer = TfidfVectorizer()
    context_vectors = vectorizer.fit_transform(contexts)
    query_vector = vectorizer.transform([message])

    similarity_scores = cosine_similarity(query_vector, context_vectors)
    best_context_index = similarity_scores.argmax()

    return contexts[best_context_index]


def answer_question(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    selected_context = choose_context(message)
    answer = qa_pipeline({"question": message, "context": selected_context})
    update.message.reply_text(answer)


def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    updater = Updater("5406578688:AAFH_y4p9ubBqp0XeHv9tYwmMjCk0HEh9OU", use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answer_question))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()