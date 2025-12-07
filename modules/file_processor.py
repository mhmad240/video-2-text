import tempfile
import os
import streamlit as st
from businessLogic import transcribe_audio_optimized

class ProcessController:
    def __init__(self):
        self.should_stop = False
    
    def request_stop(self):
        self.should_stop = True

    def stop(self):
        """Alias for request_stop to match app.py usage"""
        self.request_stop()
    
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

def process_youtube_url(url, model, device_info, progress_callback, controller, cookies=None):
    """معالجة رابط يوتيوب باستخدام النموذج المخبأ"""
    try:
        if controller.check_stop():
            return None, "⏹️ تم إيقاف العملية"

        original_text = transcribe_audio_optimized(
            url, 
            model,
            device_info,
            progress_callback,
            cookies=cookies  # ✅ تمرير الكوكيز
        )
        
        if not controller.check_stop():
            if original_text and not original_text.startswith("❌"):
                return original_text, "✅ تم تحويل الفيديو إلى نص بنجاح!"
            else:
                # Avoid double prefixing
                error_msg = original_text if original_text.startswith("❌") else f"❌ Error: {original_text}"
                return error_msg, "❌ فشل تحويل الفيديو إلى نص"
        else:
            return None, "⏹️ تم إيقاف العملية"
                
    except Exception as e:
        return f"❌ Exception: {str(e)}", f"❌ حدث خطأ: {str(e)}"

def translate_to_arabic(text, controller, progress_callback=None):
    """ترجمة النص إلى العربية باستخدام deep-translator (أكثر استقراراً)"""
    try:
        if controller.check_stop():
            return "⏹️ تم إيقاف الترجمة"
            
        if not text or text.strip() == "":
            return "⚠️ لا يوجد نص للترجمة"
        
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            return "❌ مكتبة deep-translator غير مثبتة."
        
        # Check connectivity
        try:
            import requests
            requests.get("https://translate.google.com", timeout=5)
        except:
            return "❌ لا يوجد اتصال بالإنترنت للترجمة"
        
        translator = GoogleTranslator(source='auto', target='ar')
        max_chunk_size = 4000  # Deep translator handles larger chunks better
        
        if len(text) > max_chunk_size:
            if progress_callback:
                progress_callback("🔄 تقسيم النص للترجمة...")
            
            # Simple chunking by newline or period
            chunks = []
            current_chunk = ""
            
            # Better splitting logic
            paragraphs = text.replace('\n', ' \n ').split(' ')
            
            for word in paragraphs:
                if len(current_chunk) + len(word) + 1 <= max_chunk_size:
                    current_chunk += word + " "
                else:
                    chunks.append(current_chunk)
                    current_chunk = word + " "
            
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
                    translated = translator.translate(chunk)
                    translated_parts.append(translated)
                    # Small delay to avoid rate limiting
                    import time
                    time.sleep(0.5)
                    
                except Exception as chunk_error:
                    print(f"Translation error on chunk {i}: {chunk_error}")
                    translated_parts.append(f"[خطأ في الترجمة جزء {i+1}]")
                    continue
            
            result = ' '.join(translated_parts)
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            return result
            
        else:
            if progress_callback:
                progress_callback("🔄 جاري الترجمة...")
            
            translated = translator.translate(text)
            
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            return translated
            
    except Exception as e:
        error_msg = f"❌ خطأ غير متوقع في الترجمة: {str(e)}"
        print(error_msg)
        if progress_callback:
            progress_callback(error_msg)
        return f"⚠️ حدث خطأ أثناء الترجمة: {str(e)}"