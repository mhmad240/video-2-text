import streamlit as st
import tempfile
import os
import time
import sys

# Force UTF-8 encoding check removed for Streamlit Cloud compatibility
# Streamlit handles encoding internally

# ✅ إعداد السجلات لتظهر فوراً في Streamlit Cloud
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
# فرض تحديث السجلات فوراً
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

# استبدال الطباعة العادية بالطباعة مع فرض التحديث
_original_print = print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _original_print(*args, **kwargs)


# إضافة مسار مجلد modules يدوياً
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.join(current_dir, 'modules')
sys.path.insert(0, modules_path)

# استيراد الوحدات الجديدة من المسار المباشر - محدث
from device_manager import get_device_info, setup_cuda_environment
from model_loader import load_whisper_model
from file_processor import ProcessController, process_uploaded_file, process_youtube_url, translate_to_arabic
from ui_components import (
    display_progress_indicator, display_results, render_about_tab,
    render_file_upload_section, render_youtube_section, 
    render_model_selection, render_control_buttons
)
from businessLogic import ProgressState

# ✅ إعداد بيئة CUDA و cuDNN (مع cache - لا رسائل متكررة)
cudnn_available, paths_added = setup_cuda_environment()

# ✅ إعداد جهاز الحساب (مع cache - لا رسائل متكررة)
# Note: The original code calls get_device_info() inside main().
# If setup_compute_device() is a new function, it needs to be defined.
# Assuming the intent is to remove the print statements related to CUDA setup
# and potentially move device info acquisition here if setup_compute_device()
# is meant to replace the existing logic.
# For now, I'm keeping the original get_device_info() call in main()
# and only applying the explicit changes requested.
# The line '"ℹ️ النظام يعمل على CPU بكفاءة عالية")' is syntactically incorrect
# and appears to be a remnant of a print statement, so it's removed.

