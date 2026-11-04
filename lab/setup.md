# Red Team — Giai đoạn 1: dataset và hash

Nhóm 7, chủ đề **Hash & bảo mật mật khẩu + Crack Demo**. Giai đoạn này chuẩn bị dữ liệu tổng hợp và tạo **9 hash: 3 mật khẩu × 3 thuật toán**. Chỉ dùng dữ liệu do nhóm tạo, phục vụ lab được phép.

## 1. Vị trí các file

| Đường dẫn | Chức năng |
| --- | --- |
| `scripts/generate_dataset.py` | Sinh wordlist, chọn mật khẩu mục tiêu và ghi metadata. |
| `scripts/generate_hashes.py` | Đọc 3 mật khẩu mục tiêu và băm mỗi mật khẩu bằng MD5, bcrypt, Argon2id. |
| `scripts/requirements-redteam.txt` | Thư viện Python riêng cho bước chuẩn bị Red Team. |
| `data/wordlist.txt` | Đúng 1.000 mật khẩu tổng hợp, mỗi dòng một mật khẩu, không trùng lặp. |
| `data/targets.txt` | 3 mật khẩu mục tiêu, mỗi dòng một mật khẩu. |
| `data/targets_metadata.csv` | ID mục tiêu, mức độ minh họa và vị trí trong wordlist. |
| `data/hashes/md5.txt` | 3 hash MD5 dạng hex, mỗi dòng một hash. |
| `data/hashes/bcrypt.txt` | 3 hash bcrypt dạng Modular Crypt, bắt đầu bằng `$2b$10$`. |
| `data/hashes/argon2id.txt` | 3 hash Argon2id dạng PHC, bắt đầu bằng `$argon2id$v=19$`. |
| `tests/test_redteam_dataset.py` | Kiểm tra dataset và 9 hash của lab. |

Quy ước chung: `scripts/` chứa chương trình; `data/` chứa wordlist, mục tiêu và hash; `lab/` chứa hướng dẫn, cấu hình và kết quả thực nghiệm. Những thí nghiệm benchmark, Hashcat/John the Ripper, rainbow table và timing về sau sẽ đặt trong `lab/` khi triển khai. `src/` tiếp tục chứa Blue Team.

Các script Red Team hoạt động độc lập: không dùng pepper, cấu hình Argon2 của Blue Team hoặc `users.db`. Không cần khởi động Flask hay tạo database.

## 2. Chạy trong VS Code trên Windows

Mở repository trong VS Code, chọn **Terminal → New Terminal**, dùng PowerShell tại thư mục gốc:

```powershell
cd C:\password-security-lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-redteam.txt
.\.venv\Scripts\python.exe scripts/generate_dataset.py
.\.venv\Scripts\python.exe scripts/generate_hashes.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_redteam_dataset.py -v
```

Nếu đã có `.venv`, dùng môi trường đó và bỏ qua lệnh tạo môi trường. Các lệnh gọi trực tiếp Python trong `.venv`, nên không cần chạy `Activate.ps1`.

Nếu `python` không được nhận diện hoặc mở Microsoft Store do alias WindowsApps, dùng đường dẫn Python thật. Trên máy ADMIN, README hiện có dùng:

```powershell
& 'C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
```

Sau đó tiếp tục từ lệnh cài thư viện. Thành viên khác thay đường dẫn này bằng Python trên máy mình. Trong VS Code có thể chọn **Python: Select Interpreter** rồi chọn `.venv\Scripts\python.exe`.

File dependency riêng ghim `bcrypt==5.0.0` và `argon2-cffi==25.1.0`; `requirements.txt` của Blue Team giữ nguyên. Lệnh test trên chỉ chạy bài kiểm tra Red Team; muốn chạy toàn bộ test Blue Team thì cần cài thêm dependency từ `requirements.txt` theo README.

## 3. Dataset và cách đối chiếu mục tiêu

`generate_dataset.py` dùng seed cố định **7007**, tạo 400 mật khẩu dễ đoán, 350 mật khẩu trung bình và 250 mật khẩu khó đoán hơn. Đây là các nhóm để minh họa trong bài học. Bộ sinh có seed và các nhãn này không phải cách tạo hoặc đánh giá mật khẩu thật.

Các vị trí dưới đây đều tính từ **1**:

| Dòng trong `targets.txt` | Mục tiêu | Vị trí trong `wordlist.txt` |
| ---: | --- | ---: |
| 1 | Mật khẩu dễ đoán | 25 |
| 2 | Mật khẩu trung bình | 650 |
| 3 | Mật khẩu khó đoán hơn | Không có trong wordlist |

