import streamlit as st
import json
import os
from datetime import datetime
from PIL import Image
import uuid
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="토평고등학교 분실물 찾기",
    page_icon="🔍",
    layout="wide"
)

# 디렉토리 생성
os.makedirs("data", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

DATA_FILE = "data/lost_items.json"
ITEMS_PER_PAGE = 10

def load_data():
    """데이터 로드"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    """데이터 저장"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"서버에 문제가 발생했습니다. 다시 시도해주세요: {str(e)}")
        return False

def save_image(uploaded_file):
    """이미지 저장"""
    try:
        # 파일 크기 제한 (5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return None, "파일 크기는 5MB를 초과할 수 없습니다."
        
        # 파일 확장자 확인
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            return None, "지원하는 이미지 형식은 jpg, jpeg, png, gif입니다."
        
        # 고유한 파일명 생성
        file_id = str(uuid.uuid4())
        file_path = f"uploads/{file_id}.{file_extension}"
        
        # 이미지 저장
        image = Image.open(uploaded_file)
        image.save(file_path)
        
        return file_path, None
    except Exception as e:
        return None, f"파일 업로드에 실패했습니다: {str(e)}"

def delete_image(image_path):
    """이미지 삭제"""
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
    except:
        pass

def main():
    st.title("🔍 토평고등학교 분실물 찾기")
    
    # 세션 상태 초기화
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    if 'view_item_id' not in st.session_state:
        st.session_state.view_item_id = None
    
    # 데이터 로드
    items = load_data()
    
    # 상단 메뉴
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 잃어버린 물건을 찾아보세요")
    with col2:
        if st.button("➕ 등록하기", use_container_width=True, type="primary"):
            st.session_state.view_item_id = None
            st.session_state.show_register = True
    
    # 등록 폼 표시
    if st.session_state.get('show_register', False) or st.session_state.view_item_id is None:
        with st.expander("📝 분실물 등록하기", expanded=st.session_state.get('show_register', False)):
            with st.form("register_form", clear_on_submit=True):
                st.markdown("**필수 항목을 모두 입력해주세요**")
                
                uploaded_file = st.file_uploader(
                    "사진 업로드 (필수)",
                    type=['jpg', 'jpeg', 'png', 'gif'],
                    help="최대 5MB까지 업로드 가능합니다"
                )
                
                item_name = st.text_input("물품명 (필수)")
                category = st.selectbox(
                    "카테고리 (필수)",
                    ["전자기기", "의류", "학용품", "가방", "지갑", "기타"]
                )
                found_date = st.date_input("습득 날짜 (필수)")
                found_time = st.time_input("습득 시간 (필수)")
                location = st.text_input("발견 장소 (필수)")
                description = st.text_area("특징 및 설명")
                status = st.selectbox(
                    "상태",
                    ["습득", "찾는 중"]
                )
                
                submitted = st.form_submit_button("등록하기", use_container_width=True)
                
                if submitted:
                    # 필수 항목 검증
                    if not uploaded_file:
                        st.error("필수 항목을 모두 입력해주세요: 사진을 업로드해주세요")
                    elif not item_name or not location:
                        st.error("필수 항목을 모두 입력해주세요: 물품명과 발견 장소를 입력해주세요")
                    else:
                        # 이미지 저장
                        image_path, error = save_image(uploaded_file)
                        if error:
                            st.error(error)
                        elif image_path:
                            # 새 아이템 생성
                            new_item = {
                                "id": str(uuid.uuid4()),
                                "item_name": item_name,
                                "category": category,
                                "found_date": found_date.strftime("%Y-%m-%d"),
                                "found_time": found_time.strftime("%H:%M"),
                                "location": location,
                                "description": description,
                                "status": status,
                                "image_path": image_path,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "comments": []
                            }
                            
                            items.append(new_item)
                            if save_data(items):
                                st.success("등록이 완료되었습니다!")
                                st.session_state.show_register = False
                                st.rerun()
        
        st.session_state.show_register = False
    
    # 아이템 목록 표시
    if st.session_state.view_item_id is None:
        st.markdown("---")
        st.markdown("### 📋 분실물 목록")
        
        if not items:
            st.info("등록된 분실물이 없습니다. 첫 번째 분실물을 등록해보세요!")
        else:
            # 페이지네이션
            total_pages = (len(items) - 1) // ITEMS_PER_PAGE + 1
            start_idx = st.session_state.current_page * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, len(items))
            
            # 최신순 정렬
            sorted_items = sorted(items, key=lambda x: x['created_at'], reverse=True)
            page_items = sorted_items[start_idx:end_idx]
            
            # 그리드 레이아웃으로 표시
            cols = st.columns(3)
            for idx, item in enumerate(page_items):
                with cols[idx % 3]:
                    with st.container():
                        # 이미지 표시
                        if os.path.exists(item['image_path']):
                            try:
                                img = Image.open(item['image_path'])
                                st.image(img, use_container_width=True)
                            except:
                                st.info("이미지를 불러올 수 없습니다")
                        else:
                            st.info("이미지 없음")
                        
                        # 정보 표시
                        st.markdown(f"**{item['item_name']}**")
                        st.caption(f"📍 {item['location']} | 📅 {item['found_date']}")
                        st.caption(f"🏷️ {item['category']} | 상태: {item['status']}")
                        
                        # 상세보기 버튼
                        if st.button("상세보기", key=f"view_{item['id']}", use_container_width=True):
                            st.session_state.view_item_id = item['id']
                            st.rerun()
            
            # 페이지네이션 컨트롤
            if total_pages > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                with col1:
                    if st.button("◀ 이전", disabled=(st.session_state.current_page == 0)):
                        st.session_state.current_page -= 1
                        st.rerun()
                with col3:
                    st.markdown(f"**페이지 {st.session_state.current_page + 1} / {total_pages}**")
                with col5:
                    if st.button("다음 ▶", disabled=(st.session_state.current_page >= total_pages - 1)):
                        st.session_state.current_page += 1
                        st.rerun()
    
    # 상세보기
    else:
        item = next((x for x in items if x['id'] == st.session_state.view_item_id), None)
        
        if item:
            st.markdown("---")
            if st.button("← 목록으로 돌아가기"):
                st.session_state.view_item_id = None
                st.rerun()
            
            st.markdown("### 📄 상세 정보")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 이미지 표시
                if os.path.exists(item['image_path']):
                    try:
                        img = Image.open(item['image_path'])
                        st.image(img, use_container_width=True)
                    except:
                        st.info("이미지를 불러올 수 없습니다")
                else:
                    st.info("이미지 없음")
            
            with col2:
                st.markdown(f"### {item['item_name']}")
                st.markdown(f"**카테고리:** {item['category']}")
                st.markdown(f"**습득 날짜:** {item['found_date']}")
                st.markdown(f"**습득 시간:** {item['found_time']}")
                st.markdown(f"**발견 장소:** {item['location']}")
                st.markdown(f"**상태:** {item['status']}")
                if item['description']:
                    st.markdown(f"**설명:** {item['description']}")
                st.markdown(f"**등록일:** {item['created_at']}")
                
                # 삭제 버튼
                st.markdown("---")
                if st.button("🗑️ 삭제하기", type="secondary", use_container_width=True):
                    if st.checkbox("정말 삭제하시겠습니까?", key="delete_confirm"):
                        # 이미지 삭제
                        delete_image(item['image_path'])
                        # 데이터에서 삭제
                        items = [x for x in items if x['id'] != item['id']]
                        if save_data(items):
                            st.success("삭제되었습니다!")
                            st.session_state.view_item_id = None
                            st.rerun()
            
            # 댓글 섹션
            st.markdown("---")
            st.markdown("### 💬 댓글")
            
            # 댓글 목록
            if item['comments']:
                for comment in item['comments']:
                    with st.container():
                        col_comment, col_actions = st.columns([8, 1])
                        with col_comment:
                            st.markdown(f"**{comment.get('author', '익명')}** ({comment['created_at']})")
                            st.markdown(comment['content'])
                        with col_actions:
                            if st.button("🗑️ 삭제", key=f"delete_comment_{comment['id']}", use_container_width=True):
                                item['comments'] = [
                                    c for c in item['comments'] if c['id'] != comment['id']
                                ]
                                if save_data(items):
                                    st.success("댓글이 삭제되었습니다!")
                                    st.rerun()
                        st.markdown("---")
            else:
                st.info("아직 댓글이 없습니다.")
            
            # 댓글 작성
            with st.form("comment_form", clear_on_submit=True):
                comment_text = st.text_area("댓글 작성")
                author = st.text_input("이름 (선택사항)", placeholder="익명")
                submitted = st.form_submit_button("댓글 등록", use_container_width=True)
                
                if submitted:
                    if not comment_text:
                        st.error("댓글 내용을 입력해주세요")
                    else:
                        new_comment = {
                            "id": str(uuid.uuid4()),
                            "content": comment_text,
                            "author": author if author else "익명",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # 아이템에 댓글 추가
                        for i, it in enumerate(items):
                            if it['id'] == item['id']:
                                items[i]['comments'].append(new_comment)
                                break
                        
                        if save_data(items):
                            st.success("댓글이 등록되었습니다!")
                            st.rerun()
        else:
            st.error("해당 아이템을 찾을 수 없습니다.")
            if st.button("목록으로 돌아가기"):
                st.session_state.view_item_id = None
                st.rerun()

if __name__ == "__main__":
    main()