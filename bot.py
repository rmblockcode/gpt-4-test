import os
import math
from pytube import YouTube
from moviepy.editor import VideoFileClip
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = os.environ.get('TELEGRAM_TOKEN')
DOWNLOAD_DIR = 'downloads'
filename = 'videofinal'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Envía el enlace del video de YouTube que deseas descargar.')

def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    chat_id = update.effective_chat.id
    try:
        yt = YouTube(url, on_progress_callback=show_progress)
        video = yt.streams.filter(file_extension='mp4', progressive=True).first()

        file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.mp4")
        video.download(output_path=DOWNLOAD_DIR, filename=f"{filename}.mp4")

        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            update.message.reply_text("El video es demasiado grande. Se dividirá en partes.")
            clip = VideoFileClip(file_path)
            duration = clip.duration
            num_parts = math.ceil(os.path.getsize(file_path) / (50 * 1024 * 1024))
            part_duration = duration / num_parts

            for i in range(num_parts):
                start_time = i * part_duration
                end_time = (i + 1) * part_duration if i < num_parts - 1 else duration
                new_clip = clip.subclip(start_time, end_time)
                part_file_path = os.path.join(DOWNLOAD_DIR, f"{filename}_part{i + 1}.mp4")
                new_clip.write_videofile(part_file_path)
                with open(part_file_path, 'rb') as f:
                    context.bot.send_video(chat_id=chat_id, video=f)
        else:
            with open(file_path, 'rb') as f:
                context.bot.send_video(chat_id=chat_id, video=f)

        update.message.reply_text("Video descargado y enviado con éxito.")
    except Exception as e:
        print(e)
        update.message.reply_text("Error al descargar el video. Por favor, intenta con otro enlace.")

def show_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = int(bytes_downloaded / total_size * 100)
    print(f"Descargando: {percentage}% completado")

def main():
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
