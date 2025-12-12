"""
مكون واجهة المستخدم لتنسيق النص
"""
import streamlit as st
from businessLogic import format_text_with_sentences, format_with_timestamps, export_as_srt, get_last_segments
from modules.file_processor import translate_to_arabic

def render_text_formatting_options(original_text, segments):
    """عرض خيارات تنسيق النص"""
    if not original_text:
        return
    
    st.subheader("🎨 خيارات التنسيق")
    
    # إذا لم تكن segments موجودة، جرب الحصول عليها من businessLogic
    if not segments:
        segments = get_last_segments()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 تنسيق الجمل", help="كل جملة في سطر منفصل"):
            formatted_text = format_text_with_sentences(original_text)
            st.session_state.formatted_text = formatted_text
            st.session_state.show_formatted = True
    
    with col2:
        if segments and st.button("⏱️ عرض Timestamps", help="عرض الوقت مع كل جملة"):
            timestamped_text = format_with_timestamps(segments)
            st.session_state.timestamped_text = timestamped_text
            st.session_state.show_timestamped = True
    
    with col3:
        # إظهار أزرار SRT إذا كانت segments موجودة
        if segments and len(segments) > 0:
            # زر SRT الأصلي
            srt_content = export_as_srt(segments)
            st.download_button(
                label="📥 SRT أصلي",
                data=srt_content,
                file_name="subtitles.srt",
                mime="text/plain",
                help="ملف ترجمة بالنص الأصلي",
                key="srt_original"
            )
            
            # زر SRT مترجم
            if st.button("🌐 SRT مترجم", help="ترجمة وتحميل SRT بالعربية", key="translate_srt"):
                with st.spinner("جاري ترجمة segments..."):
                    # ترجمة كل segment
                    controller = st.session_state.get('controller')
                    translated_segments = []
                    
                    for segment in segments:
                        translated_text = translate_to_arabic(segment['text'], controller)
                        translated_segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': translated_text
                        })
                    
                    # حفظ في session_state
                    st.session_state.translated_segments = translated_segments
                    st.session_state.show_srt_download = True
            
            # عرض زر التحميل بعد الترجمة
            if st.session_state.get('show_srt_download', False):
                srt_arabic = export_as_srt(st.session_state.translated_segments)
                st.download_button(
                    label="💾 تحميل SRT عربي",
                    data=srt_arabic,
                    file_name="subtitles_arabic.srt",
                    mime="text/plain",
                    help="ملف ترجمة بالعربية",
                    key="srt_arabic_download"
                )
        else:
            st.info("⏱️ Timestamps غير متاحة")
    
    # عرض النص المنسق
    if st.session_state.get('show_formatted', False):
        st.markdown("### 📝 النص المنسق (جملة لكل سطر)")
        
        # خيار ترجمة النص المنسق
        col_a, col_b = st.columns([3, 1])
        with col_b:
            if st.button("🌐 ترجمة المنسق", key="translate_formatted"):
                with st.spinner("جاري ترجمة النص المنسق..."):
                    # استخدام controller من session_state
                    controller = st.session_state.get('controller')
                    translated_formatted = translate_to_arabic(
                        st.session_state.formatted_text,
                        controller
                    )
                    st.session_state.formatted_text_ar = translated_formatted
        
        # عرض النص (مترجم أو أصلي)
        text_to_show = st.session_state.get('formatted_text_ar', st.session_state.formatted_text)
        st.text_area("", text_to_show, height=300, key="formatted_display")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "💾 تحميل النص المنسق",
                st.session_state.formatted_text,
                file_name="formatted_text.txt",
                mime="text/plain"
            )
        with col2:
            if 'formatted_text_ar' in st.session_state:
                st.download_button(
                    "💾 تحميل المترجم",
                    st.session_state.formatted_text_ar,
                    file_name="formatted_text_arabic.txt",
                    mime="text/plain"
                )
    
    if st.session_state.get('show_timestamped', False):
        st.markdown("### ⏱️ النص مع Timestamps")
        st.text_area("", st.session_state.timestamped_text, height=300, key="timestamped_display")
        st.download_button(
            "💾 تحميل مع Timestamps",
            st.session_state.timestamped_text,
            file_name="text_with_timestamps.txt",
            mime="text/plain"
        )
