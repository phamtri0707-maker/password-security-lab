# Password Security Lab

Bài tập lớn Cơ sở An toàn thông tin, nhóm 7 — **Hash & Bảo mật mật khẩu + Crack Demo**.
Project gồm ứng dụng đăng ký/đăng nhập local (Blue Team) và thí nghiệm crack hash tổng hợp (Red Team).

## Cấu trúc project

| Vị trí | Nội dung |
| --- | --- |
| `src/` | Flask, giao diện HTML/CSS, khởi tạo SQLite và cấu hình Argon2id Blue Team. |
| `scripts/create_demo_user.py`, `scripts/tune_argon2.py` | Tạo tài khoản demo và thử cost hash/verify của Blue Team. |
| `scripts/generate_dataset.py`, `scripts/generate_hashes.py` | Sinh dữ liệu tổng hợp và 9 hash Red Team. |
| `scripts/Benchmark_hash.py`, `scripts/plot_benchmark.py` | Đo hashing time và vẽ biểu đồ từ CSV. |
| `data/` | `wordlist.txt`, `targets.txt`, `targets_metadata.csv` và `hashes/`. |
| `lab/setup.md` | Hướng dẫn chi tiết Red Team: cài đặt, Wordlist, Rules, Mask, benchmark. |
| `lab/evidence/`, `lab/results/` | 8 ảnh Hashcat; CSV và biểu đồ benchmark. |
| `docs/https-local.md`, `tests/` | Hướng dẫn TLS và kiểm thử. |

## Cài đặt Python

Môi trường đã dùng: Windows 11, Python **3.14.7**. Dependency biểu đồ yêu cầu Python >=3.11.
Tại thư mục gốc, tạo `.venv` một lần nếu chưa có, rồi cài dependency:

```powershell
cd C:\password-security-lab
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r scripts/requirements-redteam.txt
```

