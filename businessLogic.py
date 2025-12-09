import tempfile
import sys
import codecs
import ssl
import os
import subprocess
import time
import io
from moviepy.editor import VideoFileClip
import yt_dlp
import numpy as np

# Force UTF-8 encoding for Windows console (must be before any print statements)
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignore if already wrapped or in Streamlit environment

# 🔧 الإعداد الذكي لـ FFmpeg (متوافق مع Windows و Linux/Cloud)
import shutil


def get_ffmpeg_path():
    # 1. البحث في مسار النظام (System PATH)
    if shutil.which("ffmpeg"):
        return "ffmpeg", ""
        
    # 2. البحث في المجلد المحلي (Windows Portable Version)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe")
    
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg, os.path.dirname(local_ffmpeg)
        
    return None, None

ffmpeg_path, ffmpeg_dir = get_ffmpeg_path()


if ffmpeg_path:
    print(f"✅ FFmpeg تم اكتشافه: {ffmpeg_path}")
    
    # تحديث متغيرات البيئة إذا كان مساراً محلياً
    if ffmpeg_dir:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        os.environ["WHISPER_FFMPEG_PATH"] = ffmpeg_path
    
    # اختبار بسيط
    try:
        subprocess.run([ffmpeg_path, '-version'], capture_output=True, timeout=5)
    except Exception as e:
        print(f"⚠️ تحذير: فشل اختبار FFmpeg: {e}")

else:
    print("⚠️ تحذير: لم يتم العثور على FFmpeg في النظام أو المجلد المحلي!")
    # لن نوقف البرنامج هنا، فقد يعمل moviepy بدونه في بعض الحالات


ssl._create_default_https_context = ssl._create_stdlib_context

class ProgressState:
    def __init__(self):
        self.current_stage = ""
        self.progress = 0
        self.total_stages = 4
        self.stage_details = ""
        self.is_completed = False
        self.error = None

def transcribe_audio_optimized(source: str, model, device_info: dict, progress_callback=None, cookies=None, controller=None):
    """✅ دالة محسنة للتحويل باستخدام النموذج المخبأ والمعلومات المسبقة"""
    progress = ProgressState()
    
    try:
        if controller and controller.check_stop():
             return "⏹️ تم إيقاف العملية"

        # المرحلة 1: التحضير واستخراج الصوت
        progress.current_stage = "استخراج الصوت"
        progress.progress = 25
        progress.stage_details = "جاري معالجة مصدر الفيديو..."
        if progress_callback:
            progress_callback(progress)
        
        # ✅ تحديد نوع المصدر واستخراج الصوت
        source = source.strip()
        audio_path = None
        
        if source.startswith(('http://', 'https://')):
            try:
                audio_path = download_youtube_audio_optimized(source, progress_callback, cookies, controller)
            except Exception as dl_error:
                if "STOP_REQUESTED" in str(dl_error):
                    return "⏹️ تم إيقاف العملية"
                progress.error = f"❌ Error: {str(dl_error)}"
                if progress_callback:
                    progress_callback(progress)
                return progress.error
        else:
            audio_path = extract_audio_optimized(source, progress_callback)
        
        if not audio_path or not os.path.exists(audio_path):
            if not progress.error:
                progress.error = "❌ Error: لم يتم إنشاء ملف الصوت"
            if progress_callback:
                progress_callback(progress)
            return progress.error

        if controller and controller.check_stop():
             return "⏹️ تم إيقاف العملية"

        # ✅ المرحلة 2: استخدام النموذج المخبأ مباشرة (0% تقدم - فوري)
        progress.current_stage = "التحويل إلى نص"
        progress.progress = 75
        progress.stage_details = f"جاري التحويل على {device_info['device'].upper()} - {device_info['compute_type']}"
        if progress_callback:
            progress_callback(progress)
        
        # ✅ استخدام النموذج المخبأ للتحويل
        result_text = perform_transcription(audio_path, model, device_info, progress_callback)
        
        # تنظيف الملف المؤقت
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print("🧹 تم تنظيف الملف المؤقت للصوت")
            except:
                pass
        
        # المرحلة 4: الإكمال
        progress.current_stage = "الإكمال"
        progress.progress = 100
        progress.stage_details = "تم الانتهاء بنجاح!"
        progress.is_completed = True
        if progress_callback:
            progress_callback(progress)
        
        return result_text
        
    except Exception as e:
        progress.error = f"❌ Error: {str(e)}"
        progress.current_stage = "خطأ"
        progress.stage_details = f"حدث خطأ: {str(e)}"
        if progress_callback:
            progress_callback(progress)
        return progress.error


