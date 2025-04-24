from db import get_connection
from utils import get_random_datetime, generate_fake_user
from product import process_product_item
from review import extract_review_data, insert_bulk_reviews_and_images
import os
import json
from datetime import datetime

def insert_fake_users(cursor, count=10):
    """가짜 유저 N명 삽입"""
    users = [generate_fake_user() for _ in range(count)]

    sql = """
    INSERT INTO user (
        user_uuid, email, password, nickname, name,
        birthdate, phone_number, gender, state, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(sql, users)
    return [user[0] for user in users]  # user_uuid만 반환


def main():
    conn = get_connection()
    cursor = conn.cursor()
    user_list = []
    start_time = datetime.now()
    try:
        # 1. 가짜 유저 삽입
        user_list = insert_fake_users(cursor, count=100)
        conn.commit()
        print(f"👥 가짜 유저 {len(user_list)}명 삽입 완료")

        # 1. 가짜 유저 100명 불러오기
        # cursor.execute("""
        #     SELECT user_uuid FROM user ORDER BY id DESC LIMIT %s
        # """, (100,))
        # user_list = [row['user_uuid'] for row in cursor.fetchall()]
        # print(user_list)

        # 2. 상품/리뷰 삽입
        data_folder = "data"
        json_files = sorted([f for f in os.listdir(data_folder) if f.endswith(".json")])
        total_count = 0
        start_time = datetime.now()

        for file_name in json_files:
            file_path = os.path.join(data_folder, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data:
                try:
                    conn.begin()
                    created_at = updated_at = get_random_datetime()

                    product_uuid = process_product_item(item, cursor, created_at, updated_at)
                    #  상품정보 완료

                    reviews = item.get("리뷰목록", [])

                    review_values, review_image_values = extract_review_data(product_uuid, reviews, user_list)
                    insert_bulk_reviews_and_images(cursor, review_values, review_image_values)

                    conn.commit()
                    total_count += 1
                except Exception as e:
                    conn.rollback()
                    print("❌ 처리 실패:", item.get("제품명"))
                    print(e)

        print(f"\n🎉 총 {total_count}개 제품 처리 완료! ⏱️ 소요 시간: {datetime.now() - start_time}")
    finally:
        cursor.close()
        conn.close()
    end_time = datetime.now()
    total_time = end_time - start_time
    print(f"🧮 전체 소요 시간: {total_time}")
    print("데이터 개수", len(json_files))


if __name__ == "__main__":
    main()







