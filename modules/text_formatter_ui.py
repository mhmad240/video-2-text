"""
مكون واجهة المستخدم لتنسيق النص
"""
import streamlit as st
from businessLogic import format_text_with_sentences, format_with_timestamps, export_as_srt

def render_text_formatting_options(original_text, segments):
    """عرض خيارات تنسيق النص"""
    if not original_text:
        return
    
    st.subheader("🎨 خيارات التنسيق")
    
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
        if segments:
            srt_content = export_as_srt(segments)
            st.download_button(
                label="📥 تحميل SRT",
                data=srt_content,
                file_name="subtitles.srt",
                mime="text/plain",
                help="ملف ترجمة للفيديو"
            )
    
    # عرض النص المنسق
    if st.session_state.get('show_formatted', False):
        st.markdown("### 📝 النص المنسق (جملة لكل سطر)")
        st.text_area("", st.session_state.formatted_text, height=300, key="formatted_display")
        st.download_button(
            "💾 تحميل النص المنسق",
            st.session_state.formatted_text,
            file_name="formatted_text.txt",
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