`requirements.txt` chứa Flask/argon2-cffi; `scripts/requirements-redteam.txt` chứa bcrypt/argon2-cffi/matplotlib.
Nếu không dùng được `py`, dùng đường dẫn Python thật theo [hướng dẫn Windows](lab/setup.md#2-chuẩn-bị-python-trên-windows).
Muốn gõ ngắn, kích hoạt `.\.venv\Scripts\Activate.ps1` rồi dùng `python` thay đường dẫn dài.
Hashcat/PoCL cài riêng trên Kali; không sao chép `.venv` Windows sang VM.

## Blue Team

### Chức năng đã triển khai

- Register kiểm tra dữ liệu, băm `password + pepper` bằng Argon2id; SQLite lưu `id, username, password_hash`.
- Login tìm username bằng SQL có tham số, dùng `verify()` để kiểm tra mật khẩu.
- Đăng nhập thành công tạo session; `/home` yêu cầu đăng nhập; Logout xóa session.
- Form kiểm tra mã CSRF khi nhận POST; cookie có `Secure`, `HttpOnly`, `SameSite=Lax`.
- App dùng HTTPS local; username không tồn tại và password sai nhận cùng thông báo.

Salt được thư viện sinh ngẫu nhiên và nằm trong hash; pepper lấy từ môi trường, không lưu trong database.
Cấu hình ở `src/argon2_config.json`: **64 MiB, t=3, p=4**; t là số lượt xử lý, p là mức song song. Cost làm tăng chi phí mỗi lần băm.

### Chạy ứng dụng

Sau khi cài dependency, khởi tạo bảng nếu chưa có:

```powershell
$pythonExe = (Resolve-Path ".\.venv\Scripts\python.exe").Path
& $pythonExe src\init_db.py
```

**Chỉ khi thiết lập mới, chưa có tài khoản**, tạo pepper và khóa session một lần:

```powershell
$env:PASSWORD_PEPPER = & $pythonExe -c "import secrets; print(secrets.token_hex(32))"
$env:FLASK_SECRET_KEY = & $pythonExe -c "import secrets; print(secrets.token_hex(32))"
```

Nếu đã có tài khoản, cấp lại đúng pepper và khóa session cũ từ nơi lưu riêng; không sinh pepper mới.
App không tự đọc `.env`; các biến trên chỉ tồn tại trong terminal hiện tại. Đổi pepper làm mật khẩu cũ không khớp.

Tạo certificate/private key ngoài repository theo [hướng dẫn HTTPS](docs/https-local.md#2-tạo-certificate-và-private-key-một-lần), rồi chạy trong terminal đã có hai biến trên:

```powershell
$tlsDir = Join-Path $env:LOCALAPPDATA "SecureLoginLab\tls"
$env:TLS_CERT_FILE = Join-Path $tlsDir "local.crt"
$env:TLS_KEY_FILE = Join-Path $tlsDir "local.key"
& $pythonExe src\app.py
```

Mở **https://127.0.0.1:5000/**, thử **Đăng ký → Đăng nhập → Home → Logout**; `Ctrl+C` để dừng.
Certificate tự ký gây cảnh báo trình duyệt: chỉ tiếp tục với certificate lab do mình tạo.
Dùng `src/app.py` để áp dụng TLS; `flask run` thông thường không chạy phần cấu hình này.
Script `create_demo_user.py` là cách tạo tài khoản `demo` từ terminal, không bắt buộc khi dùng Register.
Muốn thử cost Blue Team: dừng web, giữ `PASSWORD_PEPPER` và chạy `& $pythonExe scripts\tune_argon2.py`.

## Red Team

### Dataset và hash

Dữ liệu có **1.000 mật khẩu không trùng**, seed `7007`; đây là dữ liệu học tập, không lấy từ dữ liệu rò rỉ.
Ba mục tiêu ở `targets.txt`: hai mục tiêu nằm trong wordlist (dòng **25, 650**), một mục tiêu ở ngoài.
Mỗi mục tiêu có MD5, bcrypt và Argon2id: **9 hash**; dòng n của mỗi file hash ứng với dòng n trong targets.
MD5 không salt; bcrypt cost **10**; Argon2id **64 MiB, t=3, p=1**. Hai loại sau có salt ngẫu nhiên, không dùng pepper.

**Dùng bộ `data/` hiện có để đối chiếu evidence.** Chỉ khi chủ động tạo lại, chạy:

```powershell
.\.venv\Scripts\python.exe scripts/generate_dataset.py
.\.venv\Scripts\python.exe scripts/generate_hashes.py
```

Hai script ghi đè dữ liệu/hash. Wordlist và targets tái lập được; bcrypt/Argon2id đổi salt/hash.
Nếu sinh lại, phải chuyển lại hash sang Kali và ghi nhận evidence tương ứng, không dùng ảnh của bộ cũ.

### Hashcat và benchmark

Hashcat đã chạy trên Kali VM bằng CPU/PoCL, phiên bản **7.1.2**.
Wordlist thử các từ sẵn có; Rules biến đổi từ trong wordlist; Mask sinh ứng viên theo mẫu ký tự.
Xem [lab/setup.md](lab/setup.md) để cài công cụ và chạy lại Wordlist, Rules, Mask với đúng mode và potfile.

Benchmark Python chạy trên Windows, độc lập với Flask và dữ liệu crack:

```powershell
.\.venv\Scripts\python.exe scripts/Benchmark_hash.py
.\.venv\Scripts\python.exe scripts/plot_benchmark.py
```

Lệnh đầu ghi đè [benchmark_summary.csv](lab/results/benchmark_summary.csv); lệnh sau đọc CSV, ghi đè [cost_trends.png](lab/results/cost_trends.png).
Phải chạy cả hai để ảnh được cập nhật. Không tạo thư mục timestamp.
MD5 đo 5 đợt × 10.000 hash, lấy trung vị thời gian trung bình mỗi đợt; bcrypt/Argon2id đo 5 lần/cấu hình.
Có warm-up; thời gian sinh salt được tính cho cả bcrypt và Argon2id. Đơn vị **ms/hash**.
Các cấu hình là bcrypt cost 10/11/12 và Argon2id 32 MiB/t=3, 64 MiB/t=3, 64 MiB/t=4, đều p=1.

## Kết quả chính

| Thí nghiệm | Kết quả đã ghi nhận |
| --- | --- |
| Wordlist, cả ba thuật toán | **2/3 mục tiêu**: tìm đủ hai mật khẩu có trong wordlist; mật khẩu thứ ba ở ngoài tập ứng viên. |
| Rules MD5, `u$!` (viết hoa + thêm `!`) | **0 hash tìm mới**; 2/3 total trong ảnh là kết quả potfile. |
| Mask MD5, 7 chữ thường + 2 chữ số | **1/3 tìm mới**, là mục tiêu đầu đã được Wordlist tìm ra; không cộng thành 3 mật khẩu khác nhau. |
| Benchmark CPU | CSV có 7 dòng cấu hình; biểu đồ tách bcrypt và Argon2id vì cost khác đơn vị. |

Xem [8 ảnh evidence và giải thích](lab/setup.md#8-evidence-và-kết-luận-thực-tế).
Ảnh Argon2id `05` ghi 2/3 tìm mới; ảnh `04` là lượt cũ có potfile, không ghép thành một phiên.
`Recovered total` có thể gồm kết quả cũ; `new` là tìm mới. `Exhausted`/`Progress 100%` nghĩa là hết tập ứng viên, không phải tìm đủ mọi mật khẩu.

## Kiểm thử

Sau khi cài cả hai file requirements, chạy tại thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Test Blue Team dùng database/secret tạm để kiểm tra đăng ký, đăng nhập, session, CSRF và HTTPS.
Test dataset kiểm tra wordlist, mục tiêu, 9 hash và salt; phần thử sinh lại dùng thư mục tạm.
Test HTTPS cần OpenSSL; một số test được bỏ qua nếu thiếu công cụ. Không dùng database thật để test.

## Giới hạn và sử dụng có trách nhiệm

- **Thí nghiệm minh họa:** MD5 và crack offline chỉ dùng mật khẩu/hash tổng hợp do nhóm tạo trong lab được phép.
- **Chưa thực hiện trong Red Team:** Rainbow Table, Timing Attack Comparison, benchmark verification/GPU; không dùng John the Ripper trên nhánh này.
- Không tìm được mật khẩu trong wordlist/mask không chứng minh mật khẩu hoặc thuật toán không thể bị crack.
- Năm lần đo còn chịu ảnh hưởng của máy, tải nền và nhiệt độ; không so trực tiếp benchmark Python với Speed của Hashcat hoặc suy ra hiệu năng GPU.
- Flask development server/certificate tự ký phục vụ local, không phải cấu hình production.
- Không dùng mật khẩu thật, dữ liệu rò rỉ có thông tin cá nhân hoặc thử mật khẩu trên dịch vụ bên ngoài; không đưa database, pepper, khóa session hay private key vào Git.
- Với demo 5–10 phút, dùng evidence đã hoàn thành; lượt Mask trong ảnh mất khoảng **5 giờ 10 phút**.

Lịch sử triển khai theo Git: [CHANGELOG.md](CHANGELOG.md).
