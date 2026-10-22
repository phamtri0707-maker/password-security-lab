# Password Security Lab — Blue Team

Ứng dụng đăng ký/đăng nhập local bằng Flask, SQLite và Argon2id. Giao diện dùng HTML/CSS thuần.

## Luồng hoạt động

1. `src/init_db.py` tạo `users.db` và bảng `users` nếu chưa có.
2. `register.html` gửi username, password và confirm password tới `/register`. App kiểm tra dữ liệu, băm `password + pepper` bằng Argon2id và chỉ lưu username cùng hash. Đăng ký xong quay về login.
3. `login.html` gửi username/password bằng POST. App tìm username bằng truy vấn SQL có tham số và kiểm tra mật khẩu bằng `verify()`.
4. Khi đúng, app xóa session cũ, lưu `user_id` và `username`, rồi chuyển tới `/home`.
5. `/home` yêu cầu đã đăng nhập. Nút Logout gửi POST, xóa session và đưa người dùng về `/`.

App đọc `PASSWORD_PEPPER` từ môi trường khi khởi động; register và login cùng dùng giá trị này. Salt được thư viện tự sinh ngẫu nhiên cho mỗi hash. Username được bỏ khoảng trắng hai đầu; password giữ nguyên, nhưng password chỉ gồm khoảng trắng bị từ chối. Ràng buộc `UNIQUE` chặn username trùng và không ghi đè tài khoản cũ.

`scripts/create_demo_user.py` vẫn là cách tạo riêng tài khoản `demo` từ terminal nếu cần; không bắt buộc chạy script để dùng Register trên web.

Session là trạng thái giúp app nhận biết người dùng giữa các lần truy cập. Flask lưu nó trong cookie có chữ ký. Chữ ký ngăn sửa dữ liệu, không che giấu nội dung cookie, nên app không đưa mật khẩu hoặc pepper vào session.

Username không tồn tại và password sai đều nhận cùng thông báo: **Username hoặc password không đúng.** Với username không tồn tại, app vẫn verify một hash tạm để giảm khác biệt thời gian xử lý.

Form có CSRF token: một mã ngẫu nhiên trong phiên và trong ô ẩn của form. App kiểm tra mã này trước khi nhận POST để chống yêu cầu giả mạo từ form khác. Cookie có `HttpOnly`, `SameSite=Lax`; các trang không được lưu cache.

## Chạy từ đầu trên PowerShell

Các lệnh dưới dùng đường dẫn Python hiện có trên máy ADMIN. Thành viên khác thay `$pythonExe` bằng đường dẫn Python trên máy mình.

```powershell
cd C:\password-security-lab
$pythonExe = "C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe"

& $pythonExe -m pip install -r requirements.txt
& $pythonExe src\init_db.py
```

Với database mới **chưa có tài khoản nào**, sinh pepper một lần:

```powershell
$env:PASSWORD_PEPPER = & $pythonExe -c "import secrets; print(secrets.token_hex(32))"
```

Nếu đã có tài khoản, cần cấp lại đúng pepper đã dùng để tạo tài khoản đó; không sinh pepper mới cho hash cũ. Pepper không nằm trong database nên không thể khôi phục từ database. App không tự đọc file `.env`.

Tạo khóa ký session riêng, sau đó chạy web trong cùng cửa sổ PowerShell:

```powershell
$env:FLASK_SECRET_KEY = & $pythonExe -c "import secrets; print(secrets.token_hex(32))"
& $pythonExe src\app.py
```

Mở **http://127.0.0.1:5000/**, bấm **Đăng ký tài khoản**, chọn username giả như `student_web` rồi nhập password và confirm password giống nhau. Đăng ký thành công sẽ về login. Đăng nhập bằng tài khoản vừa tạo, thử Logout rồi truy cập lại `/home`; app phải đưa về login. Nếu đang đăng nhập, bấm Logout trước khi thử tạo tài khoản khác. Nhấn `Ctrl+C` trong terminal để dừng web; sau khi sửa code cần chạy lại app để nhận thay đổi.

`PASSWORD_PEPPER` và `FLASK_SECRET_KEY` trong các lệnh trên chỉ tồn tại trong cửa sổ PowerShell hiện tại. Giữ pepper ở nơi riêng an toàn để cấp lại khi cần; không đưa giá trị thật vào code hoặc Git. Đổi khóa ký session sẽ làm các session cũ hết hiệu lực; đổi pepper làm mật khẩu đã băm bằng pepper cũ không còn khớp.

## Demo Register → xem hash → Login

1. Trên trình duyệt, đăng ký một tài khoản mới. Đăng ký xong chưa tự đăng nhập.
2. Để web tiếp tục chạy, mở PowerShell thứ hai và xem database bằng công cụ có sẵn trong Python 3.14:

