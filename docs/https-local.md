# HTTPS/TLS local — Secure Login Lab

Lab chạy tại **https://127.0.0.1:5000/**, dùng Flask development server và HTML/CSS thuần. Các bước dưới không đổi database, Argon2id, salt, pepper, cost tuning hay luồng Register/Login/Logout và session.

```text
Browser
  ↓ HTTPS/TLS: bảo vệ dữ liệu trên đường truyền
Flask
  ↓ Register / Login / Logout + Session
Argon2id + salt + pepper: bảo vệ mật khẩu khi lưu
  ↓
users.db
```

## Vì sao chọn certificate tự ký?

OpenSSL đã có trong Git for Windows trên máy này. Một lệnh tạo hai file ổn định, không cần thêm thư viện Python hoặc cài CA vào kho tin cậy của Windows. Cách này dễ quan sát và demo; đổi lại browser cảnh báo certificate chưa được tin cậy. Lab chỉ lắng nghe trên `127.0.0.1`.

## 1. Chuẩn bị PowerShell và giữ nguyên secret hiện tại

Dừng tiến trình Flask cũ bằng `Ctrl+C` trong terminal đang chạy nó, để giải phóng cổng 5000. Dùng cửa sổ PowerShell hiện đã có đúng `PASSWORD_PEPPER` và `FLASK_SECRET_KEY` của app:

```powershell
cd C:\password-security-lab
$pythonExe = "C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$opensslExe = "C:\Program Files\Git\usr\bin\openssl.exe"
& $opensslExe version
```

Nếu dùng Python hoặc OpenSSL ở nơi khác, thay hai đường dẫn trên. Nếu mở cửa sổ mới, cấp lại **đúng** pepper và khóa session từ nơi bạn đã lưu riêng. Không sinh lại pepper khi `users.db` đã có tài khoản: hash cũ cần pepper cũ để verify. Đổi khóa session làm phiên đăng nhập cũ hết hiệu lực.

App không tự đọc `.env`. Các lệnh `$env:...` chỉ áp dụng cho PowerShell hiện tại và tiến trình chạy từ cửa sổ đó; chúng không tự lưu cho lần khởi động sau. Với máy mới hoàn toàn chưa có database hoặc tài khoản, xem các bước cài đặt ban đầu trong [README](../README.md).

## 2. Tạo certificate và private key một lần

Trên máy hiện tại, hai file `local.crt` và `local.key` đã được tạo trong thư mục bên dưới. Bạn có thể bỏ qua khối tạo và đi thẳng tới bước 3. Khối lệnh này dành cho lần thiết lập mới trên máy khác; nó dừng nếu đã có một trong hai file để tránh ghi đè.

Lưu hai file bên ngoài `C:\password-security-lab`, trong thư mục của tài khoản Windows:

```powershell
$tlsDir = Join-Path $env:LOCALAPPDATA "SecureLoginLab\tls"
$certFile = Join-Path $tlsDir "local.crt"
$keyFile = Join-Path $tlsDir "local.key"

if ((Test-Path -LiteralPath $certFile) -or (Test-Path -LiteralPath $keyFile)) {
    throw "Đã có certificate hoặc key. Giữ nguyên hai file nếu đang dùng; không ghi đè."
}

New-Item -ItemType Directory -Path $tlsDir -Force | Out-Null

& $opensslExe req -x509 -newkey rsa:2048 -sha256 -days 365 -noenc `
    -keyout $keyFile -out $certFile `
    -subj "/CN=127.0.0.1" `
    -addext "subjectAltName=IP:127.0.0.1" `
    -addext "basicConstraints=critical,CA:FALSE" `
    -addext "keyUsage=critical,digitalSignature,keyEncipherment" `
    -addext "extendedKeyUsage=serverAuth"

if ($LASTEXITCODE -ne 0) {
    throw "OpenSSL chưa tạo certificate thành công. Kiểm tra lỗi trước khi chạy Flask."
}
```