`data/targets_metadata.csv` có các cột `target_id,target_line,difficulty,wordlist_line`. Ô `wordlist_line` để trống nghĩa là mật khẩu không có trong wordlist. Không đưa mật khẩu từ dữ liệu rò rỉ hoặc thông tin cá nhân thật vào các file này.

Luồng xử lý:

1. Chạy `generate_dataset.py` để có wordlist, 3 mục tiêu và metadata.
2. Chạy `generate_hashes.py` để đọc `targets.txt`, tạo 3 hash cho mỗi thuật toán.
3. Chạy test để kiểm tra dữ liệu và xác minh các hash khớp với mục tiêu.

**Dòng số n trong mỗi file hash luôn ứng với dòng số n trong `targets.txt`.** Ví dụ, dòng 2 của cả ba file hash đều được tạo từ mật khẩu tại dòng 2 của `targets.txt`. Mỗi file hash chỉ chứa hash, không có tiêu đề, ID hoặc plaintext; giữ thứ tự dòng để đối chiếu.

## 4. Tham số băm

| Thuật toán | Cấu hình lab |
| --- | --- |
| MD5 | Băm trực tiếp mật khẩu, không salt; xuất 32 ký tự hex. Chỉ minh họa thuật toán không phù hợp để lưu mật khẩu. |
| bcrypt | `rounds=10` là cost theo thang logarit; salt ngẫu nhiên do `bcrypt.gensalt()` tạo. |
| Argon2id | Phiên bản 19; `memory_cost=65536` KiB = 64 MiB, `time_cost=3`, `parallelism=1`, salt 16 byte, kết quả băm 32 byte. Salt ngẫu nhiên do thư viện tạo. |

Cấu hình này được ghi riêng trong script Red Team để dễ đọc và tái lập lab. Salt và cost của bcrypt/Argon2id nằm trong chính chuỗi hash, không cần một file salt riêng. Xem cách dùng `gensalt`, `hashpw`, `checkpw` trong [tài liệu bcrypt](https://pypi.org/project/bcrypt/) và các tham số, `hash`, `verify` trong [API argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/api.html).

Dataset dùng mật khẩu ASCII ngắn hơn giới hạn 72 byte của bcrypt. bcrypt 5.0.0 từ chối mật khẩu dài hơn giới hạn này; xem [ghi chú phiên bản bcrypt](https://pypi.org/project/bcrypt/).

Chạy lại bộ sinh dataset sẽ cho cùng wordlist và mục tiêu. MD5 cũng giữ nguyên khi mật khẩu giữ nguyên; bcrypt và Argon2id tạo salt mới nên chuỗi hash thay đổi, dù vẫn xác minh đúng cùng mật khẩu. Sau khi tạo lại dataset, luôn chạy lại bước sinh hash rồi chạy test để giữ các file đồng bộ.

## 5. Kiểm tra kết quả

Sau khi test kết thúc với `OK`, mở các file trong VS Code để quan sát:

- `wordlist.txt`: 1.000 dòng không trùng; `targets.txt`: 3 dòng.
- `targets_metadata.csv`: hai vị trí wordlist là 25 và 650, mục tiêu còn lại có ô vị trí trống.
- Mỗi file trong `data/hashes/`: 3 dòng, tổng cộng 9 hash đúng định dạng.

Test kiểm tra dữ liệu đã tạo trong repository và xác minh 9 hash bằng mật khẩu gốc. Việc xác minh kiểm tra tính đúng đắn, chưa đo tốc độ thử mật khẩu hay benchmark.

## 6. Chuẩn bị chuyển sang Kali ở giai đoạn sau

Các file đầu vào cần mang sang Kali:

- `data/wordlist.txt`
- `data/hashes/md5.txt`
- `data/hashes/bcrypt.txt`
- `data/hashes/argon2id.txt`

Có thể giữ `targets.txt` và `targets_metadata.csv` riêng làm đáp án để đánh giá kết quả. Các file hash dùng định dạng gốc của từng thuật toán. Định dạng `$argon2id$` được hỗ trợ trong [mã nguồn John the Ripper Jumbo](https://github.com/openwall/john/blob/bleeding-jumbo/src/argon2_fmt_plug.c); cần kiểm tra khả năng hỗ trợ của bản công cụ trên Kali khi làm giai đoạn tiếp theo, đặc biệt nếu dùng Hashcat. Giai đoạn này chưa cài hoặc chạy các công cụ đó.

Giai đoạn 1 dừng sau tạo dữ liệu, sinh hash và kiểm thử. Chưa chạy crack wordlist/rules/mask, benchmark CPU/GPU, rainbow table, timing demo, dashboard hay báo cáo kết quả thực nghiệm.
