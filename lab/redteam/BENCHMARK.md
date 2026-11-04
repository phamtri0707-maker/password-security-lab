[BENCHMARK.md](https://github.com/user-attachments/files/34386974/BENCHMARK.md)
# Password Security Lab — Dashboard Cost vs Time

> **Red Team | Offline password-hashing demo**  
> Phạm vi: **MD5 · bcrypt · Argon2id** | Môi trường: **Kali Linux trên VirtualBox**  
> Dữ liệu mục tiêu do nhóm tự tạo, mật khẩu minh họa: `student123`.

## Tổng quan

| Chỉ số | Kết quả |
|:--|:--|
| Thuật toán khảo sát | **3** (MD5, bcrypt, Argon2id) |
| Wordlist dùng trong các lần đo dưới đây | **100 ứng viên** |
| Hash mục tiêu | Hash do nhóm tạo từ mật khẩu minh họa |
| Tấn công thử nghiệm | **Offline dictionary attack** |
| Công cụ | **John the Ripper** (MD5, bcrypt); **Python + `argon2-cffi`** (Argon2id) |
| Lab window | **5 giây** cho bài test giới hạn thời gian |

## 1. Cost vs. Time — Thí nghiệm crack thông thường

| Thuật toán | Tham số cost | Hashing time trung bình | Crack time | Kết quả | Công cụ crack |
|:--|:--|--:|--:|:--:|:--|
| **MD5** | Không có cost điều chỉnh | **0.000409 ms** | **0.091 s** | ✅ Tìm thấy | John the Ripper |
| **bcrypt** | `cost = 12` | **173.681 ms** | **5.521 s** | ✅ Tìm thấy | John the Ripper |
| **Argon2id** | `t = 3`, `m = 65536 KiB` (64 MiB), `p = 4` | **108.674 ms** | **23.928 s** | ✅ Tìm thấy | Python + `argon2-cffi` |

> **Nguồn số liệu:** Những lần chạy đã ghi nhận trước đó trong quá trình làm lab. Trước khi nộp, **đối chiếu với các file `result.txt` mới nhất** và cập nhật nếu số đo khác. Đây là các lần đo riêng, không phải benchmark chuẩn hóa giữa các công cụ.

### Biểu đồ trực quan — Crack time (giây)

*Các thanh được chia tỷ lệ theo thời gian crack đã ghi nhận; làm tròn để dễ nhìn.*

```text
MD5       ▏                              0.091 s
bcrypt    ███████                        5.521 s
Argon2id  ██████████████████████████████ 23.928 s
```

### Biểu đồ trực quan — Hashing time (ms)

```text
MD5       ▏                              0.000409 ms
bcrypt    ██████████████████████████████ 173.681 ms
Argon2id  ███████████████████            108.674 ms
```

**Lưu ý cách đọc:** `Hashing time` là thời gian đo cho **một lần băm** (trung bình), còn `Crack time` là thời gian **thử các ứng viên cho đến khi tìm ra mật khẩu**. Hai đại lượng không đồng nhất. Cost của bcrypt và Argon2id cũng **không cùng đơn vị**, không được so trực tiếp số 12 với số 3.

## 2. Demo lab window — Giới hạn 5 giây

**Thiết kế:** Cùng hash mục tiêu do nhóm tạo từ `student123`; wordlist có 100 ứng viên, `student123` được đặt ở dòng cuối. Mỗi bài test chỉ được chạy trong cửa sổ thời gian khoảng **5 giây**.

| Thuật toán | Lab window | Số ứng viên đã thử | Thời gian đo | Tìm được `student123`? | Kết luận |
|:--|--:|:--|:--|:--:|:--|
| **MD5** | 5 s | Chưa đo riêng tổng số lượt thử của John | **Xem `md5/timeout_result.txt`** | ✅ Có (đã xác nhận chạy thành công) | Crack được trong lab window |
| **Argon2id** | 5 s | **53 / 100** | **5.026 s** | ❌ Không | Chưa đến mật khẩu ở dòng 100 trong lab window |

### Tiến độ thử wordlist của Argon2id trong 5 giây

```text
Argon2id  █████████████████░░░░░░░░░░░░░░░  53/100 ứng viên
           Đã thử: 53%       Còn lại: 47%
```

> **Lưu ý kỹ thuật:** Script Python kiểm tra thời gian **trước khi bắt đầu lần xác minh tiếp theo**, nên tổng thời gian có thể hơi vượt 5 giây do phép xác minh đang thực hiện. Đây là giới hạn *bắt đầu lượt thử*, không phải một lệnh dừng CPU chính xác tuyệt đối tại 5.000 giây.

### Kết luận đúng với dữ liệu

- Với wordlist 100 ứng viên, **cả MD5, bcrypt và Argon2id đều đã bị tìm ra** khi cho phép bài thử hoàn tất.
- Trong **lab window 5 giây**, MD5 tìm được mật khẩu; Argon2id mới kiểm tra **53/100** ứng viên và **chưa tìm được** mật khẩu.
- Điều này **không** chứng minh Argon2id "không thể crack"; nó minh họa rằng xác minh mỗi ứng viên tốn chi phí hơn, khiến tốc độ thử ngoại tuyến bị hạn chế trong một khoảng thời gian nhất định.

## 3. Giải thích cost và khả năng bảo vệ mật khẩu

| Thuật toán | Đặc điểm | Hàm ý bảo mật |
|:--|:--|:--|
| **MD5** | Hàm hash nhanh, không thiết kế riêng cho lưu trữ mật khẩu | Không nên dùng trực tiếp để lưu mật khẩu |
| **bcrypt** | Có salt và cost factor điều chỉnh được | Khi tăng cost, mỗi lượt thử mật khẩu tốn tính toán hơn |
| **Argon2id** | Có salt và các tham số time/memory/parallelism | Tăng chi phí tính toán **và bộ nhớ** cho việc thử ngoại tuyến |

## 4. Tái hiện kết quả

Chạy tại thư mục gốc của repository (`password-security-lab`):

```bash
# Thí nghiệm crack thông thường
./lab/redteam/md5/crack.sh 2>&1 | tee lab/redteam/md5/result.txt
./lab/redteam/bcrypt/crack.sh 2>&1 | tee lab/redteam/bcrypt/result.txt
./lab/redteam/argon2id/crack.sh 2>&1 | tee lab/redteam/argon2id/result.txt

# Thí nghiệm giới hạn thời gian
bash lab/redteam/md5/timeout_test.sh 2>&1 | tee lab/redteam/md5/timeout_result.txt
bash lab/redteam/argon2id/timeout_test.sh 2>&1 | tee lab/redteam/argon2id/timeout_result.txt
```

Các file liên quan:

- [MD5 — mã thử nghiệm](md5/crack.sh) · [Kết quả](md5/result.txt) · [Test 5 giây](md5/timeout_result.txt)
- [bcrypt — mã thử nghiệm](bcrypt/crack.sh) · [Kết quả](bcrypt/result.txt)
- [Argon2id — mã thử nghiệm](argon2id/crack.sh) · [Kết quả](argon2id/result.txt) · [Test 5 giây](argon2id/timeout_result.txt)
- [Wordlist 100 ứng viên](wordlists/wordlist-100.txt) · [Wordlist 10.000 ứng viên](wordlists/wordlist-10000.txt)

## 5. Giới hạn thí nghiệm và Responsible Use

- Kết quả phụ thuộc CPU, số luồng, tải hệ thống và tài nguyên cấp cho VirtualBox.
- MD5/bcrypt dùng **John**, Argon2id dùng **Python**; không thể suy ra tỷ lệ tốc độ tuyệt đối giữa các thuật toán chỉ từ bảng trên.
- Không đánh đồng thời gian **tạo hash** với thời gian **xác minh hash** hoặc thời gian chạy công cụ crack.
- Mật khẩu yếu nằm trong wordlist vẫn có thể bị tìm thấy ngay cả khi dùng thuật toán hash mạnh.
- Các hash mục tiêu được tạo trong lab; không thử mật khẩu trên dịch vụ trực tuyến và không sử dụng tài khoản thật.
- Nếu bộ wordlist công khai được sử dụng, cần ghi rõ nguồn và xác nhận yêu cầu về **dataset tổng hợp** với giảng viên.

---

**Trạng thái:** Kết quả thực nghiệm phục vụ thuyết trình và review mã nguồn trên nhánh `feature/redteam`. **Chưa merge vào `develop`** cho đến khi nhóm duyệt Pull Request.
