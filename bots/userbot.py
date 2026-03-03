from pyrogram import Client, filters
import logging
import time

logging.basicConfig(level=logging.INFO)

# userbot sesion debe ser creada con "pyrogram" CLI o manualmente
user = Client("userbot", api_id=12345, api_hash="<HASH>")


@user.on_message(filters.group)
def watch(client, message):
    # registro de mensajes para análisis forense
    logging.info(f"[userbot] {message.date} {message.from_user.id} {message.text}")


if __name__ == "__main__":
    user.run()
