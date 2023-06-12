import pipeline_qa

qa = pipeline_qa.pipeline()

qa({"context": """
ada beberapa tempat peribadatan yang biasanya dikunjungi oleh jamaah indonesia.Kota Madinah merupakan salah satu tempat yang pastinya dikunjungi saat melaksanakan ibadah haji maupun umroh tempat peribadatan yang terkenal salahsatunya adalah masjid nabawi yang dekat dengan makam al-baqi dimana sahabat nabi dimakamkan dan pastinya populer bagi jamaah haji maupun umrah di indonesia untuk melakukan peribadatan di masjid tersebut,
selain itu akses menuju masjid dapat menggunakan kendaraan dikarenakan adanya tempat parkir yang telah disediakan. untuk menuju ke masjid nabawi dapat melalui link berikut:
https://www.google.com/maps/search/?api=1&query=my+location+to+Masjid+nabawi+madinah&hl=id.
"""})

qa({"context": """

"""})