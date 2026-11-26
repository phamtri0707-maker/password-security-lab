# Red Team — Hướng dẫn chạy lại thí nghiệm

Nhóm 7 — Hash & Bảo mật mật khẩu + Crack Demo. Phạm vi hiện tại gồm dataset tổng hợp, MD5/bcrypt/Argon2id, Hashcat Wordlist/Rules/Mask và benchmark hashing time trên CPU. **Không triển khai Rainbow Table, Timing Attack Comparison, benchmark verification hoặc GPU.** John the Ripper không nằm trong thực nghiệm của nhánh này.

## 1. File và môi trường

| Vị trí | Chức năng |
| --- | --- |
| [generate_dataset.py](../scripts/generate_dataset.py) | Sinh wordlist, 3 mục tiêu và metadata. |
| [generate_hashes.py](../scripts/generate_hashes.py) | Băm mỗi mục tiêu bằng ba thuật toán, tổng cộng 9 hash. |
| [Benchmark_hash.py](../scripts/Benchmark_hash.py) | Đo hashing time và cost tuning bằng các vòng lặp đơn giản. |
| [plot_benchmark.py](../scripts/plot_benchmark.py) | Đọc CSV và vẽ biểu đồ. |
| [requirements-redteam.txt](../scripts/requirements-redteam.txt) | Dependency Python cho Red Team. |
| [wordlist.txt](../data/wordlist.txt), [targets.txt](../data/targets.txt), [targets_metadata.csv](../data/targets_metadata.csv) | Dữ liệu tổng hợp và đáp án. |
| [md5.txt](../data/hashes/md5.txt), [bcrypt.txt](../data/hashes/bcrypt.txt), [argon2id.txt](../data/hashes/argon2id.txt) | Ba file hash, mỗi file 3 dòng, không chứa plaintext/header. |
| [evidence/](evidence/) | 8 ảnh thực nghiệm Hashcat. |
| [benchmark_summary.csv](results/benchmark_summary.csv), [cost_trends.png](results/cost_trends.png) | Hai file kết quả benchmark hiện tại. |

`scripts/` chứa chương trình, `data/` chứa dữ liệu, `lab/` chứa hướng dẫn và kết quả. `src/` cùng `users.db` thuộc Blue Team; các script Red Team không đọc database, pepper hoặc cấu hình Argon2id của Blue Team.

Môi trường thực nghiệm:

- Chuẩn bị dữ liệu/benchmark: Windows 11, Python 3.14.7; bcrypt 5.0.0, argon2-cffi 25.1.0, matplotlib 3.11.2. Matplotlib này yêu cầu Python >=3.11.
- Crack: Kali Linux VM, Hashcat **7.1.2**, OpenCL PoCL; ảnh thiết bị báo CPU Intel Core Ultra 7 155H, 4 MCU. Đây là CPU trong VM, không phải benchmark GPU.
- Thời gian và tốc độ thay đổi theo máy, tài nguyên VM, tải nền và trạng thái CPU. Các môi trường khác chưa được cam kết cho số đo giống ảnh.

## 2. Chuẩn bị Python trên Windows

Mở PowerShell ở thư mục gốc. Nếu chưa có `.venv`:

```powershell
cd C:\password-security-lab
py -3.14 -m venv .venv
```

Nếu không dùng được `py`, thay bằng đường dẫn Python thật; ví dụ máy ADMIN:

```powershell
& 'C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
```

Cài dependency Red Team bằng chính Python của môi trường:

```powershell
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-redteam.txt
```