```powershell
cd C:\password-security-lab
$pythonExe = "C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $pythonExe -m sqlite3 users.db "PRAGMA table_info(users);"
& $pythonExe -m sqlite3 users.db "SELECT id, username, password_hash FROM users;"
```

`PRAGMA table_info(users)` hiển thị cấu trúc bảng: chỉ có `id`, `username`, `password_hash`; không có cột password hoặc confirm password. Lệnh `SELECT` đọc các bản ghi đã lưu. Cột `password_hash` có chuỗi bắt đầu bằng `$argon2id$`, thay vì mật khẩu đã nhập.

Trong hash, `m=65536,t=3,p=4` là các tham số cost; hai phần tiếp theo chứa salt và kết quả băm. Salt nằm trong hash, còn pepper không được lưu trong database.

3. Quay lại trình duyệt và đăng nhập bằng tài khoản vừa đăng ký. Thử đăng ký lại cùng username hoặc nhập confirm password khác để xem lỗi; các trường hợp này không thêm hay sửa tài khoản.

## Cost tuning Argon2id

App và script tạo tài khoản đều đọc `src/argon2_config.json`:

```json
{
    "memory_cost": 65536,
    "time_cost": 3,
    "parallelism": 4
}
```

- `memory_cost`: bộ nhớ cấu hình cho một lần băm, đơn vị KiB. `65536 KiB = 64 MiB`; đây không phải số RAM toàn tiến trình đo được.
- `time_cost`: số lượt xử lý bộ nhớ; tăng thường làm phép băm lâu hơn.
- `parallelism`: mức xử lý song song. Giá trị 4 không nhân bộ nhớ cấu hình thành 256 MiB và không có nghĩa thời gian sẽ tăng 4 lần.

Salt vẫn do thư viện tự sinh ngẫu nhiên, nằm trong chuỗi hash cùng các tham số. Pepper chỉ được lấy từ biến môi trường.

Khi web đã dừng, chạy script đo nhỏ trong terminal đã có `PASSWORD_PEPPER`:

```powershell
& $pythonExe scripts\tune_argon2.py
```

Script thử bốn cấu hình, chạy khởi động một lần rồi đo hash/verify ba lần và lấy trung bình. Script chỉ tạo mật khẩu đo tạm trong RAM, không đọc hoặc ghi `users.db`. Dấu `*` đánh dấu cấu hình app đang sử dụng; script không tự sửa cấu hình.

Một lượt đo tham khảo, chạy riêng sau khi test đã kết thúc trên Python 3.14.7, Windows, CPU Intel64 Family 6 Model 170 Stepping 4:

| memory_cost (KiB) | time_cost | parallelism | Hash (ms) | Verify (ms) |
| ---: | ---: | ---: | ---: | ---: |
| 19456 | 2 | 1 | 23.6 | 23.3 |
| 65536 | 2 | 1 | 85.4 | 89.3 |
| 65536 | 3 | 1 | 124.3 | 121.8 |
| **65536** | **3** | **4** | **49.0** | **50.2** |

Chọn 64 MiB, 3 lượt, song song 4 cho app local vì trên máy đo phép kiểm tra khoảng 50 ms, còn đủ nhanh cho đăng nhập thủ công. Đây cũng là cấu hình tương ứng với profile `RFC_9106_LOW_MEMORY` của argon2-cffi. Kết quả thay đổi theo máy và tải hệ thống; số đo này không phải cam kết cho máy khác hoặc nhiều lượt đăng nhập đồng thời.

Sửa cấu hình tác động tới hash được tạo mới. Khi kiểm tra hash cũ, `verify()` đọc tham số nằm trong hash đó; app chưa tự cập nhật hash cũ.

Tham khảo: [argon2-cffi: chọn tham số](https://argon2-cffi.readthedocs.io/en/stable/parameters.html), [OWASP: lưu mật khẩu](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [Flask session](https://flask.palletsprojects.com/en/stable/quickstart/#sessions).

## Kiểm thử

```powershell
& $pythonExe -B -m unittest discover -s tests -v
```

Các test tự tạo database tạm, pepper và khóa session riêng, không dùng database thật. Phạm vi gồm đăng nhập đúng/sai, username không tồn tại, pepper thiếu/sai, cấu hình hash và salt, truy cập `/home`, logout, CSRF và việc không ghi đè tài khoản demo đã có.

Test Register kiểm tra tạo tài khoản, username trùng, xác nhận password sai, dữ liệu trống, salt ngẫu nhiên và đăng nhập bằng tài khoản vừa tạo. Test cũng kiểm tra schema và nội dung file database tạm: chỉ lưu hash, không lưu password rõ hay pepper.
