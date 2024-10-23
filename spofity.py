import redis
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from googleapiclient.discovery import build
import os
import re

# Tokeningizni kiriting
API_TOKEN = '6901637071:AAGUjoH4b1daS5dhfFT15tgpMVnNxzZxzx8'  # Botingizning haqiqiy API tokenini qo'shing
YOUTUBE_API_KEY = 'AIzaSyDuOYC8k6I-0EBxU4WXtDonPJQXcItQ70c'  # YouTube API kaliti

# YouTube API'ga ulanish
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Botni yaratamiz
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Redis kesh uchun ulash
cache = redis.Redis(host='localhost', port=6379, db=0)

def clean_filename(filename):
    # Fayl nomlaridan maxsus belgilarni olib tashlaydi
    # Maxsus belgilarni olib tashlash uchun yanada kengroq regex qo'llaniladi
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()  # Strip bo'sh joylarni olib tashlaydi


@dp.callback_query_handler(lambda call: call.data.startswith('link'))
async def handle_search_result(call: types.CallbackQuery):
    _, _, link = call.data.split('_')

    await call.answer(f'Siz quyidagi musiqani tanladingiz: {link}')

    # Agar Instagram video linki bo'lsa, avval yuklash
    if "instagram.com" in link:
        video_title, video_file = await download_instagram_video(link)

        # Yuklab olingan faylni tekshirish va yuborish
        if os.path.exists(video_file):
            with open(video_file, 'rb') as video:
                await bot.send_video(call.from_user.id, video=video, caption=f'Yuklab olingan video: {video_title}')
        else:
            await call.answer("Video fayl topilmadi, qayta urinib ko'ring.")
    else:
        # Boshqa musiqalarni yuklab olish
        download_path = download_media(link, format_type='audio')

        if os.path.exists(download_path):
            with open(download_path, 'rb') as audio_file:
                await bot.send_audio(call.from_user.id, audio=audio_file,
                                     caption=f'Yuklab olingan musiqa: {download_path}')
        else:
            await call.answer("Musiqa fayli topilmadi, qayta urinib ko'ring.")


async def download_instagram_video(url):
    ydl_opts = {
        'ffmpeg_location': r'D:\TestBot\ffmpeg-master-latest-win64-gpl-shared\bin',
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_title = clean_filename(info['title'])  # Fayl nomini tozalash
        video_file = f"downloads/{video_title}.{info['ext']}"
        return video_title, video_file

# Instagram musiqasini yuklash uchun yordamchi funksiya


# Video va musiqa yuklash uchun yordamchi funksiya
def download_media(link, format_type='audio'):
    ydl_opts = {
        'ffmpeg_location': r'D:\TestBot\ffmpeg-master-latest-win64-gpl-shared\bin',
        'format': 'bestaudio/best',
        'outtmpl': 'audios/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=True)
        title = clean_filename(info_dict.get('title', 'Untitled'))  # Fayl nomini tozalash
        return f'audios/{title}.mp3'  # Tozalangan fayl nomini ishlatish


# Musiqa va video qidirish
def search_youtube(query, page_token=None):
    search_response = youtube.search().list(
        q=query,
        part='snippet',
        maxResults=10,
        type='video',
        videoCategoryId='10',
        pageToken=page_token
    ).execute()

    results = []
    next_page_token = search_response.get('nextPageToken')
    for item in search_response.get('items', []):
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        title = item['snippet']['title']
        channel_title = item['snippet']['channelTitle']
        results.append({'title': title, 'url': video_url, 'author': channel_title})

    return results, next_page_token

# Musiqa qidirish tugmasi
@dp.message_handler()
async def search_media(message: types.Message):
    query = message.text
    search_results, next_page_token = search_youtube(query)

    if search_results:
        await send_search_results(message, query, search_results, next_page_token)
    else:
        await message.answer("Hech qanday natija topilmadi.")

# Natijalarni yuborish
async def send_search_results(message, query, search_results, next_page_token, prev_page_token=None):
    results_text = "Natijalar:\n\n" + "\n".join(
        [f"{i + 1}. {result['title']} - {result['author']} - {result['url']}" for i, result in
         enumerate(search_results)]
    )

    # Eski natijani o'chirish
    await message.answer(results_text)

    markup = InlineKeyboardMarkup()
    button_row = []

    for index, result in enumerate(search_results, start=1):
        button = InlineKeyboardButton(text=f"Yuklab olish {index}", callback_data=f"link_{index}_{result['url']}")
        button_row.append(button)

        if index % 5 == 0 or index == len(search_results):
            markup.add(*button_row)
            button_row = []

    # Keyingi sahifa tugmasini qo'shamiz
    if next_page_token:
        markup.add(InlineKeyboardButton("Keyingi sahifa", callback_data=f"next_{query}_{next_page_token}"))

    # Oldingi sahifa tugmasini qo'shamiz
    if prev_page_token:
        markup.add(InlineKeyboardButton("Oldingi sahifa", callback_data=f"previous_{query}_{prev_page_token}"))

    await message.answer("Natijalar:", reply_markup=markup)

# Qidiruv natijalarini ishlatish
@dp.callback_query_handler(lambda call: call.data.startswith('link'))
async def handle_search_result(call: types.CallbackQuery):
    _, _, link = call.data.split('_')

    await call.answer(f'Siz quyidagi musiqani tanladingiz: {link}')

    # Musiqa yuklab olish
    download_path = download_media(link, format_type='audio')

    # Yuklab olingan faylni tekshirish
    if os.path.exists(download_path):
        with open(download_path, 'rb') as audio_file:
            await bot.send_audio(call.from_user.id, audio=audio_file, caption=f'Yuklab olingan: {download_path}')
    else:
        await call.answer("Fayl topilmadi, qayta urinib ko'ring.")

# Keyingi sahifa tugmasini ishlatish
@dp.callback_query_handler(lambda call: call.data.startswith('next'))
async def handle_next_page(call: types.CallbackQuery):
    _, query, page_token = call.data.split('_')
    search_results, next_page_token = search_youtube(query, page_token)

    # Eski natijani o'chirish
    await call.message.delete()

    if search_results:
        await send_search_results(call.message, query, search_results, next_page_token, page_token)

# Oldingi sahifa tugmasini ishlatish
@dp.callback_query_handler(lambda call: call.data.startswith('previous'))
async def handle_previous_page(call: types.CallbackQuery):
    _, query, page_token = call.data.split('_')
    search_results, next_page_token = search_youtube(query, page_token)

    # Eski natijani o'chirish
    await call.message.delete()

    if search_results:
        await send_search_results(call.message, query, search_results, next_page_token, page_token)

# Botni ishga tushirish
if __name__ == '__main__':
    if not os.path.exists('videos'):
        os.makedirs('videos')
    if not os.path.exists('audios'):
        os.makedirs('audios')

    executor.start_polling(dp, skip_updates=True)
