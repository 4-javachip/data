import uuid
import random

added_categories = {}
added_subcategories = {}

# category 테이블에 대분류가 없으면 create, 있으면 기존 id 반환
def get_or_create_category(cursor, cat_name, item, created_at, updated_at):
    if cat_name in added_categories:
        return added_categories[cat_name]
    # db에 이미 있는지 확인
    cursor.execute("SELECT id FROM category WHERE name = %s", (cat_name,))
    result = cursor.fetchone()
    if result:
        category_id = result['id']
        added_categories[cat_name] = category_id
        return category_id
    # 없으면 새로 생성
    thumbnails = item.get("썸네일이미지", [])
    image = thumbnails[0]["url"] if thumbnails else "https://default.img"
    desc = cat_name

    cursor.execute("""
        INSERT INTO category (name, image, description, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (cat_name, image, desc, created_at, updated_at))

    category_id = cursor.lastrowid
    added_categories[cat_name] = category_id
    return category_id

# subcategory 테이블에 소분류가 없으면 create, 있으면 기존 id 반환
def get_or_create_subcategory(cursor, subcat_name, category_id, created_at, updated_at):
    key = (subcat_name, category_id)
    if key in added_subcategories:
        return added_subcategories[key]
    
    # DB에 이미 있는지 확인
    cursor.execute("""
        SELECT id FROM sub_category WHERE name = %s AND category_id = %s
    """, (subcat_name, category_id))
    result = cursor.fetchone()
    if result:
        subcategory_id = result['id']
        added_subcategories[key] = subcategory_id
        return subcategory_id
    # 없으면 새로 생성
    cursor.execute("""
        INSERT INTO sub_category (name, category_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s)
    """, (subcat_name, category_id, created_at, updated_at))

    subcategory_id = cursor.lastrowid
    added_subcategories[key] = subcategory_id
    return subcategory_id

# product 테이블에 상품 삽입
def insert_product(cursor, product_name, created_at, updated_at):
    product_uuid = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO product (name, product_uuid, created_at, updated_at)
        VALUES (%s, %s, %s, %s)
    """, (product_name, product_uuid, created_at, updated_at))
    return product_uuid

# thumbnail 테이블에 썸네일 이미지 삽입
def insert_thumbnails(cursor, product_uuid, thumbnails, created_at, updated_at):
    for i, thumb in enumerate(thumbnails):
        cursor.execute("""
            INSERT INTO thumbnail 
            (product_uuid, thumbnail_url, description, defaulted, created_at, updated_at, deleted)
            VALUES (%s, %s, %s, %s, %s, %s, false)
        """, (product_uuid, thumb["url"], thumb["alt"], i == 0, created_at, updated_at))

# product_description 테이블에 상세설명 HTML 저장
def insert_product_description(cursor, product_uuid, detail_html, created_at, updated_at):
    cursor.execute("""
        INSERT INTO product_description 
        (product_uuid, detail_description, description, created_at, updated_at)
        VALUES (%s, %s, '상품이미지', %s, %s)
    """, (product_uuid, detail_html, created_at, updated_at))

# product_category_list 테이블에 상품-카테고리 연결 정보 저장
def insert_product_category_list(cursor, product_uuid, category_id, subcategory_id, created_at, updated_at):
    cursor.execute("""
        INSERT INTO product_category_list 
        (product_uuid, category_id, sub_category_id, created_at, updated_at, deleted)
        VALUES (%s, %s, %s, %s, %s, false)
    """, (product_uuid, category_id, subcategory_id, created_at, updated_at))

# product_option 테이블에 상품 옵션 정보 저장
def insert_product_options(cursor, product_uuid, item, created_at, updated_at):
    option_names = item.get("옵션명", [])
    original_price = item.get("정가", 0)
    sale_price = item.get("할인가", 0)

    color_keywords = ["color", "Color", "색"]
    size_keywords = ["size", "Size", "사이즈"]

    has_color = any(any(k in opt for k in color_keywords) for opt in option_names)
    has_size = any(any(k in opt for k in size_keywords) for opt in option_names)

    color_ids = random.sample(range(1, 6), k=random.randint(2, 5)) if has_color else [None]
    size_ids = random.sample(range(1, 3), k=2) if has_size else [None]

    for color_id in color_ids:
        for size_id in size_ids:
            option_uuid = str(uuid.uuid4())
            stock = random.randint(10, 100)
            discount_rate = round((1 - (sale_price / original_price)) * 100) if original_price else 0

            cursor.execute("""
                INSERT INTO product_option (
                    product_option_uuid, product_uuid, color_option_id, size_option_id,
                    stock, price, discount_rate, total_price,
                    created_at, updated_at, deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false)
            """, (
                option_uuid, product_uuid, color_id, size_id,
                stock, original_price, discount_rate, sale_price,
                created_at, updated_at
            ))

# 위 함수들 종합. json 상품 1개를 DB에 삽입하는 통합 처리기
def process_product_item(item, cursor, created_at, updated_at):
    product_name = item["제품명"]
    product_uuid = insert_product(cursor, product_name, created_at, updated_at)

    # thumbnail create
    if "썸네일이미지" in item:
        insert_thumbnails(cursor, product_uuid, item["썸네일이미지"], created_at, updated_at)

    # 상세정보 HTML 저장
    detail_html = item.get("상세정보HTML", "")
    insert_product_description(cursor, product_uuid, detail_html, created_at, updated_at)

    # 카테고리 저장
    cat_list = item.get("카테고리", [])

    category_id = get_or_create_category(cursor, cat_list[0], item, created_at, updated_at)
    subcategory_id = get_or_create_subcategory(cursor, cat_list[-1], category_id, created_at, updated_at)

    # 상품-카테고리 연결 정보 저장
    insert_product_category_list(cursor, product_uuid, category_id, subcategory_id, created_at, updated_at)
    # 상품 옵션 정보 저장
    insert_product_options(cursor, product_uuid, item, created_at, updated_at)
    return product_uuid
