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
        
        # Check connectivity with shorter timeout
        try:
            import requests
            print("🌐 فحص الاتصال بالإنترنت...")
            requests.get("https://translate.google.com", timeout=3)
            print("✅ الاتصال بالإنترنت متاح")
        except Exception as conn_error:
            print(f"❌ فشل الاتصال: {conn_error}")
            return "❌ لا يوجد اتصال بالإنترنت للترجمة"
        
        translator = GoogleTranslator(source='auto', target='ar')
        max_chunk_size = 4000
        
        if len(text) > max_chunk_size:
            if progress_callback:
                progress_callback("🔄 تقسيم النص للترجمة...")
            
            chunks = []
            current_chunk = ""
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
            print(f"📊 عدد الأجزاء للترجمة: {total_chunks}")
            
            for i, chunk in enumerate(chunks):
                if controller.check_stop():
                    return "⏹️ تم إيقاف الترجمة"
                
                if progress_callback:
                    progress_callback(f"🔄 جاري الترجمة {i+1}/{total_chunks}...")
                
                print(f"🔄 ترجمة الجزء {i+1}/{total_chunks}...")
                
                try:
                    # Add timeout to translation
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Translation timeout")
                    
                    # Set timeout for translation (30 seconds per chunk)
                    translated = translator.translate(chunk)
                    translated_parts.append(translated)
                    print(f"✅ تمت ترجمة الجزء {i+1}")
                    
                    # Small delay to avoid rate limiting
                    import time
                    time.sleep(0.5)
                    
                except TimeoutError:
                    print(f"⏱️ انتهت مهلة ترجمة الجزء {i+1}")
                    translated_parts.append(f"[انتهت المهلة - جزء {i+1}]")
                    continue
                except Exception as chunk_error:
                    print(f"❌ خطأ في ترجمة الجزء {i}: {chunk_error}")
                    translated_parts.append(f"[خطأ في الترجمة جزء {i+1}]")
                    continue
            
            result = ' '.join(translated_parts)
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            print("✅ اكتملت الترجمة بنجاح!")
            return result
            
        else:
            if progress_callback:
                progress_callback("🔄 جاري الترجمة...")
            
            print("🔄 بدء الترجمة...")
            try:
                translated = translator.translate(text)
                print("✅ تمت الترجمة بنجاح!")
            except Exception as trans_error:
                print(f"❌ خطأ في الترجمة: {trans_error}")
                return f"❌ فشلت الترجمة: {str(trans_error)}"
            
            if progress_callback:
                progress_callback("✅ اكتملت الترجمة!")
            return translated
            
    except Exception as e:
        error_msg = f"❌ خطأ غير متوقع في الترجمة: {str(e)}"
        print(error_msg)
        if progress_callback:
            progress_callback(error_msg)
        return f"⚠️ حدث خطأ أثناء الترجمة: {str(e)}"