Dấu backtick ở cuối dòng là ký hiệu nối dòng của PowerShell; không thêm khoảng trắng sau dấu đó. Chỉ chạy khối tạo này lần đầu. Nếu hai file đã tồn tại và còn dùng được, bỏ qua khối tạo và chuyển sang bước 3.

Với tài khoản ADMIN, vị trí thường là:

- Certificate: `C:\Users\ADMIN\AppData\Local\SecureLoginLab\tls\local.crt`.
- Private key: `C:\Users\ADMIN\AppData\Local\SecureLoginLab\tls\local.key`.

`-x509` tạo certificate tự ký, `-days 365` đặt thời hạn 365 ngày, SAN khai báo IP `127.0.0.1`. `-noenc` tạo private key không có passphrase để Flask đọc trực tiếp khi khởi động. Đây là lựa chọn đơn giản cho lab: giữ file trong thư mục tài khoản, kiểm tra quyền Windows chỉ cho tài khoản cần dùng và quản trị viên, không chia sẻ thư mục hoặc sao chép key vào repository. [Tài liệu lệnh OpenSSL](https://docs.openssl.org/3.5/man1/openssl-req/).

Private key tuyệt đối không commit Git. `.gitignore` đã chặn các mẫu file TLS phổ biến như một lớp phòng ngừa; vị trí lưu chính vẫn nằm ngoài repository.

## 3. Cho Flask đọc hai file và chạy HTTPS

Trong PowerShell đã có đúng pepper và khóa session:

```powershell
$tlsDir = Join-Path $env:LOCALAPPDATA "SecureLoginLab\tls"
$env:TLS_CERT_FILE = Join-Path $tlsDir "local.crt"
$env:TLS_KEY_FILE = Join-Path $tlsDir "local.key"

if (-not (Test-Path -LiteralPath $env:TLS_CERT_FILE -PathType Leaf)) {
    throw "Không tìm thấy certificate. Hãy hoàn thành bước 2."
}
if (-not (Test-Path -LiteralPath $env:TLS_KEY_FILE -PathType Leaf)) {
    throw "Không tìm thấy private key. Hãy hoàn thành bước 2."
}

& $pythonExe src\app.py
```

`src/app.py` lấy đường dẫn từ `TLS_CERT_FILE` và `TLS_KEY_FILE`, rồi truyền vào:

```python
tls_context = LocalHTTPSContext(ssl.PROTOCOL_TLS_SERVER)
tls_context.load_cert_chain(cert_file, key_file)
app.run(
    host="127.0.0.1",
    port=5000,
    ssl_context=tls_context,
    request_handler=LocalHTTPSRequestHandler,
    threaded=True,
)
```

Werkzeug thực sự nạp certificate và private key để thiết lập TLS; đây không chỉ là đổi chữ `http` thành `https`. Thiếu biến TLS, app dừng với thông báo cấu hình; đường dẫn sai hoặc cặp file không hợp lệ khiến server không khởi động. [Werkzeug: SSL/TLS](https://werkzeug.palletsprojects.com/en/stable/serving/#ssl).

`LocalHTTPSContext` chuyển TLS handshake sang worker xử lý từng kết nối. Nếu browser mở sẵn một kết nối nhưng chưa gửi handshake, kết nối đó không chặn toàn bộ server. `LocalHTTPSRequestHandler` đặt timeout 10 giây cho việc chờ handshake/request. Kết nối vẫn bắt buộc dùng TLS trước khi Flask đọc form; không chuyển dữ liệu sang HTTP.

Dùng `python src\app.py` theo lệnh trên. `flask run` thông thường không chạy khối `__main__` chứa cấu hình này. Cổng 5000 chỉ phục vụ HTTPS, không có HTTP song song hoặc redirect HTTP. Nhấn `Ctrl+C` để dừng server; khởi động lại sau khi sửa code.

## 4. Mở browser và hiểu cảnh báo certificate

Truy cập **https://127.0.0.1:5000/**. Dùng đúng IP này; certificate không khai báo `localhost` hoặc IP máy khác.

Browser có thể báo “Your connection is not private”, “Potential Security Risk” hoặc lỗi CA chưa được tin cậy. Certificate do bạn tự ký không có chuỗi chứng thực tới CA mà browser đã tin cậy. Cảnh báo này không có nghĩa server đang truyền HTTP; TLS vẫn được cấu hình, nhưng browser chưa tự xác minh được danh tính server. Chỉ tiếp tục qua tùy chọn nâng cao nếu bạn đang mở đúng lab local và nhận ra certificate mình vừa tạo. Không áp dụng cách bỏ qua cảnh báo này cho website khác. [MDN: xác thực server bằng TLS](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Transport_Layer_Security#server_authentication).

Bạn có thể xem certificate trong phần thông tin kết nối của browser: IP trong SAN, thời hạn và dấu vân tay SHA-256. Để đối chiếu với file local, mở PowerShell thứ hai:

```powershell
$opensslExe = "C:\Program Files\Git\usr\bin\openssl.exe"
$certFile = Join-Path $env:LOCALAPPDATA "SecureLoginLab\tls\local.crt"
& $opensslExe x509 -in $certFile -noout -subject -dates -ext subjectAltName -fingerprint -sha256
```

Lệnh chỉ đọc certificate công khai; không mở hoặc in private key. Khi certificate hết hạn, tạo cặp mới ở vị trí mới rồi cập nhật hai biến đường dẫn, giữ cặp cũ cho tới khi đã kiểm tra cặp mới hoạt động.

## 5. Kiểm tra Register / Login / Logout

Thử với dữ liệu giả dành riêng cho lab:

1. Mở `/register`, đăng ký username mới với password và confirm password giống nhau. Thành công phải chuyển về login; chưa tự đăng nhập.
2. Đăng nhập tài khoản vừa tạo. Phải vào `/home`, hiển thị đúng username và giao diện dashboard.
3. Bấm Logout. Phải về login; truy cập lại `https://127.0.0.1:5000/home` phải được đưa về login.
4. Thử password sai và username không tồn tại: cùng nhận lỗi đăng nhập chung. Thử username trùng hoặc confirm password khác: nhận lỗi rõ ràng, không sửa tài khoản cũ.
5. Đăng nhập lại một tài khoản đã có trước khi sửa HTTPS. Kết quả đúng xác nhận pepper cũ vẫn được cấp chính xác.
6. Trong DevTools → Network, xem URL của trang và các POST: đều bắt đầu bằng `https://127.0.0.1:5000`. Logout vẫn là POST và form vẫn có CSRF token ẩn.
7. Trong DevTools → Application/Storage → Cookies, kiểm tra cookie `session` có `Secure`, `HttpOnly`, `SameSite=Lax`. Nếu chưa thấy cookie, tải lại trang và mở một form.
8. Thu nhỏ browser về kích thước điện thoại; form và dashboard phải vừa màn hình, chữ và nút dễ đọc, không tràn ngang.

DevTools vẫn xem được dữ liệu form do bạn gửi, vì browser là một đầu của kết nối TLS. Điều đó không có nghĩa dữ liệu trên đường truyền đang ở dạng rõ.

Chạy bộ test sẵn có từ cửa sổ PowerShell thứ hai để kiểm tra auth bằng database tạm, không dùng tài khoản thật:

```powershell
cd C:\password-security-lab
$pythonExe = "C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $pythonExe -B -m unittest discover -s tests -v
```

`tests/test_https.py` còn tạo certificate/key tạm bên ngoài repository và chạy server TLS thật: kiểm tra certificate chưa được tin cậy, hostname sai, cookie HTTPS và Register → Login → Logout trên database tạm. Test cũng giữ một kết nối TCP chưa gửi TLS handshake để kiểm tra rằng các request HTTPS khác vẫn hoạt động. Test này cần OpenSSL; nếu không tìm thấy thì được bỏ qua, còn các test auth vẫn chạy. Trên máy này OpenSSL đi kèm Git đã được tìm thấy và test TLS đã chạy thành công.

Test tự động không thay thế việc xem và chấp nhận đúng certificate local trong browser. Nếu POST thiếu CSRF token, app vẫn từ chối với HTTP 400 như trước. Thử gửi form theo luồng bình thường để có token và session hợp lệ.

## Cookie trên HTTPS

- `SESSION_COOKIE_SECURE=True`: cookie chỉ được gửi qua kết nối HTTPS.
- `SESSION_COOKIE_HTTPONLY=True`: JavaScript không đọc được cookie session qua `document.cookie`.
- `SESSION_COOKIE_SAMESITE="Lax"`: hạn chế cookie trong nhiều yêu cầu từ website khác, vẫn phù hợp với điều hướng thông thường. CSRF token hiện tại tiếp tục kiểm tra POST; `SameSite` không thay thế token.

Các cờ này bảo vệ việc sử dụng cookie; cách tạo và xóa session khi login/logout được giữ nguyên. [Flask: cookie options](https://flask.palletsprojects.com/en/stable/web-security/#set-cookie-options).

## Certificate, private key và TLS handshake

**Certificate** là giấy chứng nhận số chứa public key, địa chỉ được chứng nhận, thời hạn và chữ ký. Browser nhận certificate từ server trong handshake; nó kiểm tra địa chỉ đang mở với SAN, thời hạn và chuỗi tin cậy. Ở lab này, SAN chứa `127.0.0.1`. Certificate là thông tin công khai, không chứa pepper hoặc mật khẩu. [RFC 9525: xác minh danh tính dịch vụ](https://www.rfc-editor.org/rfc/rfc9525.html#section-6).

**Private key** là phần bí mật tương ứng public key; giữ ở server. Với TLS hiện đại dùng certificate, server dùng key này để ký và chứng minh mình sở hữu khóa. Browser kiểm tra chữ ký bằng public key. Server không gửi private key cho browser.

Handshake ở mức tổng quan:

1. Browser và server thương lượng phiên bản TLS và thuật toán.
2. Server cung cấp certificate và bằng chứng sở hữu private key; browser kiểm tra chúng.
3. Hai bên trao đổi dữ liệu mật mã để tạo các khóa phiên đối xứng.
4. Các khóa phiên bảo vệ HTTP, gồm username/password, cookie và phản hồi. Public/private key RSA không trực tiếp mã hóa từng request.

Đây là mô tả rút gọn cho kết nối mới; TLS thư viện hệ thống xử lý các bước chi tiết. [RFC 8446: tổng quan TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html#section-2).

## HTTPS khác Argon2id + salt + pepper như thế nào?

| Cơ chế | Bảo vệ ở đâu? | Vai trò |
| --- | --- | --- |
| HTTPS/TLS | Browser ↔ Flask | Mã hóa dữ liệu đang truyền và phát hiện sửa đổi; xác thực server phụ thuộc việc kiểm tra certificate đáng tin cậy. |
| Argon2id | Trước khi ghi `users.db` | Băm một chiều với cost để tăng chi phí thử mật khẩu khi hash bị lộ. |
| Salt | Trong mỗi hash | Giá trị ngẫu nhiên riêng do Argon2id tự sinh; tránh cùng mật khẩu tạo cùng hash và giảm hiệu quả bảng băm sẵn. |
| Pepper | Môi trường của app | Bí mật bổ sung hiện được ghép với password trước khi băm; không lưu trong database. |

HTTPS giữ credential khó bị đọc hoặc sửa trên đường truyền. Sau khi TLS giải mã tại Flask, app vẫn cần nhận password để verify; Argon2id + salt + pepper bảo vệ bản lưu. Hai lớp bổ sung cho nhau. Với self-signed, cần nhận diện đúng certificate local thay vì mặc nhiên tin mọi cảnh báo. [MDN: các thuộc tính bảo vệ của TLS](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Transport_Layer_Security).

Giao diện không hiển thị pepper, private key hay password hash. Các tham số Argon2id và dữ liệu trong `users.db` không cần thay đổi để bật HTTPS.
