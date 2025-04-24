SSG.com 의 데이터를 크롤링하는 코드입니다.

- 데이터타입 (typescript 기준)
```
type Product = {
  카테고리: string[]; // 큰거일수록 index 낮음 ex) ["대", "중", "소"]
  상품상세URL: string;
  썸네일이미지: {
    url: string;
    alt: string;
  }[];
  옵션명: string[]; // ex) ["size", "color"]
  제품명: string;
  정가: number;
  할인가: number;
  상세정보HTML: string;
  총리뷰수: number;
  평균별점: number;
  리뷰목록: {
    별점: number;
    리뷰내용: string;
    리뷰이미지url: string[];
    작성자: string;
    작성일: string; // yyyy-MM-dd
  }[];
  상품필수정보: { 유형: string; 값: string }[];
};
```

## 파일 설명
- crawling/ids/ids.json
  - https://www.ssg.com/ 의 '전체 카테고리' 항목 중 일부 카테고리들의 상품 id를 저장한 json 파일
  - 해당 id값을 바탕으로 세부 상품 데이터 스크래핑

- crawling/crawling_ssg_data.py
  - ids.json 정보를 바탕으로 제품 상세 정보를 스크래핑하는 코드.
  - 각 하위 카테고리별로 json 파일을 생성함.
    - ex) 제일 첫 카테고리 ('생활/주방'-'화장지/생리대'-'화장지' 카테고리의 세부 정보는 0_0_0.json 파일에 저장)
  - 'START', 'END' 항목의 카테고리 값들을 조정해, 원하는 카테고리만을 저장하도록 설정 가능.
  - `ThreadPoolExecutor(max_workers=4)` 값을 조절해 병렬 처리를 통해 빠른 속도로 크롤링 가능

- crawling/fix_description.py
  - 크롤링 데이터 중 '상세정보HTML' 항목의 경우, <iframe> 태그를 포함하는 경우가 많아 화면 구성에 어려움이 있음.
  - 이를 처리하기 위해, 크롤링한 세부정보를 바탕으로, '상세정보HTML'의 <iframe> 태그를, 해당 <iframe> 문서 내부의 <div> 태그로 교체하는 코드
 
- sql_input/main.py
  - 해당 크롤링 데이터 (data 폴더 기준)를 db에 insert하는 코드 작성.
  - dp.py : 저장할 db, 저장방식 설정
  - main.py : 실행 코드 + fake 유저 저장 로직
  - product.py : 제품 정보 저장 로직
  - review.py : 리뷰 정보 저장 로직

## Getting Started
사용 라이브러리 : selenium, pymysql, faker
```
pip install selenium pymysql faker
```

1. `crawling/crawling_ssg_data.py 실행` (ids 항목의, 카테고리별 ids 항목을 기준으로 크롤링함.)
   - 이 때 'START', 'END' 항목의 카테고리 값들을 조정해, 원하는 범위를 저장하도록 설정 가능.
   - output 폴더에 크롤링한 데이터 생성.
2. `crawling/fix_desciption.py 실행`
   - data_html_fix 폴더에 크롤링한 데이터 생성.
3. `sql_input/main.py 실행`
   - 실행 전, db.py를 본인의 db 관련 정보들로 수정할 것.
   - 이후 main.py 실행
   - 실행 시 fake_user 100명을 삽입한 후, 리뷰 데이터 저장 시 해당 유저들을 무작위로 리뷰 작성자로 선정.
     - fake_user를 원하지 않을 경우, main.py의 `1. 가짜 유저 삽입` 코드를 주석 처리한 뒤, 아래의 `1. 가짜 유저 100명 불러오기`를 실행해 최근 유저 100명을 불러와서 리뷰 작성자로 선정`
    
