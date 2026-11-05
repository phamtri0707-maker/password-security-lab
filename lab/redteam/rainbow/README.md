
# MD5 Rainbow Table — Salt Comparison Lab

## 1. Mục tiêu

Thí nghiệm mô phỏng việc khôi phục mật khẩu từ hash MD5 bị lộ, nhằm:

- Minh họa cách hoạt động của rainbow table.
- So sánh MD5 không salt và MD5 có salt.
- Kiểm tra khả năng tái sử dụng rainbow table khi thêm salt.
- Chứng minh salt không ngăn hoàn toàn việc thử mật khẩu offline.

Toàn bộ mật khẩu và hash đều là dữ liệu giả lập phục vụ học tập.

## 2. Cấu hình rainbow table

| Thông số | Giá trị | Bằng chứng |
|---|---|---|
| Thuật toán hash | MD5 | [Mã nguồn](md5_rainbow_1000.py) |
| Số mật khẩu trong wordlist | 1.000 | [wordlist-1000.txt](wordlist-1000.txt) |
| Số chuỗi rainbow | 100 | [Bảng START-END](md5_table_1000.csv) |
| Độ dài mỗi chuỗi | 12 vòng | [Cấu hình trong code](md5_rainbow_1000.py) |
| Bảng rainbow | Lưu cặp START-END | [md5_table_1000.csv](md5_table_1000.csv) |
| Bảng tra cứu trực tiếp | Lưu password và MD5 hash | [md5_direct_table_1000.csv](md5_direct_table_1000.csv) |
| Dữ liệu kiểm tra | 20 hash mục tiêu | [targets_20.csv](targets_20.csv) |

**Lưu ý:** `md5_table_1000.csv` mới là rainbow table.
`md5_direct_table_1000.csv` là bảng tra cứu hash thông thường, được tạo để so sánh.

## 3. Kết quả rainbow table không salt

| Chỉ số | Kết quả | File chứng minh |
|---|---|---|
| Tổng số hash kiểm tra | 20 | [targets_20.csv](targets_20.csv) |
| Số hash khôi phục thành công | 15 | [test_results_20.csv](test_results_20.csv) |
| Số hash không tìm được | 5 | [test_results_20.csv](test_results_20.csv) |
| Tỷ lệ thành công | 75% | [test_result_1000.txt](test_result_1000.txt) |
| Thời gian tra cứu trung bình | Khoảng 0,127 ms | [test_result_1000.txt](test_result_1000.txt) |
| Chương trình thực hiện | Python | [md5_rainbow_1000.py](md5_rainbow_1000.py) |

Kết quả 75% chỉ áp dụng cho bộ 20 hash kiểm tra trong thí nghiệm,
không đại diện cho xác suất khôi phục mật khẩu trong thực tế.

## 4. So sánh MD5 có salt và không salt

Để so sánh công bằng, hai trường hợp sử dụng:
- Cùng mật khẩu đối chứng: `1026`.
- Cùng thuật toán: MD5.
- Cùng rainbow table đã tạo trước.
- Chỉ thay đổi việc có salt hay không.

| Tiêu chí | MD5 không salt | MD5 có salt | Bằng chứng |
|---|---|---|---|
| Mật khẩu gốc | `1026` | `1026` | [Kết quả chạy](md5_salt_result.txt) |
| Salt | Không có | `lab_salt_A:` | [Code thí nghiệm](md5_salt_demo.py) |
| Đầu vào phép băm | `1026` | `lab_salt_A:1026` | [Code thí nghiệm](md5_salt_demo.py) |
| Thuật toán | MD5 | MD5 | [Code thí nghiệm](md5_salt_demo.py) |
| Hash mục tiêu | MD5 của mật khẩu | MD5 của salt + mật khẩu | [Kết quả chạy](md5_salt_result.txt) |
| Rainbow table | Bảng đã tạo trước | Cùng bảng, không tạo lại | [Bảng rainbow](md5_table_1000.csv) |
| Kết quả tra cứu | `Found: 1026` | `Found: None` | [Kết quả chạy](md5_salt_result.txt) |
| Thành công? | `True` | `False` | [Kết quả chạy](md5_salt_result.txt) |