# تهيئة حالة الجلسة
def initialize_session_state():
    """تهيئة جميع متغيرات الجلسة"""
    session_defaults = {
        'original_text': None,
        'translated_text': None,
        'segments': [],  # لحفظ segments مع timestamps
        'process_running': False,
        'process_stopped': False,
        'stop_requested': False,
        'progress_state': None,
        'current_progress': 0,
        'current_stage': "",
        'stage_details': "",
        'translating': False,
        'controller': ProcessController(),
        'device_info': None
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def progress_callback(progress_state):
    """دالة callback لتحديث حالة التقدم"""
    st.session_state.progress_state = progress_state
    st.session_state.current_progress = progress_state.progress
    st.session_state.current_stage = progress_state.current_stage
    st.session_state.stage_details = progress_state.stage_details

def translation_progress_callback(message):
    """دالة callback خاصة بالترجمة"""
    st.session_state.current_stage = "ترجمة"
    st.session_state.stage_details = message

# ... (Keep previous imports)

def start_processing(uploaded_file, url, model, cached_model, device_info, cookies=None):  # ✅ إضافة cookies
    """بدء عملية التحويل باستخدام النموذج المخبأ"""
    st.session_state.process_running = True
    # ... (Keep existing state resets) ...
    st.session_state.process_stopped = False
    st.session_state.stop_requested = False
    st.session_state.controller.should_stop = False
    st.session_state.progress_state = None
    st.session_state.current_progress = 0
    st.session_state.current_stage = ""
    st.session_state.stage_details = ""
    st.session_state.translating = False
    
    # استخدام النموذج المخبأ بدلاً من تحميل جديد
    if cached_model is None:
        st.error("❌ النموذج غير محمل - يرجى المحاولة مرة أخرى")
        st.session_state.process_running = False
        return
    
    # تشغيل المعالجة مباشرة
    if uploaded_file:
        original_text, message = process_uploaded_file(
            uploaded_file, cached_model, device_info,
            progress_callback, st.session_state.controller
        )
        st.session_state.original_text = original_text
        if message:
            if "✅" in message:
                st.success(message)
            elif "❌" in message:
                st.error(message)
    elif url:
        original_text, message = process_youtube_url(
            url, cached_model, device_info,
            progress_callback, st.session_state.controller,
            cookies=cookies  # ✅ تمرير Cookies
        )
        st.session_state.original_text = original_text
        if message:
            if "✅" in message:
                st.success(message)
            elif "❌" in message:
                st.error(message)
    
    # تحديث نهائي واحد فقط عند الانتهاء
    st.session_state.process_running = False
    st.rerun()

def stop_processing():
    """طلب إيقاف المعالجة"""
    st.session_state.stop_requested = True
    st.session_state.controller.stop()
    st.warning("⚠️ جاري الإيقاف... يرجى الانتظار")
    # لا نقوم بـ rerun هنا للسماح للكود بالتحقق من العلم

def reset_session():
    """إعادة تعيين الجلسة بالكامل"""
    # الاحتفاظ بالنموذج المخبأ فقط
    st.session_state.original_text = None
    st.session_state.translated_text = None
    st.session_state.process_running = False
    st.session_state.process_stopped = False
    st.session_state.stop_requested = False
    st.session_state.progress_state = None
    st.session_state.current_progress = 0
    st.session_state.current_stage = ""
    st.session_state.stage_details = ""
    st.session_state.translating = False
    st.session_state.controller = ProcessController()
    
    # ✅ تنظيف المدخلات (بفضل استخدام keys في ui_components)
    if "youtube_url" in st.session_state:
        st.session_state["youtube_url"] = ""
    if "file_uploader" in st.session_state:
        # Streamlit resets file_uploader if the key is removed
        del st.session_state["file_uploader"]
        
    # st.rerun() removed - not needed in callback context as Streamlit reruns automatically

def main():
    st.title("🎥 Video2Text - تحويل الفيديو إلى نص")
    
    # ... (Keep device info logic) ...
    
    # الحصول على معلومات الجهاز مرات واحدة فقط
    if st.session_state.device_info is None:
        st.session_state.device_info = get_device_info()
    
    device_info = st.session_state.device_info

    # ... (Keep expander) ...
    with st.expander("ℹ️ معلومات النظام والأداء", expanded=False):
        st.write(f"**{device_info['icon']} وضع التشغيل:** {device_info['reason']}")
        st.write(f"**💡 نصيحة الأداء:** {device_info['performance_tip']}")
        st.write(f"**🎯 النماذج الموصى بها:** {', '.join(device_info['recommended_models'])}")
        st.write(f"**⚡ نوع الحساب:** {device_info['compute_type']}")
        st.write("**💾 المزايا:** ⚡ أسرع 4x | 💾 ذاكرة أقل | 🔄 تحميل فوري")
        
        # عرض حالة cuDNN إذا كان GPU مفعل
        if device_info['device'] == 'cuda':
            st.success("✅ GPU مفعل مع cuDNN - سرعة محسنة!")
        elif "cuDNN" in device_info['reason']:
            st.warning("🚫 قم بتثبيت cuDNN لتفعيل GPU")
        else:
            st.info("💻 CPU مع INT8 - أداء متوازن")

    # تبويبات التنقل
    tab1, tab2 = st.tabs(["🔄 تحويل الفيديو", "ℹ️ عن التطبيق"])
    
    with tab1:
        # ... (Keep update button) ...
        if st.session_state.process_running:
            if st.button("🔄 تحديث الواجهة", type="secondary"):
                st.rerun()
        
        # ... (Keep progress) ...
        if st.session_state.process_running:
            st.subheader("📊 حالة التقدم")
            display_progress_indicator(
                st.session_state.process_running,
                st.session_state.progress_state,
                st.session_state.current_progress,
                st.session_state.current_stage,
                st.session_state.stage_details
            )
            
            if st.session_state.stop_requested:
                st.error("🛑 جاري إيقاف العملية...")
        
        st.write("يمكنك رفع ملف فيديو محلي أو إدخال رابط يوتيوب")
        
        # استخدام المكونات الجديدة
        uploaded_file = render_file_upload_section()
        url, cookies = render_youtube_section()  # ✅ استلام cookies
        model = render_model_selection()
        
        # تحميل النموذج المخبأ عند اختيار النموذج
        cached_model = load_whisper_model(model, device_info)
        
        # ... (Keep large file warning) ...
        if uploaded_file and (uploaded_file.size / (1024 * 1024)) > 500:
            st.write("💡 **للتحويل السريع**: اختر `tiny` أو `base` - **للجودة العالية**: اختر `small` أو `medium`")
        else:
            st.write("النماذج الأصغر أسرع ولكن أقل دقة، النماذج الأكبر أبطأ ولكن أكثر دقة")
        
        # أزرار التحكم الرئيسية
        has_file_or_url = uploaded_file or url
        button_action = render_control_buttons(
            st.session_state.process_running,
            st.session_state.stop_requested,
            has_file_or_url,
            cached_model,
            reset_callback=reset_session  # ✅ تمرير دالة التنظيف مباشرة
        )
        
        if button_action == "start":
            start_processing(uploaded_file, url, model, cached_model, device_info, cookies)  # ✅ تمرير cookies
        elif button_action == "stop":
            stop_processing()
        # elif button_action == "reset":  <-- Removed, handled by callback
        
        # عرض النتائج إذا كانت موجودة
        if st.session_state.original_text:
            translate_requested = display_results(
                st.session_state.original_text,
                st.session_state.translated_text,
                st.session_state.translating,
                st.session_state.controller
            )
            
            if translate_requested:
                st.session_state.translating = True
                try:
                    import gc
                    gc.collect()  # 🧹 تنظيف الذاكرة قبل الترجمة تفادياً لامتلاء الرام
                    
                    with st.spinner("جاري الترجمة... قد تستغرق بضع ثوانٍ"):
                        st.session_state.translated_text = translate_to_arabic(
                            st.session_state.original_text, 
                            st.session_state.controller,
                            translation_progress_callback  # ✅ إضافة progress_callback
                        )
                except Exception as e:
                    st.error(f"❌ حدث خطأ في الترجمة: {e}")
                finally:
                    st.session_state.translating = False
                st.rerun()
        
        # قسم المساعدة للفيديوهات الكبيرة
        if uploaded_file and (uploaded_file.size / (1024 * 1024)) > 500:
            with st.expander("💡 نصائح للفيديوهات الكبيرة"):
                st.write("""
                **للفيديوهات الأكبر من 500 MB:**
                
                - 🚀 **للسرعة**: استخدم `tiny` أو `base`
                - ⚡ **للتوازن**: استخدم `small` 
                - 🐌 **للدقة**: استخدم `medium` (بطيء جداً)
                - ❌ **تجنب**: `large` (قد يفشل لاستهلاك الذاكرة)
                
                **مراحل التحويل:**
                1. 🎵 استخراج الصوت من الفيديو (25%)
                2. 🤖 استخدام النموذج المخبأ (0%) - ⚡ فوري  
                3. 📝 تحويل الصوت إلى نص (75%)
                4. ✅ الانتهاء والمعالجة (100%)
                
                **ملاحظة:** يمكنك إيقاف العملية في أي وقت باستخدام زر ⏹️
                """)
    
    with tab2:
        render_about_tab()
    
    # قسم حقوق الملكية
    st.markdown("---")
    st.markdown("**© 2025 Video2Text - تم التطوير بواسطة Muhammed ElOmer**")

if __name__ == "__main__":
    initialize_session_state()
    main()