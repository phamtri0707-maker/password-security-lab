# Changelog

Các mốc dưới đây dựa trên commit thực tế trong lịch sử dẫn tới nhánh `feature/hash-lab`, đến `2290057`. Ngày lấy theo Git, múi giờ +07:00; đây là ngày commit, không nhất thiết trùng thời điểm chụp ảnh/chạy thí nghiệm. Chưa có số phiên bản phát hành riêng.

Lịch sử ở các nhánh khác chưa được merge vào nhánh này không được ghi nhận như tính năng đã triển khai ở đây.

## Chưa phát hành

- Cập nhật README toàn project, giữ mô tả Blue Team và bổ sung phạm vi/kết quả Red Team.
- Hoàn thiện `lab/setup.md`: dependency, bộ dữ liệu có sẵn/sinh lại, Kali/Hashcat, Wordlist/Rules/Mask, potfile, evidence và benchmark.
- Điền changelog theo lịch sử Git; thay đổi tài liệu này chưa được gán commit hoặc phiên bản phát hành.

## 2026-11-09

- `2290057` — `chore: remove unused users file`: xóa file `users` rỗng, không phải database `users.db`.
- `0c30cc7` — `fix: update Bcrypt and Argon2id`: cập nhật/sắp xếp evidence bcrypt và Argon2id, đổi tên ảnh Rules, bổ sung ảnh Mask; cập nhật CSV benchmark và biểu đồ. Ảnh kết quả Argon2id mới ghi nhận 2/3 hash tìm mới; ảnh khởi tạo lượt cũ có potfile vẫn được giữ riêng.
- `40959da` — `feat: complete hashing benchmark`: thêm benchmark hashing time/cost tuning MD5, bcrypt, Argon2id và script vẽ riêng; lưu `benchmark_summary.csv`, `cost_trends.png`; thêm matplotlib, hướng dẫn benchmark và ảnh Rules. Phiên bản đã commit dùng vòng lặp đơn giản, không có benchmark verify hoặc hệ thống metadata/timestamp.

## 2026-11-06

- `269425c` — `docs: add hashcat craking evidence`: bổ sung các ảnh Hashcat Wordlist cho MD5, bcrypt và Argon2id. Một số tên/nội dung ảnh được cập nhật tiếp ở `0c30cc7`; dùng đường dẫn hiện tại trong [lab/setup.md](lab/setup.md#8-evidence-và-kết-luận-thực-tế).

## 2026-11-04

- `1b39079` — `feat: add synthetic password dataset and hash generation`: tạo wordlist 1.000 mật khẩu tổng hợp, ba mục tiêu, metadata, chín hash MD5/bcrypt/Argon2id; thêm hai script sinh dữ liệu/hash, dependency Red Team, hướng dẫn và test dataset.

## 2026-10-28

- `2812fc4` — merge PR #2 từ `feature/database`: tích hợp Blue Team vào `develop`. Đây là merge đã có trong lịch sử, không phải merge Red Team.

## 2026-10-24

- `ef1fed0` — `feat: add HTTPS support and improve secure login UI`: bổ sung HTTPS local bằng certificate/private key bên ngoài repository, xử lý TLS handshake trong worker và timeout; cải thiện giao diện Register/Login/Home; thêm hướng dẫn TLS và kiểm thử HTTPS.

## 2026-10-22

- `0b74dc4` — `feat: complete secure login with Argon2id`: hoàn thiện Register/Login/Logout, session, CSRF, truy vấn SQL có tham số; Argon2id + salt + pepper, cấu hình cost, script tạo tài khoản demo/tune cost và test đăng nhập.
- `db292d4` — `fix: correct gitignore`: chỉnh quy tắc ignore.
- `353d151` — `fix: ignore local database`: bỏ theo dõi `users.db` trong cây Git hiện tại và thêm quy tắc ignore database local.
- `c4d2845` — `feat: add initial database and login page`: tạo schema SQLite và trang đăng nhập ban đầu.
- `51b7f2c` — `lab: initialize project structure`: khởi tạo cấu trúc repository cùng các file nền tảng.

## Phạm vi phiên bản hiện tại

Red Team đã triển khai dataset/hash, Hashcat Wordlist với ba thuật toán, Rules, Mask và benchmark hashing time trên CPU. Rules không tìm thêm hash; Mask tìm lại mục tiêu đầu đã được Wordlist khôi phục, không làm tổng số mục tiêu khác nhau tăng từ hai lên ba.

Rainbow Table và Timing Attack Comparison không triển khai. John the Ripper, benchmark GPU và benchmark verification không thuộc phần thực nghiệm đã commit trên nhánh này.

Xem [README](README.md) và [hướng dẫn/evidence Red Team](lab/setup.md).