Có thể dùng lệnh ngắn sau khi kích hoạt một lần cho terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```

Các ví dụ Windows tiếp theo dùng `python` sau khi kích hoạt. Nếu PowerShell chặn activation, thay `python` bằng `.\.venv\Scripts\python.exe`; không cần đổi execution policy. Chạy toàn bộ ứng dụng/test Blue Team cần cài thêm `requirements.txt` theo [README](../README.md).

## 3. Dataset và hash

### Dùng bộ dữ liệu đã có

Để đối chiếu với evidence, giữ nguyên các file trong `data/`. Không cần chạy lại các script sinh dữ liệu hoặc khởi động Flask.

Dataset có đúng 1.000 mật khẩu không trùng, dùng seed `7007`: 400 dễ đoán, 350 trung bình, 250 khó đoán hơn. Đây là nhãn phục vụ minh họa, không phải đánh giá độ mạnh mật khẩu thực tế hoặc bộ sinh mật khẩu để sử dụng thật.

| Mục tiêu | Dòng trong targets.txt và mỗi file hash | Vị trí trong wordlist.txt |
| --- | ---: | ---: |
| target_1, dễ đoán | 1 | 25 |
| target_2, trung bình | 2 | 650 |
| target_3, khó đoán hơn | 3 | Không có |

Vị trí tính từ **1**. Ô `wordlist_line` trống trong CSV nghĩa là không nằm trong wordlist. Dòng n của cả ba file hash thuộc mục tiêu dòng n; không đổi thứ tự khi đối chiếu.

| Thuật toán | Cấu hình bộ hash mục tiêu |
| --- | --- |
| MD5 | Không salt, 32 ký tự hex. Chỉ minh họa thuật toán không phù hợp để lưu mật khẩu. |
| bcrypt | `$2b$`, cost `10`; salt 16 byte ngẫu nhiên do `bcrypt.gensalt()` tạo. |
| Argon2id | `v=19`, `memory_cost=65536` KiB = 64 MiB, `time_cost=3`, `parallelism=1`; salt 16 byte, digest 32 byte. |

Salt và cost nằm trong chuỗi bcrypt/Argon2id. Red Team không dùng pepper. Blue Team hiện dùng `p=4` và có pepper, nên không lấy hash Blue Team làm đầu vào crack.

Có thể kiểm tra bộ dữ liệu hiện có bằng:

```powershell
python -B -m unittest discover -s tests -p test_redteam_dataset.py -v
```

Test đối chiếu wordlist, metadata, 9 hash và kiểm tra salt; phần thử sinh lại dùng thư mục tạm, không ghi đè bộ dữ liệu chính.

### Chỉ tạo lại khi chủ động làm bộ thí nghiệm mới

Hai lệnh sau **ghi đè dữ liệu/hash Red Team hiện có**:

```powershell
python scripts/generate_dataset.py
python scripts/generate_hashes.py
python -B -m unittest discover -s tests -p test_redteam_dataset.py -v
```

Wordlist/targets giữ nguyên nhờ seed; bcrypt/Argon2id sinh salt mới nên hash thay đổi. Khi sinh lại, phải chuyển đúng bộ hash mới sang Kali; potfile và ảnh của hash cũ không còn chứng minh kết quả của bộ mới. Các file TXT/CSV được script xuất bằng UTF-8 không BOM, xuống dòng LF.

## 4. Chuẩn bị Kali và Hashcat

Chuyển `data/wordlist.txt` và cả ba file `data/hashes/*.txt` sang Kali, giữ cấu trúc:

```text
~/password-security-lab/
  data/
    wordlist.txt
    hashes/
      md5.txt
      bcrypt.txt
      argon2id.txt
```

Giữ `targets.txt` và metadata làm đáp án riêng nếu cần. Không chuyển `users.db`, pepper, private key hoặc `.venv` Windows sang Kali.

Nếu Kali chưa có Hashcat và OpenCL CPU runtime:

```bash
sudo apt update
sudo apt install hashcat pocl-opencl-icd clinfo
hashcat --version
clinfo
hashcat -I
```

Các lệnh cài đặt có thể tải phiên bản khác 7.1.2 tùy repository Kali. Kiểm tra `hashcat --help` có các mode dưới đây trước khi chạy, nhất là `34000`. Không dùng `--force` để bỏ qua lỗi driver; nếu không thấy thiết bị, kiểm tra PoCL và tài nguyên VM. Để chỉ chọn OpenCL CPU khi máy có nhiều loại thiết bị, có thể thêm `-D 1` vào lệnh attack.

| Mode | Thuật toán/file |
| ---: | --- |
| 0 | MD5 không salt — `data/hashes/md5.txt` |
| 3200 | bcrypt — `data/hashes/bcrypt.txt` |
| 34000 | Argon2, hỗ trợ chuỗi Argon2id đang dùng — `data/hashes/argon2id.txt` |

Thông tin tham khảo: [Hashcat trên Kali](https://www.kali.org/tools/hashcat/), [module Argon2 của Hashcat 7.1.2](https://github.com/hashcat/hashcat/blob/v7.1.2/src/modules/module_34000.c).

## 5. Chạy Wordlist Attack

Các lệnh Hashcat đều chạy trong **Bash/Zsh của Kali**, tại thư mục gốc:

```bash
cd ~/password-security-lab
wc -l data/wordlist.txt data/hashes/md5.txt data/hashes/bcrypt.txt data/hashes/argon2id.txt
```

Cần thấy 1.000 dòng wordlist và 3 dòng cho mỗi file hash. Chạy từng lệnh, chờ kết thúc rồi mới chạy lệnh tiếp theo:

```bash
hashcat -m 0 -a 0 data/hashes/md5.txt data/wordlist.txt --potfile-disable
hashcat -m 3200 -a 0 data/hashes/bcrypt.txt data/wordlist.txt --potfile-disable
hashcat -m 34000 -a 0 data/hashes/argon2id.txt data/wordlist.txt --potfile-disable
```

`-m` chọn loại hash, `-a 0` dùng wordlist. Các lượt độc lập này tắt potfile để không dùng kết quả có sẵn. Với bộ dữ liệu hiện tại, hai mục tiêu trong wordlist có thể được tìm ra; mục tiêu thứ ba không có trong tập ứng viên.

### Đọc trạng thái và potfile

- `Recovered ... total`: tổng số hash đã biết, có thể gồm kết quả potfile; `new`: số tìm mới trong lượt hiện tại.
- `INFO: Removed ... found as potfile entries`: Hashcat bỏ qua hash đã có kết quả, không tính đó là phát hiện mới của attack.
- `Exhausted`: đã thử hết tập ứng viên được chọn; không đồng nghĩa tìm được mọi mật khẩu. `Progress 100%` cũng không có nghĩa crack thành công 100%.
- `Speed` có đơn vị H/s, kH/s hoặc MH/s; `Time.Started` cho thời gian attack. Dòng `Started/Stopped` toàn tiến trình còn gồm khởi tạo.
- Tiến độ của hash có salt có thể tính công việc qua nhiều salt; `3000/3000` không có nghĩa file wordlist có 3.000 mật khẩu.

Trong Hashcat 7.1.2, `--potfile-disable` tắt cơ chế potfile cho lượt chạy; kết quả vẫn có thể xuất trên terminal nhưng không được giữ trong potfile cho `--show` sau đó. Nếu chủ động dùng potfile, có thể chỉ định `--potfile-path` tới file riêng và dùng `--show` với cùng file đó; `--show` đọc kết quả đã lưu, không crack mới. Không cần xóa potfile cũ để chạy các lệnh độc lập phía trên.

Potfile/restore/cache là dữ liệu local của công cụ; kiểm tra trước khi đưa file lên Git. Hiện `.gitignore` chưa bao gồm mọi mẫu `*.potfile`/`*.restore`. Xem [mô tả trạng thái Hashcat](https://hashcat.net/wiki/doku.php?id=hashcat#status_output) và [cơ chế potfile trong 7.1.2](https://github.com/hashcat/hashcat/blob/v7.1.2/src/potfile.c).

## 6. Rules Attack

Thực nghiệm dùng một rule viết trực tiếp, không cần tạo file rule:

```bash
hashcat -m 0 -a 0 data/hashes/md5.txt data/wordlist.txt -j 'u$!' --potfile-disable
```

`u` đổi toàn bộ chữ thành chữ hoa, `$!` thêm `!` vào cuối. Giữ dấu nháy đơn để shell không diễn giải `$!`. Ví dụ minh họa: `labmoon14` thành `LABMOON14!`.

Không có mục tiêu hiện tại nào khớp phép biến đổi này. Lệnh độc lập có thể kết thúc `Exhausted` với `0/3 new` và `0/3 total`. **Ảnh 06 là lượt cũ không tắt potfile:** nó ghi `2/3 total`, `0/3 new` và thông báo lấy hai kết quả potfile. Vì vậy kết luận thực nghiệm là **đã chạy Rules nhưng không tìm thêm hash**, không phải Rules crack mới hai mật khẩu.

Tham khảo cú pháp [Hashcat Rules](https://hashcat.net/wiki/doku.php?id=rule_based_attack).

## 7. Mask Attack

Mask đã thử gồm **7 chữ thường + 2 chữ số**, tổng độ dài 9:

```bash
hashcat -m 0 -a 3 data/hashes/md5.txt '?l?l?l?l?l?l?l?d?d' --potfile-disable
```

`-a 3` chọn Mask Attack; `?l` là chữ a–z, `?d` là chữ số. Có `26^7 × 10^2 = 803.181.017.600` ứng viên. Ảnh 07 ghi nhận hết không gian này sau khoảng **5 giờ 10 phút**, tìm mới `1/3`. Đây không phải lệnh nên chạy đầy đủ trong demo 5–10 phút; dùng evidence đã có để trình bày.

Mask chỉ bao phủ mục tiêu đầu `labmoon14`. Mục tiêu thứ hai dài 14, mục tiêu thứ ba dài 20, nên không nằm trong mask này. Mục tiêu đầu đã được Wordlist tìm ra; **không cộng Wordlist 2 + Mask 1 thành 3 mật khẩu khác nhau**.

Tham khảo [Hashcat Mask Attack](https://hashcat.net/wiki/doku.php?id=mask_attack).

## 8. Evidence và kết luận thực tế

| Ảnh | Nội dung chứng minh |
| --- | --- |
| [01-md5-crack.png](evidence/01-md5-crack.png) | Wordlist MD5: `Exhausted`, 2/3 total và 2/3 new; 1000/1000, 6891 H/s. Thiếu dòng lệnh trong ảnh; dùng cấu hình Wordlist ở mục 5 để giải thích. |
| [02-bcrypt-crack.png](evidence/02-bcrypt-crack.png) | Lệnh bcrypt `-m 3200 -a 0` với `--potfile-disable` và thông tin CPU. |
| [03-bcrypt-crack.png](evidence/03-bcrypt-crack.png) | Kết quả bcrypt: 2/3 total, 2/3 new; 3000/3000, 26 H/s; attack khoảng 1 phút 1 giây. |
| [04-Argon2id-crack.png](evidence/04-Argon2id-crack.png) | Khởi tạo lượt Argon2id cũ, có thông báo hash lấy từ potfile và cảnh báo bộ nhớ VM. Không chứng minh toàn bộ hash đều tìm mới. |
| [05-Argon2id-crack.png](evidence/05-Argon2id-crack.png) | Ảnh kết quả mới, cập nhật trong commit `0c30cc7`: 2/3 total, 2/3 new; 3000/3000, 8 H/s; attack khoảng 3 phút 32 giây. |
| [06-rules-crack.png](evidence/06-rules-crack.png) | Rule `u$!`: 2/3 total từ potfile, **0/3 new**; 1000/1000. |
| [07-mask-crack.png](evidence/07-mask-crack.png) | Kết quả Mask: 1/3 total, 1/3 new; hết không gian 803.181.017.600; khoảng 5 giờ 10 phút. |
| [08-mask-crack.png](evidence/08-mask-crack.png) | Lệnh Mask `-a 3` với 7 `?l` + 2 `?d` và `--potfile-disable`; chưa có kết quả cuối trong riêng ảnh này. |

Ảnh 04 và 05 **không phải đầu/cuối của cùng một lượt chạy**: ảnh 04 là lượt cũ có potfile, ảnh 05 là kết quả mới. Không ghép các số liệu của chúng thành một phiên duy nhất. Tương tự, khi giải thích các cặp ảnh lệnh/kết quả khác, dùng đúng mode, đầu vào và cấu hình hiển thị; không suy thêm thông tin bị cắt khỏi ảnh.

Dataset hiện tại giải thích kết quả: hai mục tiêu có trong wordlist được tìm thấy với cả ba thuật toán; Rules không mở rộng tới mục tiêu còn lại; Mask tìm lại mục tiêu đầu. Không tìm được mục tiêu thứ ba chỉ chứng minh giới hạn của các tập ứng viên đã thử, không chứng minh mật khẩu hay Argon2id không thể bị crack.

## 9. Benchmark hashing time và cost tuning

Chạy trên Windows, trong môi trường Python đã cài ở mục 2, tại thư mục gốc:

```powershell
python scripts/Benchmark_hash.py
python scripts/plot_benchmark.py
```

Script chính giữ cách viết theo vòng lặp: MD5 → bcrypt → Argon2id, `time.perf_counter()`, list kết quả và `statistics.median()`:

- MD5: 5 đợt, mỗi đợt 10.000 hash, lấy thời gian trung bình mỗi đợt rồi trung vị của 5 giá trị.
- bcrypt: cost 10/11/12; mỗi cost đo 5 lần.
- Argon2id: 32 MiB/t=3, 64 MiB/t=3, 64 MiB/t=4; tất cả p=1; mỗi cấu hình đo 5 lần.
- Warm-up một lần ngoài khoảng đo; bcrypt/Argon2id đều tính sinh salt trong khoảng đo. Đầu vào là bytes của `hello123`, không dùng pepper.
- Chỉ đo hash; chưa benchmark verify. MD5 dùng digest bytes; hai thư viện còn lại trả định dạng hash của chúng.

Lệnh đầu **ghi đè** [benchmark_summary.csv](results/benchmark_summary.csv); lệnh sau đọc CSV và **ghi đè** [cost_trends.png](results/cost_trends.png). Cần chạy cả hai để ảnh phản ánh số liệu mới. Không tạo JSON, file mẫu đo hoặc thư mục timestamp.

CSV có 7 dòng kết quả. `median_ms` là trung vị tính bằng ms/hash, `measurements=5`; `hashes_per_measurement` là 10.000 cho MD5 và 1 cho bcrypt/Argon2id. Các cột cost, memory MiB, time cost, p chỉ có giá trị khi áp dụng. CSV chỉ giữ số tổng hợp, không lưu đủ 5 mẫu để tính lại trung vị sau đó.

Biểu đồ tách bcrypt và Argon2id vì cost không cùng đơn vị. Các cấu hình Argon2id là nhãn bộ nhớ/t, không phải một đại lượng cost chung; MD5 không có cost tuning nên chỉ có trong CSV.

Giữ cùng chế độ nguồn, đóng tác vụ nặng và không chạy benchmark song song với crack/test/VM đang tải cao. Số đo gồm Python overhead và chi phí API, không chỉ lõi thuật toán. Năm lần đo phục vụ minh họa; môi trường và nhiệt độ CPU có thể làm kết quả dao động. Không đổi kết quả để ép đường biểu diễn tăng đều, không suy trực tiếp tốc độ Hashcat/GPU từ nghịch đảo ms/hash. Benchmark Blue Team dùng cấu hình/cách đo khác và nằm riêng trong `scripts/tune_argon2.py`.

## 10. Lỗi thường gặp và nguyên tắc sử dụng

| Hiện tượng | Kiểm tra |
| --- | --- |
| Không nhận `python` hoặc thiếu thư viện | Chọn interpreter `.venv`; cài requirements bằng chính `.\.venv\Scripts\python.exe -m pip`. |
| Không tìm thấy file trên Kali | Đứng ở thư mục gốc, giữ `data/hashes/` và đúng chữ hoa/thường của tên file. |
| Không nhận mode 34000 | Kiểm tra version và `hashcat --help`; evidence dùng 7.1.2 có hỗ trợ Argon2id. |
| Không có OpenCL device | Kiểm tra `clinfo`, `hashcat -I` và PoCL CPU runtime; không thêm `--force` để che lỗi. |
| Total khác new | Kiểm tra potfile và thông báo đầu phiên; dùng `--potfile-disable` cho lượt độc lập. |
| PNG không đổi sau benchmark | Chạy tiếp `plot_benchmark.py`, đóng/mở lại ảnh trong VS Code. |
| Test báo sai LF/BOM sau khi copy/checkout | Giữ UTF-8 không BOM và LF cho TXT/CSV trong `data/`; sửa định dạng xuống dòng, không cần sinh lại salt/hash chỉ vì lỗi định dạng. |

Chỉ crack hash do nhóm tạo trong môi trường được phép; không dùng mật khẩu thật, dữ liệu rò rỉ có PII hoặc brute force dịch vụ online. Plaintext trong targets là đáp án tổng hợp cho lab. Không đưa pepper, khóa session, private key hoặc dữ liệu tài khoản thật vào Git.

Thực nghiệm giới hạn ở ba thuật toán và CPU. Chưa có Rainbow Table, Timing Attack Comparison, benchmark GPU/verification; không mô tả chúng như các chức năng đã hoàn thành.