def perform_transcription(audio_path: str, model, device_info: dict, progress_callback=None):
    """✅ تنفيذ التحويل باستخدام النموذج المخبأ"""
    print(f"🎯 بدء تحويل الصوت إلى نص باستخدام Faster-Whisper")
    print(f"📊 وضع التشغيل: {device_info['device']} - {device_info['compute_type']}")
    
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"ملف الصوت غير موجود: {audio_path}")
        
        # ✅ التحويل باستخدام النموذج المخبأ
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        # جمع النص والـ segments
        text_parts = []
        segments_data = []
        
        for segment in segments:
            text_parts.append(segment.text)
            # حفظ segment مع timestamps
            segments_data.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
        
        text = " ".join(text_parts)
        print("✅ تم التحويل بنجاح باستخدام Faster-Whisper!")
        print(f"📊 معلومات التحويل: اللغة={info.language}, احتمال اللغة={info.language_probability:.2f}")
        
        # إرجاع النص مع segments
        return {
            'text': text,
            'segments': segments_data,
            'language': info.language,
            'language_probability': info.language_probability
        }
        
    except Exception as e:
        print(f"❌ خطأ في التحويل باستخدام Faster-Whisper: {e}")
        return {
            'text': f"Error during transcription: {str(e)}",
            'segments': [],
            'language': 'unknown',
            'language_probability': 0.0
        }

def format_text_with_sentences(text):
    """تنسيق النص بحيث تكون كل جملة في سطر منفصل"""
    import re
    # تقسيم النص حسب علامات الترقيم
    sentences = re.split(r'([.!?]+\s+)', text)
    
    formatted_lines = []
    current_sentence = ""
    
    for i, part in enumerate(sentences):
        current_sentence += part
        # إذا كانت علامة ترقيم، أضف السطر
        if re.match(r'[.!?]+\s+', part) or i == len(sentences) - 1:
            if current_sentence.strip():
                formatted_lines.append(current_sentence.strip())
            current_sentence = ""
    
    return "\n".join(formatted_lines)

def format_with_timestamps(segments_data):
    """تنسيق النص مع timestamps"""
    formatted_lines = []
    
    for segment in segments_data:
        # تحويل الوقت إلى صيغة [HH:MM:SS]
        start_time = format_timestamp(segment['start'])
        formatted_lines.append(f"[{start_time}] {segment['text']}")
    
    return "\n".join(formatted_lines)

