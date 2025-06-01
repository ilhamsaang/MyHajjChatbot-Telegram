# 🕋 MyHajjChatbot-Telegram

**MyHajjChatbot-Telegram** is a specialized chatbot designed to assist Hajj pilgrims by providing answers to frequently asked questions and offering navigational support during the pilgrimage. This project was developed as part of a final thesis titled:

> *"Desain Interaksi Q/A Closed Domain Dukungan Peta Navigasi Keperluan Jamaah Haji"*

The chatbot leverages the [**Indonesian T5 (IDT5)**](https://huggingface.co/muchad/idt5-qa-qg) model for both question answering and question generation within a closed-domain context, focusing on Hajj-related topics.

---

## 📌 Features

- **Closed-Domain Q&A**: Provides accurate answers to Hajj-related questions using the IDT5 model.
- **Question Generation**: Generates relevant questions to enhance the chatbot's knowledge base.
- **Telegram Integration**: Accessible via the Telegram messaging platform for ease of use.
- **Navigation Support**: Offers map-based guidance to assist pilgrims during their journey.

---

## 🛠️ Installation

### Prerequisites

- Python 3.7 or higher
- Telegram Bot Token (obtain from [@BotFather](https://t.me/BotFather))
- Required Python packages (listed in `requirements.txt`)

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ilhamsaang/MyHajjChatbot-Telegram.git
   cd MyHajjChatbot-Telegram

2. **Install Dependencies**

   pip install -r requirements.txt

3. **Configure the Bot**

   Create a .env file in the root directory.

   Add your Telegram Bot Token on .env file:
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

4. **Run the Bot**
   Bash : python Main.py