### Giải thích

**Không salt:** Hash mục tiêu được tạo bằng `MD5(password)`,
phù hợp với cách rainbow table đã được xây dựng.

**Có salt:** Hash mục tiêu được tạo bằng `MD5(salt + password)`,
trong khi rainbow table cũ vẫn sử dụng `MD5(password)`.

Do đó, rainbow table cũ không tìm được mật khẩu trong trường hợp
có salt của thí nghiệm này.

Xem:
- [Mã nguồn tạo và tra cứu rainbow table](md5_rainbow_1000.py)
- [Mã nguồn so sánh salt](md5_salt_demo.py)
- [Kết quả chạy thực tế](md5_salt_result.txt)

## 5. Tại sao vẫn crack được khi biết salt?

Trong thí nghiệm tiếp theo, chương trình biết salt và thử từng
mật khẩu ứng viên trong wordlist:

`MD5(salt + candidate) == target_hash`

| Phương pháp | Kết quả | Bằng chứng |
|---|---|---|
| Dùng lại rainbow table không salt | Không tìm được | [md5_salt_result.txt](md5_salt_result.txt) |
| Biết salt và thử wordlist | Tìm được `1026` | [md5_salt_result.txt](md5_salt_result.txt) |
| Danh sách ứng viên | 1.000 mật khẩu | [wordlist-1000.txt](wordlist-1000.txt) |
| Thuật toán thử ứng viên | MD5(salt + candidate) | [md5_salt_demo.py](md5_salt_demo.py) |

Điều này cho thấy salt không làm mật khẩu trở nên không thể crack.
Salt chủ yếu ngăn việc tái sử dụng trực tiếp các bảng hash
tính trước cho nhiều salt khác nhau.

## 6. So sánh dung lượng bảng

| Loại bảng | Dung lượng ghi nhận | File |
|---|---|---|
| Rainbow table (100 START-END) | 1.576 bytes | [md5_table_1000.csv](md5_table_1000.csv) |
| Direct table (1.000 password-hash) | 41.367 bytes | [md5_direct_table_1000.csv](md5_direct_table_1000.csv) |
| Log xây dựng | Thời gian và kích thước | [build_result_1000.txt](build_result_1000.txt) |

Lưu ý: Hai bảng có độ bao phủ khác nhau, vì vậy không thể dùng
riêng tỷ lệ dung lượng này để kết luận bảng rainbow luôn hiệu quả hơn.

## 7. Kết luận

1. Rainbow table có thể khôi phục một số hash MD5 không salt
   thuộc phạm vi bảng bao phủ.
2. Việc thêm salt khiến rainbow table không salt cũ không thể
   được tái sử dụng trực tiếp trong thí nghiệm.
3. Hai salt khác nhau tạo ra hash khác nhau cho cùng mật khẩu.
4. Khi salt đã biết, việc thử mật khẩu offline vẫn có thể thành công.
5. MD5 không phù hợp để lưu trữ mật khẩu thực tế; nên sử dụng
   thuật toán chuyên dụng như Argon2id hoặc bcrypt với salt riêng.

## 8. Danh mục bằng chứng

| File | Vai trò |
|---|---|
| [md5_rainbow_1000.py](md5_rainbow_1000.py) | Xây dựng và tra cứu rainbow table |
| [md5_table_1000.csv](md5_table_1000.csv) | Rainbow table START-END |
| [md5_direct_table_1000.csv](md5_direct_table_1000.csv) | Bảng tra cứu hash trực tiếp |
| [wordlist-1000.txt](wordlist-1000.txt) | Wordlist của thí nghiệm |
| [targets_20.csv](targets_20.csv) | 20 hash mục tiêu |
| [test_results_20.csv](test_results_20.csv) | Kết quả chi tiết từng hash |
| [test_result_1000.txt](test_result_1000.txt) | Tổng kết 20 bài kiểm tra |
| [build_result_1000.txt](build_result_1000.txt) | Thời gian tạo bảng và dung lượng |
| [md5_salt_demo.py](md5_salt_demo.py) | Code so sánh có salt/không salt |
| [md5_salt_result.txt](md5_salt_result.txt) | Kết quả thí nghiệm salt |
