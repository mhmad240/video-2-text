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
    tab1, tab2 = st.tabs(["النص الأصلي", "الترجمة العربية"])
    
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
                translate_requested = True  # إشارة لبدء الترجمة
    
    with tab2:
        if translated_text:
            # ✅ عرض النص المترجم بشكل واضح
            st.text_area("الترجمة العربية:", translated_text, height=300, key="translated_display")
            
            # ✅ زر تحميل النص المترجم
            st.download_button(
                label="📥 تحميل النص المترجم",
                data=translated_text,
                file_name="النص_المترجم_عربي.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # ✅ عرض معلومات عن الترجمة
            st.success(f"✅ تمت ترجمة {len(translated_text.split())} كلمة بنجاح!")
        else:
            if translating:
                st.info("🔄 جاري الترجمة... يرجى الانتظار")
            else:
                st.info("🌐 استخدم زر 'ترجمة إلى العربية' في تبويب النص الأصلي لبدء الترجمة")
    
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
    - 🌐 تحويل فيديوهات اليوتيوب إلى نص  
    - 🌐 ترجمة النص إلى العربية
    - 💾 تحميل النتائج كملفات نصية
    - ⚡ **Faster-Whisper** - أسرع 4x من النسخة العادية
    - 🤖 **تحميل ذكي** - النموذج يحمل مرة واحدة فقط
    - 🎯 **تحسين تلقائي** - اكتشاف GPU/CPU مع إعدادات مثلى
    - ⏹️ إمكانية إيقاف العملية في أي وقت
    - 📊 متابعة التقدم خطوة بخطوة
    
    ---
    
    ### 🛠️ التقنيات المستخدمة:
    - **Faster-Whisper** - تحويل الصوت إلى نص (مُسرع)
    - **CTranslate2** - محرك تسريع الذكاء الاصطناعي
    - **Streamlit** - واجهة المستخدم
    - **FFmpeg** - معالجة الفيديوهات
    - **Translators** - الترجمة الآمنة
    
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
        help="Limit 800 MB per file • MP4, AVI, MOV, MKV, MPEG4"
    )
    
    # عرض معلومات الحجم إذا كان الملف كبيراً
    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 500:
            st.info(f"📏 حجم الملف: {file_size_mb:.1f} MB - يوصى باستخدام نموذج سريع مثل 'tiny' أو 'base'")
    
    return uploaded_file

def render_youtube_section():
    """عرض قسم رابط يوتيوب"""
    st.subheader("🔗 رابط يوتيوب")
    url = st.text_input("أدخل رابط يوتيوب:", label_visibility="collapsed")
    return url

def render_model_selection():
    """عرض اختيار النموذج"""
    models = ["tiny", "base", "small", "medium", "large"]
    model = st.selectbox("اختر نموذج التحويل:", models)
    return model

def render_control_buttons(process_running, stop_requested, has_file_or_url, cached_model):
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
        if st.button("🔄 جلسة جديدة", type="secondary", use_container_width=True):
            return "reset"
    
    return None