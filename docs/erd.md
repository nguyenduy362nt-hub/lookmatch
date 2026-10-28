# ERD sơ bộ
```mermaid
erDiagram
  SHOP ||--o{ PRODUCT : co
  PRODUCT ||--o{ PRODUCT_IMAGE : co
  PRODUCT_IMAGE ||--|| EMBEDDING : sinh_ra
  SHOP ||--o{ QUERY : nhan
  QUERY ||--o{ QUERY_RESULT : tra_ve
  PRODUCT ||--o{ QUERY_RESULT : xuat_hien
  SHOP { int id string ten }
  PRODUCT { int id string ma_sp string ten string nhom }
  PRODUCT_IMAGE { int id int product_id string duong_dan }
  EMBEDDING { int image_id int dim blob vector }
  QUERY { int id datetime thoi_diem float giay_tim }
  QUERY_RESULT { int query_id int product_id int hang float diem }
```
