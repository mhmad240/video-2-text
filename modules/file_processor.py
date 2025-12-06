import tempfile
import os
import streamlit as st
from businessLogic import transcribe_audio_optimized

class ProcessController:
    def __init__(self):
        self.should_stop = False
    
    def request_stop(self):
        self.should_stop = True
    
    def check_stop(self):
        return self.should_stop

def process_uploaded_file(uploaded_file, model, device_info, progress_callback, controller):
    """معالجة الملف المرفوع باستخدام النموذج المخبأ"""
    file_size_mb = uploaded_file.size / (1024 * 1024)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_video_path = tmp_file.name
    
    try:
        if controller.check_stop():
            return None, "⏹️ تم إيقاف العملية"

        original_text = transcribe_audio_optimized(
            temp_video_path, 
            model,
            device_info,
            progress_callback
        )
        
        if not controller.check_stop():
            if original_text and not original_text.startswith("❌ Error"):
                return original_text, "✅ تم تحويل الفيديو إلى نص بنجاح!"
            else:
                return f"❌ Error: {original_text}", "❌ فشل تحويل الفيديو إلى نص"
        else:
            return None, "⏹️ تم إيقاف العملية"
                
    except Exception as e:
        return f"❌ Exception: {str(e)}", f"❌ حدث خطأ: {str(e)}"
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except:
                pass

def process_youtube_url(url, model, device_info, progress_callback, controller):
    """معالجة رابط يوتيوب باستخدام النموذج المخبأ"""
    try:
        if controller.check_stop():
            return None, "⏹️ تم إيقاف العملية"

        original_text = transcribe_audio_optimized(
            url, 
            model,
            device_info,
            progress_callback
        )
        
        if not controller.check_stop():
            if original_text and not original_text.startswith("❌ Error"):
                return original_text, "✅ تم تحويل الفيديو إلى نص بنجاح!"
            else:
                return f"❌ Error: {original_text}", "❌ فشل تحويل الفيديو إلى نص"
        else:
            return None, "⏹️ تم إيقاف العملية"
                
    except Exception as e:
        return f"❌ Exception: {str(e)}", f"❌ حدث خطأ: {str(e)}"

def translate_to_arabic(text, controller, progress_callback=None):
    """ترجمة النص إلى العربية باستخدام translators مع معالجة أخطاء محسنة"""
    try:
        if controller.check_stop():
            return "⏹️ تم إيقاف الترجمة"
            
        if not text or text.strip() == "":
            return "⚠️ لا يوجد نص للترجمة"
        
        try:
            import translators as ts
        except ImportError:
            return "❌ مكتبة الترجمة غير مثبتة. الرجاء تثبيت: pip install translators"
        
        try:
            import requests
            requests.get("https://translate.google.com", timeout=5)
        except:
            return "❌ لا يوجد اتصال بالإنترنت للترجمة"
        
        max_chunk_size = 3000
        if len(text) > max_chunk_size:
            if progress_callback:
                progress_callback("🔄 تقسيم النص للترجمة...")
            
            chunks = []
            current_chunk = ""
            
            for sentence in text.split('.'):
                if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                    current_chunk += sentence + '.'
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence + '.'
            
            if current_chunk:
                chunks.append(current_chunk)
            
            translated_parts = []
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                if controller.check_stop():
                    return "⏹️ تم إيقاف الترجمة"
                
                if progress_callback:
                    progress_callback(f"🔄 جاري الترجمة {i+1}/{total_chunks}...")
                
                try:
                    translated = ts.translate_text(
                        chunk, 
                        translator='google', 
                        to_language='ar',
                        timeout=10
                    )
                    translated_parts.append(translated)
                    
                except Exception as chunk_error:
                    translated_parts.append(f"[ترجمة غير متوفرة: {chunk}]")
                    continue
            
            result = ' '.join(translated_parts)
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            return result
            
        else:
            if progress_callback:
                progress_callback("🔄 جاري الترجمة...")
            
            translated = ts.translate_text(
                text, 
                translator='google', 
                to_language='ar',
                timeout=10
            )
            
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            return translated
            
    except Exception as e:
        error_msg = f"❌ خطأ في الترجمة: {str(e)}"
        if progress_callback:
            progress_callback(error_msg)
        return f"⚠️ النص الأصلي ({error_msg}): {text[:100]}..."