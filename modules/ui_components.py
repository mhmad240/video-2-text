import streamlit as st

def display_progress_indicator(process_running, progress_state, current_progress, current_stage, stage_details):
    """عرض مؤشر التقدم بشكل تفاعلي"""
    if not process_running:
        return
    
    # عرض شريط التقدم الرئيسي
    st.progress(current_progress / 100)
    
    # عرض تفاصيل المرحلة الحالية
    col1, col2 = st.columns([3, 1])
    with col1:
        if current_stage:
            st.markdown(f"**{current_stage}**")
        if stage_details:
            st.write(f"📝 {stage_details}")
    
    with col2:
        st.markdown(f"**{current_progress}%**")
    
    # عرض رسالة الخطأ إذا وجدت
    if progress_state and progress_state.error:
        st.error(f"❌ {progress_state.error}")
    
    # عرض رسالة الإكمال
    if progress_state and progress_state.is_completed:
        st.success("✅ تم الانتهاء بنجاح!")
    
    st.markdown("---")

def display_results(original_text, translated_text, translating, controller):
    """عرض النتائج وأزرار التحميل"""
    if not original_text:
        return False
        
    st.subheader("📝 النتائج")
    
    # متغير لتتبع طلب الترجمة
    translate_requested = False
    
    # تبويبات للتنقل بين النتائج
    tab1, tab2, tab3 = st.tabs(["النص الأصلي", "الترجمة العربية", "🎨 خيارات التنسيق"])
    
    with tab1:
        st.text_area("النص المستخرج:", original_text, height=300, key="original_display")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 تحميل النص الأصلي",
                data=original_text,
                file_name="النص_الأصلي.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            translate_disabled = bool(translating or translated_text is not None)
            
            if st.button("🌐 ترجمة إلى العربية", 
                       type="secondary", 
                       disabled=translate_disabled,
                       use_container_width=True,
                       key="translate_btn"):
                translate_requested = True
    
    with tab2:
        if translated_text:
            st.text_area("الترجمة العربية:", translated_text, height=300, key="translated_display")
            
            st.download_button(
                label="📥 تحميل النص المترجم",
                data=translated_text,
                file_name="النص_المترجم_عربي.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.success(f"✅ تمت ترجمة {len(translated_text.split())} كلمة بنجاح!")
        else:
            if translating:
                st.info("🔄 جاري الترجمة... يرجى الانتظار")
            else:
                st.info("🌐 استخدم زر 'ترجمة إلى العربية' في تبويب النص الأصلي لبدء الترجمة")
    
    with tab3:
        # عرض خيارات التنسيق
        from modules.text_formatter_ui import render_text_formatting_options
        segments = st.session_state.get('segments', [])
        render_text_formatting_options(original_text, segments)
    
    return translate_requested

def render_about_tab():
    """عرض تبويب عن التطبيق"""
    st.header("ℹ️ عن تطبيق Video2Text")
    
    st.markdown("""
    ### 🎥 Video2Text
    
    **تطبيق متكامل لتحويل الفيديو إلى نص باستخدام الذكاء الاصطناعي المتقدم**
    
    ---
    
    ### ✨ المميزات:
    - 🔄 تحويل الفيديوهات المحلية إلى نص
    - 🌐 تحويل الفيديوهات من الإنترنت إلى نص
      - ✅ **يوتيوب** (YouTube)
      - ✅ **فيسبوك** (Facebook)
      - ✅ **يودمي** (Udemy) - مع دعم الكوكيز للفيديوهات المدفوعة
      - ✅ **فيميو** (Vimeo)
      - ✅ **تويتر/X** (Twitter/X)
      - ✅ **تيك توك** (TikTok)
      - ✅ **انستغرام** (Instagram)
      - ✅ **أكثر من 1000 موقع آخر** عبر yt-dlp
    - 🌐 ترجمة النص إلى العربية
    - 💾 تحميل النتائج كملفات نصية
    - ⚡ **Faster-Whisper** - أسرع 4x من النسخة العادية
    - 🤖 **تحميل ذكي** - النموذج يحمل مرة واحدة فقط
    - 🎯 **تحسين تلقائي** - اكتشاف GPU/CPU مع إعدادات مثلى
    - ⏹️ إمكانية إيقاف العملية في أي وقت
    - 📊 متابعة التقدم خطوة بخطوة
    
    ### 🎨 **ميزات التنسيق الجديدة:**
    - 📝 **تنسيق الجمل** - كل جملة في سطر منفصل
    - ⏱️ **Timestamps** - عرض الوقت مع كل segment
    - 📥 **تصدير SRT** - ملف ترجمة للفيديو
    - 🌐 **ترجمة النص المنسق** - ترجمة النص المنسق إلى العربية
    
    ---
    
    ### 🛠️ التقنيات المستخدمة:
    - **Faster-Whisper** - تحويل الصوت إلى نص (مُسرع)
    - **CTranslate2** - محرك تسريع الذكاء الاصطناعي
    - **Streamlit** - واجهة المستخدم
    - **FFmpeg** - معالجة الفيديوهات
    - **Deep Translator** - الترجمة الآمنة
    
    ---
    
    ### 🔒 التحديثات الأمنية:
    - ✅ **Streamlit 1.51.0** - إصلاح ثغرات أمنية
    - ✅ **PyTorch 2.9.1** - أحدث إصدار آمن
    - ✅ **تحديثات أمنية شاملة** - إصلاح 7+ ثغرات
    
    ---
    
    ### 👨‍💻 المطور:
    **Muhammed ElOmer**  
    مبرمج ومطور تطبيقات الذكاء الاصطناعي
    """)

def render_file_upload_section():
    """عرض قسم رفع الملف"""
    st.subheader("📁 رفع ملف فيديو محلي")
    uploaded_file = st.file_uploader(
        "اسحب وأفلت الملف هنا", 
        type=['mp4', 'avi', 'mov', 'mkv', 'mpeg4'],
        label_visibility="collapsed",
        help="Limit 800 MB per file • MP4, AVI, MOV, MKV, MPEG4",
        key="file_uploader"
    )
    
    
    # عرض معلومات الحجم إذا كان الملف كبيراً
    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 500:
            st.info(f"📏 حجم الملف: {file_size_mb:.1f} MB - يوصى باستخدام نموذج سريع مثل 'tiny' أو 'base'")
    
    return uploaded_file

def render_youtube_section():
    """عرض قسم رابط الفيديو من الإنترنت"""
    st.subheader("🔗 رابط فيديو من الإنترنت")
    url = st.text_input(
        "أدخل رابط الفيديو (يوتيوب، فيسبوك، يودمي، فيميو، وغيرها):", 
        label_visibility="collapsed", 
        key="youtube_url",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    cookies = None
    
    # 🔐 التحقق من وجود كوكيز في الأسرار (Secrets)
    secret_cookies = None
    try:
        if "YOUTUBE_COOKIES" in st.secrets:
            secret_cookies = st.secrets["YOUTUBE_COOKIES"]
    except:
        pass

    with st.expander("🍪 إعدادات متقدمة (لمشاكل التحميل)"):
        if secret_cookies:
            st.success("🔒 تم اكتشاف كوكيز مخزنة في الأسرار (Secrets) وسيتم استخدامها تلقائياً.")
            st.info("يمكنك تجاوزها بإدخال كوكيز جديدة أدناه:")
        
        st.write("إذا فشل التحميل بسبب الحظر (403/Sign in)، قم بإضافة ملفات تعريف الارتباط (Cookies) هنا.")
        manual_cookies = st.text_area(
            "الصق محتوى Netscape Cookies هنا:", 
            placeholder="# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/..." if not secret_cookies else "تم استخدام الكوكيز من الأسرار (اترك هذا فارغاً للاستخدام الافتراضي)",
            height=150
        )
        st.info("💡 يمكنك استخدام إضافة 'Get cookies.txt LOCALLY' للمتصفح للحصول عليها.")
    
    # استخدام المدخل اليدوي أولاً، ثم الأسرار
    cookies = manual_cookies if manual_cookies.strip() else secret_cookies
        
    return url, cookies

def render_model_selection():
    """عرض اختيار النموذج"""
    models = ["tiny", "base", "small", "medium", "large"]
    # جعل Small هو الافتراضي (index=2) - توازن ممتاز بين السرعة والجودة
    model = st.selectbox("اختر نموذج التحويل:", models, index=2)
    return model


def render_control_buttons(process_running, stop_requested, has_file_or_url, cached_model, reset_callback=None):
    """عرض أزرار التحكم"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_disabled = process_running or (not has_file_or_url) or cached_model is None
        if st.button("▶️ بدء التحويل", type="primary", disabled=start_disabled, use_container_width=True):
            return "start"
    
    with col2:
        stop_disabled = not process_running or stop_requested
        if st.button("⏹️ إيقاف فوري", type="secondary", disabled=stop_disabled, use_container_width=True):
            return "stop"
    
    with col3:
        # ✅ استخدام callback لتنظيف الحالة قبل إعادة التشغيل
        st.button("🔄 جلسة جديدة", type="secondary", use_container_width=True, on_click=reset_callback)
    
    return None