def format_timestamp(seconds):
    """تحويل الثواني إلى صيغة HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def export_as_srt(segments_data):
    """تصدير كملف SRT للترجمة"""
    srt_lines = []
    
    for i, segment in enumerate(segments_data, 1):
        start = format_srt_timestamp(segment['start'])
        end = format_srt_timestamp(segment['end'])
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(segment['text'])
        srt_lines.append("")  # سطر فارغ
    
    return "\n".join(srt_lines)

def format_srt_timestamp(seconds):
    """تحويل الثواني إلى صيغة SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def extract_audio_optimized(video_path: str, progress_callback=None) -> str:
    """استخراج الصوت مع محاولات متعددة"""
    try:
        print(f"🎵 استخراج الصوت من: {video_path}")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"الملف غير موجود: {video_path}")
        
        # تحديث التقدم
        if progress_callback:
            progress = ProgressState()
            progress.current_stage = "استخراج الصوت"
            progress.stage_details = "جاري استخراج الصوت من الفيديو..."
            progress_callback(progress)
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{video_name}_audio.wav")
        
        # المحاولة 1: استخدام moviepy (لا يحتاج FFmpeg في PATH)
        try:
            print("🔧 المحاولة 1: استخدام moviepy...")
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_path, verbose=False, logger=None)
            audio_clip.close()
            video_clip.close()
            
            if os.path.exists(audio_path):
                print(f"✅ نجح باستخدام moviepy: {audio_path}")
                return audio_path
        except Exception as e:
            print(f"⚠️ فشلت moviepy: {e}")
        
        # المحاولة 2: استخدام FFmpeg مباشرة إذا كان متوفراً
        try:
            print("🔧 المحاولة 2: استخدام FFmpeg مباشرة...")
            ffmpeg_cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', audio_path
            ]
            
            # زيادة وقت الانتظار لـ FFmpeg إلى 60 ثانية
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(audio_path):
                print(f"✅ نجح باستخدام FFmpeg مباشرة: {audio_path}")
                return audio_path
            else:
                print(f"⚠️ فشل FFmpeg: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("⚠️ استخراج الصوت باستخدام FFmpeg تجاوز الوقت المحدد")
        except Exception as e:
            print(f"⚠️ فشلت محاولة FFmpeg: {e}")
        
        print("❌ فشلت جميع محاولات استخراج الصوت")
        return None
            
    except Exception as e:
        print(f"❌ خطأ في استخراج الصوت: {e}")
        return None

def download_youtube_audio_optimized(youtube_url: str, progress_callback=None, cookies_content=None, controller=None) -> str:
    """تحميل الصوت من يوتيوب مع دعم الكوكيز"""
    cookie_file_path = None
    try:
        print(f"📥 جاري تحميل فيديو يوتيوب: {youtube_url}")
        
        # تحديث التقدم
        if progress_callback:
            progress = ProgressState()
            progress.current_stage = "استخراج الصوت"
            progress.stage_details = "جاري تحميل فيديو اليوتيوب..."
            progress_callback(progress)
        
        temp_dir = tempfile.gettempdir()
        
        # ✅ إنشاء ملف كوكيز مؤقت إذا توفر المحتوى
        if cookies_content:
            try:
                cookie_fd, cookie_file_path = tempfile.mkstemp(suffix='.txt', text=True)
                with os.fdopen(cookie_fd, 'w') as f:
                    f.write(cookies_content)
                print(f"🍪 تم استخدام الكوكيز من المدخلات: {cookie_file_path}")
            except Exception as e:
                print(f"⚠️ فشل إنشاء ملف الكوكيز: {e}")
        
        # ✅ Clean up previous files
        try:
            for filename in os.listdir(temp_dir):
                if filename.startswith('youtube_audio_'):
                    try:
                        os.remove(os.path.join(temp_dir, filename))
                    except:
                        pass
        except Exception:
            pass

        # ✅ إعدادات yt-dlp مع دعم الكوكيز
        ydl_opts = {
            # محاولة طلب صيغة m4a مباشرة (غالباً تكون متاحة وسريعة)
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, 'youtube_audio_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,  # ✅ Catch errors explicitly instead of returning None
            'no_check_certificate': True,
            'extractaudio': True,
            'audioformat': 'wav',
            
            # خيارات الشبكة المتقدمة
            'socket_timeout': 30,
            
            # استخدام ملف الكوكيز إن وجد
            'cookiefile': cookie_file_path if cookie_file_path else None,
            
            # 🔧 إعدادات الشبكة لتفادي أخطاء الاتصال (Stream ID Error)
            'concurrent_fragment_downloads': 1,  # منع التحميل المتوازي
            'retries': 10,
            'fragment_retries': 10,
            
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        
        # 🛑 إضافة Progress Hook للإيقاف
        def stop_check_hook(d):
            if controller and hasattr(controller, 'check_stop') and controller.check_stop():
                raise Exception("STOP_REQUESTED")

        if controller:
            ydl_opts['progress_hooks'] = [stop_check_hook]

        # 🛡️ استراتيجية العميل (Client Strategy)
        if cookie_file_path:
            # ✅ إذا وجد كوكيز (من متصفح)، نستخدم عميل الويب العادي لتطابق الجلسة
            print("🍪 استخدام وضع المتصفح الموثق (Auth Mode)")
        else:
            # ❌ بدون كوكيز، نحاول التمويه كـ TV أو Android
            print("🕵️ استخدام وضع التمويه (Anonymous Mode)")
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['tv', 'android', 'web'],
                }
            }
        
        # 🏁 محاولة أولى
        success = False
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if info is None:
                    raise Exception("yt-dlp returned None (Video unavailable or blocked)")
                
                video_title = info.get('title', 'youtube_video')
                video_id = info.get('id', 'unknown')
                video_title = info.get('title', 'youtube_video')
                print(f"🎬 جاري تحميل: {video_title}")
                ydl.download([youtube_url])
                
                # البحث عن الملف المحمل بأي امتداد
                import glob
                possible_files = []
                
                # البحث عن الملفات المحتملة
                for pattern in [
                    f"youtube_audio_{video_id}.wav",
                    f"youtube_audio_{video_id}.m4a",
                    f"youtube_audio_{video_id}.m4a.part",
                    f"youtube_audio_{video_id}.*"
                ]:
                    matches = glob.glob(os.path.join(temp_dir, pattern))
                    possible_files.extend(matches)
                
                # إزالة المكررات والفرز حسب الحجم (الأكبر أولاً)
                possible_files = list(set(possible_files))
                possible_files.sort(key=lambda x: os.path.getsize(x) if os.path.exists(x) else 0, reverse=True)
                
                # البحث عن أول ملف صالح
                for file_path in possible_files:
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        # إذا كان الملف .part، حاول إعادة تسميته
                        if file_path.endswith('.part'):
                            try:
                                new_path = file_path[:-5]  # إزالة .part
                                os.rename(file_path, new_path)
                                file_path = new_path
                                print(f"✅ تمت إعادة تسمية الملف: {file_path}")
                            except Exception as rename_error:
                                print(f"⚠️ فشل إعادة التسمية، سنستخدم الملف كما هو: {rename_error}")
                        
                        print(f"✅ تم تحميل الملف بنجاح: {file_path}")
                        return file_path
                
                # إذا لم نجد أي ملف
                raise Exception(f"ملف الصوت غير موجود. الملفات المتاحة: {possible_files}")

        except Exception as e:
            print(f"⚠️ فشلت المحاولة الأولى (yt-dlp): {e}")
            
            # 🔄 محاولة ثانية: البحث عن أي ملف محمل في المجلد المؤقت
            print("🔍 البحث عن ملفات محملة في المجلد المؤقت...")
            import glob
            recent_audio_files = glob.glob(os.path.join(temp_dir, 'youtube_audio_*'))
            if recent_audio_files:
                # الفرز حسب وقت التعديل (الأحدث أولاً)
                recent_audio_files.sort(key=os.path.getmtime, reverse=True)
                latest_file = recent_audio_files[0]
                if os.path.getsize(latest_file) > 0:
                    print(f"✅ تم العثور على ملف محمل: {latest_file}")
                    return latest_file
            
            # 🔄 محاولة ثالثة: إذا كنا نستخدم كوكيز وفشلت، نجرب الوضع المجهول
            if cookie_file_path:
                print("🔄 الكوكيز ربما تكون معطلة. جاري المحاولة بوضع التمويه (Anonymous Mode)...")
                try:
                    # إعدادات جديدة بدون كوكيز ومع تمويه
                    ydl_opts_anon = ydl_opts.copy()
                    ydl_opts_anon['cookiefile'] = None
                    ydl_opts_anon['extractor_args'] = {
                        'youtube': {
                            'player_client': ['tv', 'android', 'ios'],
                        }
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts_anon) as ydl:
                        ydl.download([youtube_url])
                        # (نفس منطق التحقق من الملف - يمكن تحسين الكود لعدم التكرار لكن للسرعة نكرره)
                        # نحتاج معرف الفيديو مرة أخرى أو نفترض أنه نفسه
                        # للأمان نعيد البحث عن الملفات الحديثة
                        import glob
                        wav_files = sorted(glob.glob(os.path.join(temp_dir, 'youtube_audio_*.wav')), key=os.path.getmtime, reverse=True)
                        if wav_files and os.path.getsize(wav_files[0]) > 0:
                            print(f"✅ نجح التحميل بالوضع المجهول: {wav_files[0]}")
                            return wav_files[0]
                        else:
                             raise Exception("فشل الوضع المجهول أيضاً")

                except Exception as anon_error:
                    print(f"❌ فشل الوضع المجهول: {anon_error}")

            # 🔄 محاولة ثالثة وأخيرة: استخدام pytube
            try:
                print("🔄 فشل yt-dlp تماماً. جاري تجربة pytube كبديل أخير...")
                from pytube import YouTube
                
                yt = YouTube(youtube_url)
                # استخدام الجودة المنخفضة لضمان التحميل
                audio_stream = yt.streams.filter(only_audio=True).first()
                
                if audio_stream:
                    video_path = audio_stream.download(output_path=temp_dir, filename=f"youtube_temp_{yt.video_id}.mp4")
                    print(f"📥 تم التحميل باستخدام pytube: {video_path}")
                    
                    if progress_callback:
                        progress.stage_details = "جاري استخراج الصوت..."
                        progress_callback(progress)
                    
                    audio_path = extract_audio_optimized(video_path, progress_callback)
                    
                    # تنظيف
                    try:
                        os.remove(video_path)
                    except:
                        pass
                    
                    if audio_path and os.path.exists(audio_path):
                        return audio_path
                    else:
                        raise Exception("فشل استخراج الصوت")
                else:
                    raise Exception("لا يوجد تيار صوتي")
                    
            except Exception as pytube_error:
                print(f"❌ فشل pytube أيضاً: {pytube_error}")
                # Raise informative error
                raise Exception(f"فشل جميع محاولات التحميل.\nخطأ المصدر: {str(e)}\nخطأ البديل: {str(pytube_error)}")
    
    # End of function
    
    except Exception as e:
        # Re-raise to let the caller handle it
        raise e


# دوال مساعدة للترجمة (للتوافق مع الإصدارات السابقة)
def split_long_text(text, max_length=4000):
    if len(text) <= max_length:
        return [text]
    
    sentences = text.split('. ')
    parts = []
    current_part = ""
    
    for sentence in sentences:
        if len(current_part + sentence) <= max_length:
            current_part += sentence + ". "
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = sentence + ". "
    
    if current_part:
        parts.append(current_part.strip())
    
    return parts